#!/usr/bin/env python3
"""
Direct Coinstore signature test - dev's suggestion.
Tests if signature works with requests library (not aiohttp).
"""
import hashlib
import hmac
import json
import math
import time
import requests
import sys
import os
from dotenv import load_dotenv

# Load environment - try multiple methods
env_path = '/opt/trading-bridge/.env'
if os.path.exists(env_path):
    load_dotenv(env_path)

# Also read .env file directly as fallback
DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not DATABASE_URL or not ENCRYPTION_KEY:
    # Read .env file directly
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    if key == 'DATABASE_URL':
                        DATABASE_URL = value
                    elif key == 'ENCRYPTION_KEY':
                        ENCRYPTION_KEY = value

if not DATABASE_URL or not ENCRYPTION_KEY:
    print(f"ERROR: DATABASE_URL or ENCRYPTION_KEY not set")
    print(f"   DATABASE_URL: {'SET' if DATABASE_URL else 'NOT SET'}")
    print(f"   ENCRYPTION_KEY: {'SET' if ENCRYPTION_KEY else 'NOT SET'}")
    sys.exit(1)

# Get credentials from database
try:
    from sqlalchemy import create_engine, text
    from cryptography.fernet import Fernet
    
    fernet = Fernet(ENCRYPTION_KEY.encode())
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT ec.api_key_encrypted, ec.api_secret_encrypted
            FROM exchange_credentials ec
            WHERE ec.exchange = 'coinstore'
            LIMIT 1
        """))
        
        row = result.fetchone()
        if not row:
            print("ERROR: No Coinstore credentials found")
            sys.exit(1)
        
        api_key = fernet.decrypt(row[0].encode()).decode().strip()
        api_secret = fernet.decrypt(row[1].encode()).decode().strip()
        
        print(f"✅ Loaded credentials")
        print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
        print(f"   Secret length: {len(api_secret)}")
        
except Exception as e:
    print(f"ERROR loading credentials: {e}")
    sys.exit(1)

# Test 1: Balance check (simplest case)
print("\n" + "="*80)
print("TEST 1: Balance Check (POST /spot/accountList)")
print("="*80)

secret_bytes = api_secret.encode('utf-8')
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
key = hmac.new(secret_bytes, expires_key.encode('utf-8'), hashlib.sha256).hexdigest()
payload = json.dumps({})
sig = hmac.new(key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

headers = {
    "X-CS-APIKEY": api_key,
    "X-CS-SIGN": sig,
    "X-CS-EXPIRES": str(expires),
    "Content-Type": "application/json",
    "exch-language": "en_US"
}

print(f"Expires: {expires}")
print(f"Payload: {repr(payload)}")
print(f"Signature: {sig[:32]}...")

r = requests.post("https://api.coinstore.com/api/spot/accountList",
    data=payload,
    headers=headers,
    timeout=10)

print(f"\nResponse Status: {r.status_code}")
print(f"Response Body: {r.text[:500]}")

if r.status_code == 200:
    print("\n✅ BALANCE CHECK SUCCESSFUL - Signature works!")
elif r.status_code == 401:
    print("\n❌ BALANCE CHECK FAILED - Signature rejected (401)")
    print("   This confirms signature issue")
else:
    print(f"\n⚠️  Unexpected status: {r.status_code}")

# Test 2: Order placement (if balance works)
if r.status_code == 200:
    print("\n" + "="*80)
    print("TEST 2: Order Placement (POST /trade/order/place)")
    print("="*80)
    
    expires = int(time.time() * 1000)
    expires_key = str(math.floor(expires / 30000))
    key = hmac.new(secret_bytes, expires_key.encode('utf-8'), hashlib.sha256).hexdigest()
    
    params = {
        "symbol": "SHARPUSDT",
        "side": "BUY",
        "ordType": "MARKET",
        "ordAmt": "1",
        "timestamp": expires
    }
    
    # Test with compact JSON (current implementation)
    payload = json.dumps(params, separators=(',', ':'))
    sig = hmac.new(key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    headers = {
        "X-CS-APIKEY": api_key,
        "X-CS-SIGN": sig,
        "X-CS-EXPIRES": str(expires),
        "Content-Type": "application/json",
        "exch-language": "en_US"
    }
    
    print(f"Payload: {payload}")
    print(f"Signature: {sig[:32]}...")
    
    r2 = requests.post("https://api.coinstore.com/api/trade/order/place",
        data=payload,
        headers=headers,
        timeout=10)
    
    print(f"\nResponse Status: {r2.status_code}")
    print(f"Response Body: {r2.text[:500]}")
    
    if r2.status_code == 200:
        print("\n✅ ORDER PLACEMENT SUCCESSFUL - Signature works!")
    elif r2.status_code == 401:
        print("\n❌ ORDER PLACEMENT FAILED - Signature rejected (401)")
        print("\n   Testing with default JSON separators (no compact)...")
        
        # Test with default JSON separators
        payload_default = json.dumps(params)
        sig_default = hmac.new(key.encode('utf-8'), payload_default.encode('utf-8'), hashlib.sha256).hexdigest()
        
        headers["X-CS-SIGN"] = sig_default
        
        print(f"Payload (default): {payload_default}")
        print(f"Signature: {sig_default[:32]}...")
        
        r3 = requests.post("https://api.coinstore.com/api/trade/order/place",
            data=payload_default,
            headers=headers,
            timeout=10)
        
        print(f"\nResponse Status: {r3.status_code}")
        print(f"Response Body: {r3.text[:500]}")
        
        if r3.status_code == 200:
            print("\n✅ SUCCESS with default JSON separators!")
            print("   Fix: Remove separators=(',', ':') from json.dumps()")
        else:
            print(f"\n❌ Still failing with default separators")
    elif r2.status_code in [400, 500]:
        print(f"\n⚠️  Order rejected but NOT signature issue (status {r2.status_code})")
        print("   This means signature WORKS - issue is order parameters or balance")
    else:
        print(f"\n⚠️  Unexpected status: {r2.status_code}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
