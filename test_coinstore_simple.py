#!/usr/bin/env python3
"""Simple Coinstore test using app's own decryption."""
import sys
import os
sys.path.insert(0, '/opt/trading-bridge')

# Set up environment
os.chdir('/opt/trading-bridge')
from dotenv import load_dotenv
load_dotenv('/opt/trading-bridge/.env')

import hashlib
import hmac
import json
import math
import time
import requests

# Use app's decryption
from app.security import decrypt_credential
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT api_key_encrypted, api_secret_encrypted
        FROM exchange_credentials
        WHERE exchange = 'coinstore'
        LIMIT 1
    """))
    row = result.fetchone()
    if not row:
        print("ERROR: No Coinstore credentials found")
        sys.exit(1)
    
    api_key = decrypt_credential(row[0])
    api_secret = decrypt_credential(row[1])

print(f"✅ Loaded API key: {api_key[:10]}...")
print(f"✅ Secret length: {len(api_secret)}")

# Test balance check
print("\n" + "="*60)
print("TEST: Balance Check")
print("="*60)

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
    data=payload, headers=headers, timeout=10)

print(f"\nStatus: {r.status_code}")
print(f"Response: {r.text[:300]}")

if r.status_code == 200:
    print("\n✅ SUCCESS - Signature works with requests library!")
    print("   This means: Bug is in aiohttp, not signature generation")
elif r.status_code == 401:
    print("\n❌ FAILED - Signature rejected (401)")
    print("   This means: Signature issue OR IP whitelist/permissions")
else:
    print(f"\n⚠️  Status {r.status_code}")
