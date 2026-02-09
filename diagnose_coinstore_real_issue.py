#!/usr/bin/env python3
"""
Diagnostic script to identify the REAL Coinstore issue.
This will show EXACTLY what we're sending and what we're receiving.
"""
import asyncio
import aiohttp
import hmac
import hashlib
import json
import math
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_coinstore_direct():
    """Test Coinstore API directly with full request/response logging."""
    
    # Try to get from database first
    api_key = None
    api_secret = None
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from app.security import decrypt_credential
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        if DATABASE_URL:
            engine = create_engine(DATABASE_URL)
            Session = sessionmaker(bind=engine)
            db = Session()
            
            creds = db.execute(text("""
                SELECT api_key_encrypted, api_secret_encrypted
                FROM exchange_credentials
                WHERE exchange = 'coinstore'
                LIMIT 1
            """)).fetchone()
            
            if creds:
                api_key = decrypt_credential(creds.api_key_encrypted).strip()
                api_secret = decrypt_credential(creds.api_secret_encrypted).strip()
                print("✅ Loaded keys from database")
            db.close()
    except Exception as db_err:
        print(f"⚠️  Could not load from database: {db_err}")
    
    # Fallback to environment
    if not api_key or not api_secret:
        api_key = os.getenv("COINSTORE_API_KEY")
        api_secret = os.getenv("COINSTORE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: No API keys found")
        print("   Set COINSTORE_API_KEY and COINSTORE_API_SECRET in environment")
        print("   Or ensure exchange_credentials table has coinstore entry")
        return
    
    print("=" * 80)
    print("COINSTORE API DIAGNOSTIC TEST")
    print("=" * 80)
    print(f"\n📋 API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"📋 API Secret: {api_secret[:10]}...{api_secret[-5:]}")
    print(f"📋 Key lengths: key={len(api_key)}, secret={len(api_secret)}")
    
    # Test endpoint
    url = "https://api.coinstore.com/api/spot/accountList"
    method = "POST"
    
    # Prepare payload (empty for accountList)
    payload = json.dumps({})
    
    # Generate signature
    expires = int(time.time() * 1000)
    expires_key = str(math.floor(expires / 30000))
    
    print(f"\n🔐 SIGNATURE GENERATION:")
    print(f"   expires (ms): {expires}")
    print(f"   expires_key: {expires_key}")
    print(f"   payload: '{payload}'")
    
    # Step 1: Derive key
    key = hmac.new(
        api_secret.encode('utf-8'),
        expires_key.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    print(f"   derived_key: {key[:20]}...{key[-10:]}")
    
    # Step 2: Sign payload
    signature = hmac.new(
        key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    print(f"   signature: {signature[:20]}...{signature[-10:]}")
    
    # Prepare headers
    headers = {
        'X-CS-APIKEY': api_key,
        'X-CS-SIGN': signature,
        'X-CS-EXPIRES': str(expires),
        'exch-language': 'en_US',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }
    
    print(f"\n📤 REQUEST:")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    print(f"   Headers:")
    for k, v in headers.items():
        if k == 'X-CS-APIKEY':
            print(f"      {k}: {v[:10]}...{v[-5:]}")
        elif k == 'X-CS-SIGN':
            print(f"      {k}: {v[:20]}...{v[-10:]}")
        else:
            print(f"      {k}: {v}")
    print(f"   Body: {payload}")
    
    # Make request
    print(f"\n📡 SENDING REQUEST...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=json.loads(payload), headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"\n📥 RESPONSE:")
                print(f"   HTTP Status: {status}")
                print(f"   Response Length: {len(response_text)} bytes")
                print(f"   Response Headers:")
                for k, v in response.headers.items():
                    print(f"      {k}: {v}")
                print(f"   Response Body:")
                print(f"      {response_text}")
                
                # Try to parse JSON
                try:
                    response_json = await response.json()
                    print(f"\n📊 PARSED JSON:")
                    print(f"   {json.dumps(response_json, indent=2)}")
                    
                    code = response_json.get('code')
                    message = response_json.get('message') or response_json.get('msg')
                    
                    if code == 0 or code == "0":
                        print(f"\n✅ SUCCESS! Code: {code}")
                        print(f"   Message: {message}")
                        data = response_json.get('data', [])
                        print(f"   Data entries: {len(data)}")
                        if data:
                            print(f"   First entry: {data[0]}")
                    else:
                        print(f"\n❌ FAILED! Code: {code}")
                        print(f"   Message: {message}")
                        print(f"\n🔍 ANALYSIS:")
                        if code == 1401:
                            print(f"   Error 1401 = Unauthorized")
                            print(f"   Possible causes:")
                            print(f"   1. Invalid API key or secret")
                            print(f"   2. Signature mismatch (check signature algorithm)")
                            print(f"   3. Expired timestamp (check expires calculation)")
                            print(f"   4. Wrong payload format")
                            print(f"   5. API key permissions (needs 'spot' and 'read')")
                            print(f"   6. IP whitelist (if enabled)")
                        else:
                            print(f"   Unknown error code: {code}")
                            
                except Exception as json_err:
                    print(f"\n❌ Failed to parse JSON: {json_err}")
                    print(f"   Raw response: {response_text[:500]}")
                    
        except Exception as e:
            print(f"\n❌ REQUEST FAILED:")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coinstore_direct())
