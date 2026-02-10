#!/usr/bin/env python3
"""
Direct Coinstore API test using requests library (not aiohttp).
This tests if the issue is in aiohttp vs signature generation.

Run on Hetzner: python3 test_coinstore_direct.py
"""
import hashlib
import hmac
import json
import math
import time
import requests
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get credentials from environment or database
api_key = os.getenv("COINSTORE_API_KEY")
api_secret = os.getenv("COINSTORE_API_SECRET")

# If not in env, try database
if not api_key or not api_secret:
    try:
        from sqlalchemy import create_engine, text
        from cryptography.fernet import Fernet
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
        
        if DATABASE_URL and ENCRYPTION_KEY:
            fernet = Fernet(ENCRYPTION_KEY.encode())
            engine = create_engine(DATABASE_URL)
            
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT api_key_encrypted, api_secret_encrypted
                    FROM exchange_credentials
                    WHERE exchange = 'coinstore'
                    LIMIT 1
                """))
                row = result.fetchone()
                if row:
                    api_key = fernet.decrypt(row[0].encode()).decode().strip()
                    api_secret = fernet.decrypt(row[1].encode()).decode().strip()
    except Exception as e:
        print(f"Could not load from database: {e}")

if not api_key or not api_secret:
    print("ERROR: No API credentials found")
    print("Set COINSTORE_API_KEY and COINSTORE_API_SECRET environment variables")
    sys.exit(1)

print("=" * 80)
print("COINSTORE DIRECT TEST (requests library)")
print("=" * 80)
print(f"\nAPI Key: {api_key[:10]}...{api_key[-5:]}")
print(f"Secret length: {len(api_secret)}")

# Check server IP
import subprocess
try:
    ipv4 = subprocess.check_output(['curl', '-s', '-4', 'ifconfig.me'], text=True).strip()
    print(f"Server IPv4: {ipv4}")
    print(f"Expected IP: 5.161.64.209")
    if ipv4 != "5.161.64.209":
        print(f"⚠️  WARNING: IP mismatch! Coinstore whitelist may need {ipv4}")
except:
    pass

# Test balance endpoint (simplest case)
url = "https://api.coinstore.com/api/spot/accountList"
secret = api_secret.encode('utf-8')
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))

print(f"\nSignature calculation:")
print(f"  Expires: {expires}")
print(f"  Expires key: {expires_key}")

# Step 1: HMAC(secret, expires_key)
key = hmac.new(secret, expires_key.encode('utf-8'), hashlib.sha256).hexdigest()
print(f"  Derived key: {key[:32]}...")

# Step 2: HMAC(key, payload)
payload = json.dumps({})
print(f"  Payload: {repr(payload)}")
sig = hmac.new(key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
print(f"  Signature: {sig[:32]}...")

headers = {
    "X-CS-APIKEY": api_key,
    "X-CS-SIGN": sig,
    "X-CS-EXPIRES": str(expires),
    "Content-Type": "application/json",
    "exch-language": "en_US"
}

print(f"\nMaking request...")
print(f"  URL: {url}")
print(f"  Method: POST")
print(f"  Headers: X-CS-APIKEY, X-CS-SIGN, X-CS-EXPIRES, Content-Type, exch-language")

try:
    r = requests.post(url, data=payload, headers=headers, timeout=10)
    print(f"\nResponse:")
    print(f"  Status: {r.status_code}")
    print(f"  Headers: {dict(r.headers)}")
    print(f"  Body: {r.text[:500]}")
    
    if r.status_code == 200:
        print("\n✅ SUCCESS! Balance fetch works with requests library.")
        print("   → Issue is likely in aiohttp request handling, not signature.")
    elif r.status_code == 401:
        if "signature-failed" in r.text:
            print("\n❌ FAILED: signature-failed (401)")
            print("   → Signature calculation issue OR IP whitelist/permissions")
            print("\n   Check:")
            print("   1. IP whitelist on Coinstore dashboard")
            print("   2. API key permissions (Spot Trading enabled)")
            print("   3. API key/secret match Coinstore dashboard exactly")
        else:
            print(f"\n❌ FAILED: 401 Unauthorized")
            print(f"   Response: {r.text[:200]}")
    else:
        print(f"\n❌ FAILED: HTTP {r.status_code}")
        print(f"   Response: {r.text[:500]}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
