#!/usr/bin/env python3
"""
Direct Coinstore API Key Test
Tests the exact same code as the example to verify keys work.
"""
import os
import sys
import asyncio
import json
import hmac
import hashlib
import math
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.security import decrypt_credential

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 80)
print("COINSTORE API KEY DIRECT TEST")
print("=" * 80)

# Get Coinstore credentials
creds = db.execute(text("""
    SELECT api_key_encrypted, api_secret_encrypted
    FROM exchange_credentials
    WHERE exchange = 'coinstore'
    LIMIT 1
""")).fetchone()

if not creds:
    print("❌ No Coinstore credentials found")
    sys.exit(1)

api_key = decrypt_credential(creds.api_key_encrypted).strip()
api_secret = decrypt_credential(creds.api_secret_encrypted).strip()

print(f"\n✅ Decrypted keys:")
print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
print(f"   API Secret: {api_secret[:10]}...{api_secret[-5:]}")
print(f"   Key lengths: api_key={len(api_key)}, api_secret={len(api_secret)}")

# Test using exact example code
print("\n" + "=" * 80)
print("TESTING WITH EXACT EXAMPLE CODE")
print("=" * 80)

url = "https://api.coinstore.com/api/spot/accountList"
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
expires_key_bytes = expires_key.encode("utf-8")

# Step 1: Derive key (exact example)
key = hmac.new(api_secret.encode("utf-8"), expires_key_bytes, hashlib.sha256).hexdigest()
key_bytes = key.encode("utf-8")

# Step 2: Sign payload (exact example)
payload = json.dumps({})  # '{}'
payload_bytes = payload.encode("utf-8")
signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()

print(f"\n📝 Signature details:")
print(f"   expires: {expires}")
print(f"   expires_key: {expires_key}")
print(f"   payload: '{payload}' (bytes: {payload_bytes})")
print(f"   signature: {signature[:30]}...{signature[-10:]}")

# Test with aiohttp (our implementation)
print("\n" + "=" * 80)
print("TESTING WITH OUR CONNECTOR")
print("=" * 80)

async def test_connector():
    from app.coinstore_connector import CoinstoreConnector
    
    connector = CoinstoreConnector(
        api_key=api_key,
        api_secret=api_secret
    )
    
    try:
        print("\n💰 Calling get_balances()...")
        result = await connector.get_balances()
        
        code = result.get('code')
        if code == 0 or code == "0":
            print("   ✅ SUCCESS! Balance fetch worked!")
            balances_list = result.get('data', [])
            print(f"   Found {len(balances_list)} account entries")
            
            # Show balances
            for account in balances_list[:5]:
                currency = account.get('currency', '').upper()
                balance = float(account.get('balance', 0) or 0)
                account_type = account.get('type', 0)
                type_name = account.get('typeName', '')
                
                if balance > 0:
                    print(f"      {currency}: {balance} ({type_name or f'Type {account_type}'})")
            
            return True
        else:
            error_msg = result.get('msg') or result.get('message') or str(result)
            error_code = result.get('code', 'unknown')
            print(f"   ❌ API error (code {error_code}): {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await connector.close()

success = asyncio.run(test_connector())

print("\n" + "=" * 80)
if success:
    print("✅ KEYS WORK! The issue might be in how keys are passed to connector.")
else:
    print("❌ KEYS DON'T WORK - API keys may be invalid or have wrong permissions.")
print("=" * 80)

db.close()
