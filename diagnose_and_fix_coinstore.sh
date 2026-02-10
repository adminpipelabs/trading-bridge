#!/bin/bash
# Comprehensive Coinstore diagnostic and fix
# Run on Hetzner: bash diagnose_and_fix_coinstore.sh

set -e

cd /opt/trading-bridge
source venv/bin/activate

echo "=========================================="
echo "COINSTORE DIAGNOSTIC & FIX"
echo "=========================================="
echo ""

# Step 1: Get credentials from database
echo "📋 Step 1: Loading credentials from database..."
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
    
    api_key = fernet.decrypt(row[0].encode()).decode().strip()
    api_secret = fernet.decrypt(row[1].encode()).decode().strip()
    bot_id = row[2]
    bot_name = row[3]
    
    print(f"✅ Bot: {bot_name} ({bot_id})")
    print(f"✅ API Key: {api_key}")
    print(f"✅ API Secret: {api_secret[:10]}...{api_secret[-5:]}")
    print(f"✅ Server IP: 5.161.64.209")
    print("")
    
    # Test with official Coinstore example (exact from docs)
    print("📡 Step 2: Testing Coinstore API with official method...")
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
    print("")
    print("   Making request...")
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload_bytes, timeout=30)
        print(f"")
        print(f"📥 RESPONSE:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('code') == 0:
                    print(f"")
                    print(f"✅ SUCCESS! Balance data:")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"")
                    print(f"❌ API Error: code={data.get('code')}, msg={data.get('message')}")
                    if data.get('code') == 1401:
                        print(f"")
                        print(f"🔍 1401 Unauthorized - Possible causes:")
                        print(f"   1. IP 5.161.64.209 not whitelisted on Coinstore")
                        print(f"   2. API secret doesn't match Coinstore dashboard")
                        print(f"   3. API key permissions missing (Read/Trade)")
            except:
                print(f"   (Response is not JSON)")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "If you see 1401 error:"
echo "  1. Check Coinstore dashboard → API Key: 42b5c7c40bf625e7fcffd16a654b6ed0"
echo "  2. Verify IP 5.161.64.209 is in the IP binding list"
echo "  3. Verify API secret matches what's shown above"
echo "  4. Check API key permissions (Read + Trade enabled)"
echo ""
