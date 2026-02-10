#!/usr/bin/env python3
"""
Direct Coinstore API test - run on Hetzner
Tests with exact credentials from database
"""
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

print("=" * 80)
print("COINSTORE DIRECT API TEST")
print("=" * 80)
print()

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            ec.api_key_encrypted, 
            ec.api_secret_encrypted,
            b.id as bot_id,
            b.name as bot_name
        FROM exchange_credentials ec
        JOIN clients cl ON cl.id = ec.client_id
        JOIN bots b ON b.account = cl.account_identifier
        WHERE ec.exchange = 'coinstore' 
          AND b.connector = 'coinstore'
          AND b.status = 'running'
        ORDER BY b.name LIKE '%Coinstore%' DESC
        LIMIT 1
    """))
    
    row = result.fetchone()
    if not row:
        print("❌ No Coinstore credentials found")
        sys.exit(1)
    
    api_key_raw = fernet.decrypt(row[0].encode()).decode()
    api_secret_raw = fernet.decrypt(row[1].encode()).decode()
    
    # Strip whitespace (common issue)
    api_key = api_key_raw.strip()
    api_secret = api_secret_raw.strip()
    bot_id = row[2]
    bot_name = row[3]
    
    print(f"✅ Bot: {bot_name} ({bot_id})")
    print(f"✅ API Key: {api_key}")
    print(f"✅ API Key Length: {len(api_key)}")
    print(f"✅ API Secret Length: {len(api_secret)}")
    print(f"✅ API Secret Preview: {api_secret[:10]}...{api_secret[-5:]}")
    print(f"✅ Server IP: 5.161.64.209")
    print()
    
    # Check for whitespace issues
    if api_key != api_key_raw or api_secret != api_secret_raw:
        print(f"⚠️  Stripped whitespace from credentials")
        print(f"   API Key had {len(api_key_raw) - len(api_key)} extra chars")
        print(f"   API Secret had {len(api_secret_raw) - len(api_secret)} extra chars")
        print()
    
    # Test with official Coinstore example (exact from docs)
    print("📡 Testing Coinstore API with official method...")
    url = "https://api.coinstore.com/api/spot/accountList"
    
    expires = int(time.time() * 1000)
    expires_key = str(math.floor(expires / 30000))
    expires_key_bytes = expires_key.encode("utf-8")
    
    secret_key_bytes = api_secret.encode("utf-8")
    key = hmac.new(secret_key_bytes, expires_key_bytes, hashlib.sha256).hexdigest()
    key_bytes = key.encode("utf-8")
    
    payload_dict = {}
    payload_json = json.dumps(payload_dict)
    payload_bytes = payload_json.encode("utf-8")
    
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
    
    print(f"   URL: {url}")
    print(f"   Expires: {expires}")
    print(f"   Expires Key: {expires_key}")
    print(f"   Payload: {payload_json}")
    print(f"   Signature: {signature[:20]}...{signature[-10:]}")
    print()
    print("   Making request...")
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload_bytes, timeout=30)
        print()
        print(f"📥 RESPONSE:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('code') == 0 or data.get('code') == '0':
                    print(f"✅ SUCCESS! Balance data:")
                    print(json.dumps(data, indent=2))
                    print()
                    print("=" * 80)
                    print("✅ COINSTORE API IS WORKING!")
                    print("=" * 80)
                else:
                    error_code = data.get('code')
                    error_msg = data.get('msg') or data.get('message') or 'Unknown error'
                    print(f"❌ API Error: code={error_code}, msg={error_msg}")
                    print()
                    if error_code == 1401:
                        print("=" * 80)
                        print("❌ 1401 UNAUTHORIZED - CHECK THESE:")
                        print("=" * 80)
                        print()
                        print("1. IP Whitelist:")
                        print(f"   - Go to Coinstore dashboard")
                        print(f"   - Find API key: {api_key}")
                        print(f"   - Check IP binding list")
                        print(f"   - Verify IP 5.161.64.209 is listed")
                        print()
                        print("2. API Secret:")
                        print(f"   - Compare secret in database vs Coinstore dashboard")
                        print(f"   - Database secret preview: {api_secret[:10]}...{api_secret[-5:]}")
                        print(f"   - They must match EXACTLY (no extra spaces)")
                        print()
                        print("3. API Key Permissions:")
                        print(f"   - Check API key has 'Read' permission enabled")
                        print(f"   - Check API key has 'Spot Trading' permission enabled")
                        print()
                        print("4. Test with this exact secret:")
                        print(f"   Run: python3 test_coinstore_simple.py {api_key} YOUR_SECRET_FROM_DASHBOARD")
                        print()
            except Exception as json_err:
                print(f"❌ Failed to parse JSON: {json_err}")
                print(f"   Raw response: {response.text[:500]}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
