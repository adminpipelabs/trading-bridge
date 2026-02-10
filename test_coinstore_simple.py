#!/usr/bin/env python3
"""
Test Coinstore API using official documentation example.
Simplified version - takes API key and secret as arguments.
"""
import hashlib
import hmac
import json
import math
import time
import requests
import sys

if len(sys.argv) < 3:
    print("Usage: python3 test_coinstore_simple.py <API_KEY> <API_SECRET>")
    print("\nExample:")
    print("  python3 test_coinstore_simple.py 42b5c7c40bf625e7fcffd16a654b6ed0 YOUR_SECRET")
    sys.exit(1)

api_key = sys.argv[1]
api_secret = sys.argv[2]

print("=" * 80)
print("COINSTORE OFFICIAL API TEST")
print("=" * 80)

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
