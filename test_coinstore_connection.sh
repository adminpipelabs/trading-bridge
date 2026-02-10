#!/bin/bash
# Quick test script to verify Coinstore IP whitelisting is working
# Run on Hetzner: bash test_coinstore_connection.sh

set -e

echo "=========================================="
echo "Coinstore Connection Test"
echo "=========================================="
echo ""

cd /opt/trading-bridge
source venv/bin/activate

echo "🧪 Testing Coinstore API connection..."
echo ""

python3 << 'PYTHON_SCRIPT'
import os
import sys
from sqlalchemy import create_engine, text
from cryptography.fernet import Fernet
import hashlib
import hmac
import json
import math
import time
import requests

DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not DATABASE_URL or not ENCRYPTION_KEY:
    print("❌ DATABASE_URL or ENCRYPTION_KEY not set")
    sys.exit(1)

fernet = Fernet(ENCRYPTION_KEY.encode())
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            ec.api_key_encrypted, 
            ec.api_secret_encrypted
        FROM exchange_credentials ec
        WHERE ec.exchange = 'coinstore'
        LIMIT 1
    """))
    
    row = result.fetchone()
    if not row:
        print("❌ No Coinstore credentials found in database")
        sys.exit(1)
    
    api_key_encrypted = row[0]
    api_secret_encrypted = row[1]
    
    # Decrypt
    api_key = fernet.decrypt(api_key_encrypted.encode()).decode().strip()
    api_secret = fernet.decrypt(api_secret_encrypted.encode()).decode().strip()
    
    print(f"✅ Loaded credentials from database")
    print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"   Secret: {api_secret[:5]}...{api_secret[-3:]}")
    print("")

# Generate signature
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
expires_key_bytes = expires_key.encode("utf-8")

key = hmac.new(api_secret.encode(), expires_key_bytes, hashlib.sha256).hexdigest()
key_bytes = key.encode("utf-8")

payload = json.dumps({})
payload_bytes = payload.encode("utf-8")

signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()

headers = {
    'X-CS-APIKEY': api_key,
    'X-CS-SIGN': signature,
    'X-CS-EXPIRES': str(expires),
    'exch-language': 'en_US',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}

url = "https://api.coinstore.com/api/spot/accountList"

print("📡 Making API request to Coinstore...")
print(f"   URL: {url}")
print(f"   Method: POST")
print("")

try:
    response = requests.post(url, headers=headers, data=payload_bytes, timeout=10)
    
    print("=" * 60)
    print(f"Status Code: {response.status_code}")
    print("=" * 60)
    print("")
    
    if response.status_code == 200:
        try:
            data = response.json()
            code = data.get('code', 'unknown')
            msg = data.get('msg', '')
            
            if code == 0:
                print("✅ SUCCESS! Coinstore connection working!")
                print("")
                print("Response:")
                print(json.dumps(data, indent=2))
                print("")
                print("🎉 IP whitelisting is working correctly!")
            else:
                print(f"⚠️  Response code: {code}")
                print(f"   Message: {msg}")
                if code == 1401:
                    print("")
                    print("❌ Still getting 1401 - IP whitelist may not be active yet")
                    print("   Wait 1-2 minutes and try again")
        except:
            print("Response text:")
            print(response.text[:500])
    elif response.status_code == 401 or response.status_code == 403:
        print("❌ Authentication failed")
        print(f"   Status: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Code: {error_data.get('code', 'unknown')}")
            print(f"   Message: {error_data.get('msg', 'unknown')}")
        except:
            print(f"   Response: {response.text[:200]}")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    sys.exit(1)

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
