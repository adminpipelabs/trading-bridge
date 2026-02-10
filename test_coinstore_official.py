#!/usr/bin/env python3
"""
Test Coinstore API using official documentation example.
Run this to verify API key/IP whitelist is working.
"""
import hashlib
import hmac
import json
import math
import time
import requests
import os
import sys
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text

# Try to get from Railway CLI if not in environment
import subprocess
import json

DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not DATABASE_URL or not ENCRYPTION_KEY:
    print("⚠️  Environment variables not set, trying Railway CLI...")
    try:
        result = subprocess.run(
            ["railway", "variables", "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            vars_data = json.loads(result.stdout)
            # Railway CLI returns a dict with variable names as keys
            if isinstance(vars_data, dict):
                if "DATABASE_URL" in vars_data and not DATABASE_URL:
                    DATABASE_URL = vars_data["DATABASE_URL"]
                    print("✅ Found DATABASE_URL from Railway CLI")
                if "ENCRYPTION_KEY" in vars_data and not ENCRYPTION_KEY:
                    ENCRYPTION_KEY = vars_data["ENCRYPTION_KEY"]
                    print("✅ Found ENCRYPTION_KEY from Railway CLI")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, AttributeError) as e:
        print(f"⚠️  Railway CLI not available or error: {e}")

# Check if we have what we need
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("   Options:")
    print("     1. Set: export DATABASE_URL='postgresql://...'")
    print("     2. Use Railway CLI: railway variables")
    print("     3. Or pass as args: python test_coinstore_official.py <DATABASE_URL> <ENCRYPTION_KEY>")
    if len(sys.argv) > 1:
        DATABASE_URL = sys.argv[1]
        print(f"✅ Using DATABASE_URL from command line")
    else:
        sys.exit(1)

if not ENCRYPTION_KEY:
    print("❌ ENCRYPTION_KEY not set")
    if len(sys.argv) > 2:
        ENCRYPTION_KEY = sys.argv[2]
        print(f"✅ Using ENCRYPTION_KEY from command line")
    else:
        sys.exit(1)

# Initialize Fernet
fernet = Fernet(ENCRYPTION_KEY.encode())

# Connect to database
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("COINSTORE OFFICIAL API TEST")
print("=" * 80)

# Get API credentials from database
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT ec.api_key_encrypted, ec.api_secret_encrypted
        FROM exchange_credentials ec
        JOIN clients cl ON cl.id = ec.client_id
        JOIN bots b ON b.account = cl.account_identifier
        WHERE b.connector = 'coinstore'
        LIMIT 1
    """))
    
    row = result.fetchone()
    if not row:
        print("❌ No Coinstore credentials found in database")
        sys.exit(1)
    
    api_key_encrypted = row[0]
    api_secret_encrypted = row[1]
    
    # Decrypt
    api_key = fernet.decrypt(api_key_encrypted.encode()).decode()
    api_secret = fernet.decrypt(api_secret_encrypted.encode()).decode()

print(f"\n📋 API Key: {api_key[:10]}...{api_key[-5:]}")
print(f"📋 Secret: {api_secret[:10]}...{api_secret[-5:]}")
print(f"📋 Key length: {len(api_key)}")
print(f"📋 Secret length: {len(api_secret)}")

# Official Coinstore example (exact from docs)
url = "https://api.coinstore.com/api/spot/accountList"
api_key_bytes = api_key.encode('utf-8')
secret_key_bytes = api_secret.encode('utf-8')

expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
expires_key_bytes = expires_key.encode("utf-8")

print(f"\n🔐 SIGNATURE GENERATION:")
print(f"   expires (ms): {expires}")
print(f"   expires_key: {expires_key}")

# Step 1: HMAC(secret, expires_key)
key = hmac.new(secret_key_bytes, expires_key_bytes, hashlib.sha256).hexdigest()
key_bytes = key.encode("utf-8")

print(f"   Step 1 - key: {key[:20]}...{key[-10:]}")

# Step 2: HMAC(key, payload)
payload_dict = {}
payload_json = json.dumps(payload_dict)
payload_bytes = payload_json.encode("utf-8")

signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()

print(f"   payload: '{payload_json}'")
print(f"   Step 2 - signature: {signature}")

# Headers (exact from official docs)
headers = {
    'X-CS-APIKEY': api_key,
    'X-CS-SIGN': signature,
    'X-CS-EXPIRES': str(expires),
    'exch-language': 'en_US',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}

print(f"\n📤 REQUEST:")
print(f"   URL: {url}")
print(f"   Method: POST")
print(f"   Headers:")
for k, v in headers.items():
    if k == 'X-CS-APIKEY':
        print(f"      {k}: {v[:10]}...{v[-5:]}")
    elif k == 'X-CS-SIGN':
        print(f"      {k}: {signature[:20]}...{signature[-10:]}")
    else:
        print(f"      {k}: {v}")
print(f"   Body (bytes): {payload_bytes}")

# Make request (exact from official docs)
print(f"\n📡 SENDING REQUEST...")
try:
    response = requests.request("POST", url, headers=headers, data=payload_bytes, timeout=30)
    
    print(f"\n📥 RESPONSE:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"   Response Text: {response.text}")
    
    if response.status_code == 200:
        print(f"\n✅ SUCCESS!")
        try:
            data = response.json()
            print(f"   Response JSON: {json.dumps(data, indent=2)}")
        except:
            print(f"   (Response is not JSON)")
    elif response.status_code == 1401:
        print(f"\n❌ ERROR 1401 - Possible causes:")
        print(f"   1. IP not in whitelist")
        print(f"   2. Signature failure")
        print(f"   3. Token expired")
    else:
        print(f"\n❌ ERROR {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ REQUEST FAILED: {e}")
    import traceback
    traceback.print_exc()
