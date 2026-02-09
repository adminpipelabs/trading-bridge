#!/usr/bin/env python3
"""
Test Coinstore Signature Fix
Verifies that the signature generation matches Coinstore's official example.
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
from app.coinstore_connector import CoinstoreConnector
from app.security import decrypt_credential

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 80)
print("COINSTORE SIGNATURE FIX TEST")
print("=" * 80)

# Find Coinstore credentials
print("\n🔍 Looking for Coinstore credentials in database...")

# Get first client with Coinstore credentials
creds = db.execute(text("""
    SELECT ec.exchange, ec.api_key_encrypted, ec.api_secret_encrypted, 
           c.account_identifier, c.name as client_name
    FROM exchange_credentials ec
    JOIN clients c ON c.id = ec.client_id
    WHERE ec.exchange ILIKE '%coinstore%'
    LIMIT 1
""")).fetchone()

if not creds:
    print("❌ No Coinstore credentials found in database")
    print("\n💡 To test manually, set environment variables:")
    print("   export COINSTORE_API_KEY=your_key")
    print("   export COINSTORE_API_SECRET=your_secret")
    
    # Try environment variables
    api_key = os.getenv("COINSTORE_API_KEY")
    api_secret = os.getenv("COINSTORE_API_SECRET")
    
    if not api_key or not api_secret:
        print("\n❌ No credentials available. Exiting.")
        sys.exit(0)
    else:
        print(f"\n✅ Using credentials from environment variables")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
else:
    print(f"✅ Found credentials for client: {creds.client_name}")
    print(f"   Account: {creds.account_identifier}")
    
    # Decrypt credentials
    try:
        api_key = decrypt_credential(creds.api_key_encrypted)
        api_secret = decrypt_credential(creds.api_secret_encrypted)
        print(f"   ✅ Decrypted successfully")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
    except Exception as e:
        print(f"   ❌ Failed to decrypt: {e}")
        sys.exit(1)

# Test 1: Verify signature generation matches official example
print("\n" + "=" * 80)
print("TEST 1: Signature Generation (matches official example)")
print("=" * 80)

# Official example from Coinstore docs
url = "https://api.coinstore.com/api/spot/accountList"
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
expires_key_bytes = expires_key.encode("utf-8")
payload = json.dumps({})  # Empty params = '{}'
payload_bytes = payload.encode("utf-8")

# Step 1: Derive key
key = hmac.new(api_secret.encode("utf-8"), expires_key_bytes, hashlib.sha256).hexdigest()
key_bytes = key.encode("utf-8")

# Step 2: Sign payload
signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()

print(f"\n📝 Signature details:")
print(f"   expires: {expires}")
print(f"   expires_key: {expires_key}")
print(f"   payload: '{payload}' (length: {len(payload)})")
print(f"   derived_key: {key[:20]}...{key[-10:]}")
print(f"   signature: {signature[:20]}...{signature[-10:]}")

# Test 2: Use CoinstoreConnector to generate signature
print("\n" + "=" * 80)
print("TEST 2: CoinstoreConnector Signature Generation")
print("=" * 80)

connector = CoinstoreConnector(
    api_key=api_key,
    api_secret=api_secret,
    proxy_url=os.getenv("QUOTAGUARD_PROXY_URL") or os.getenv("HTTP_PROXY")
)

# Generate signature using our connector
connector_signature = connector._generate_signature(expires, payload)

print(f"\n📝 Connector signature:")
print(f"   payload: '{payload}'")
print(f"   signature: {connector_signature[:20]}...{connector_signature[-10:]}")

if signature == connector_signature:
    print(f"\n✅ SIGNATURE MATCHES! Our implementation is correct.")
else:
    print(f"\n❌ SIGNATURE MISMATCH!")
    print(f"   Expected: {signature[:40]}...")
    print(f"   Got:      {connector_signature[:40]}...")
    sys.exit(1)

# Test 3: Actual API call
print("\n" + "=" * 80)
print("TEST 3: Actual API Call (get_balances)")
print("=" * 80)

async def test_balance():
    try:
        print("\n💰 Calling get_balances()...")
        result = await connector.get_balances()
        
        code = result.get('code')
        if code == 0 or code == "0":
            print("   ✅ API call successful!")
            balances_list = result.get('data', [])
            print(f"   Found {len(balances_list)} account entries")
            
            # Show non-zero balances
            non_zero = []
            for account in balances_list:
                currency = account.get('currency', '').upper()
                balance = float(account.get('balance', 0) or 0)
                account_type = account.get('type', 0)
                type_name = account.get('typeName', '')
                
                if balance > 0:
                    non_zero.append({
                        'currency': currency,
                        'balance': balance,
                        'type': type_name or ('AVAILABLE' if account_type == 1 else 'FROZEN' if account_type == 4 else f'Type {account_type}')
                    })
            
            if non_zero:
                print("\n   💰 Non-zero balances:")
                for b in non_zero:
                    print(f"      {b['currency']}: {b['balance']} ({b['type']})")
            else:
                print("   ℹ️  All balances are zero")
            
            return True
        else:
            error_msg = result.get('msg') or result.get('message') or str(result)
            error_code = result.get('code', 'unknown')
            print(f"   ❌ API error (code {error_code}): {error_msg}")
            
            if error_code == 1401:
                print("\n   ⚠️  Unauthorized (1401) - Possible causes:")
                print("      1. API key/secret incorrect")
                print("      2. API key doesn't have spot trading permissions")
                print("      3. IP whitelist enabled (add Railway IPs)")
                print("      4. Signature still incorrect (check payload format)")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await connector.close()

# Run async test
success = asyncio.run(test_balance())

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

if success:
    print("✅ All tests passed!")
    print("   - Signature generation matches official example")
    print("   - CoinstoreConnector generates correct signature")
    print("   - API call successful - balances fetched")
    print("\n🎉 The signature fix is working correctly!")
else:
    print("❌ Some tests failed")
    print("   Check the error messages above for details")

db.close()
