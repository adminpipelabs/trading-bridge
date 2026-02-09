#!/usr/bin/env python3
"""
Manual Coinstore Signature Test
Tests signature generation against official Coinstore example.

Usage:
    export COINSTORE_API_KEY=your_key
    export COINSTORE_API_SECRET=your_secret
    python3 test_coinstore_signature_manual.py
"""
import os
import json
import hmac
import hashlib
import math
import time
import asyncio
from app.coinstore_connector import CoinstoreConnector

print("=" * 80)
print("COINSTORE SIGNATURE FIX TEST (Manual)")
print("=" * 80)

api_key = os.getenv("COINSTORE_API_KEY")
api_secret = os.getenv("COINSTORE_API_SECRET")

if not api_key or not api_secret:
    print("\n❌ Please set environment variables:")
    print("   export COINSTORE_API_KEY=your_key")
    print("   export COINSTORE_API_SECRET=your_secret")
    sys.exit(1)

print(f"\n✅ Using API Key: {api_key[:8]}...{api_key[-4:]}")

# Test 1: Official example signature
print("\n" + "=" * 80)
print("TEST 1: Official Example Signature Generation")
print("=" * 80)

expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
payload = json.dumps({})  # Empty params = '{}'

# Official example method
key_official = hmac.new(
    api_secret.encode("utf-8"),
    expires_key.encode("utf-8"),
    hashlib.sha256
).hexdigest()

signature_official = hmac.new(
    key_official.encode("utf-8"),
    payload.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print(f"\n📝 Official example:")
print(f"   expires: {expires}")
print(f"   expires_key: {expires_key}")
print(f"   payload: '{payload}' (length: {len(payload)})")
print(f"   signature: {signature_official[:30]}...{signature_official[-10:]}")

# Test 2: Our connector signature
print("\n" + "=" * 80)
print("TEST 2: CoinstoreConnector Signature")
print("=" * 80)

connector = CoinstoreConnector(
    api_key=api_key,
    api_secret=api_secret,
    proxy_url=os.getenv("QUOTAGUARD_PROXY_URL") or os.getenv("HTTP_PROXY")
)

signature_ours = connector._generate_signature(expires, payload)

print(f"\n📝 Our connector:")
print(f"   payload: '{payload}'")
print(f"   signature: {signature_ours[:30]}...{signature_ours[-10:]}")

# Compare
if signature_official == signature_ours:
    print(f"\n✅ SIGNATURE MATCHES! Our implementation is correct.")
else:
    print(f"\n❌ SIGNATURE MISMATCH!")
    print(f"   Expected: {signature_official}")
    print(f"   Got:      {signature_ours}")
    exit(1)

# Test 3: Actual API call
print("\n" + "=" * 80)
print("TEST 3: Actual API Call")
print("=" * 80)

async def test_api():
    try:
        print("\n💰 Calling get_balances()...")
        result = await connector.get_balances()
        
        code = result.get('code')
        if code == 0 or code == "0":
            print("   ✅ API call successful!")
            balances_list = result.get('data', [])
            print(f"   Found {len(balances_list)} account entries")
            
            # Show balances
            for account in balances_list[:5]:  # Show first 5
                currency = account.get('currency', '').upper()
                balance = float(account.get('balance', 0) or 0)
                account_type = account.get('type', 0)
                type_name = account.get('typeName', '')
                
                if balance > 0:
                    print(f"      {currency}: {balance} ({type_name or f'Type {account_type}'})")
            
            print("\n🎉 SUCCESS! Signature fix is working correctly!")
            return True
        else:
            error_msg = result.get('msg') or result.get('message') or str(result)
            error_code = result.get('code', 'unknown')
            print(f"   ❌ API error (code {error_code}): {error_msg}")
            
            if error_code == 1401:
                print("\n   ⚠️  Unauthorized (1401) - Check:")
                print("      - API key/secret correct")
                print("      - API key has spot trading permissions")
                print("      - IP whitelist (if enabled)")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await connector.close()

success = asyncio.run(test_api())

print("\n" + "=" * 80)
if success:
    print("✅ ALL TESTS PASSED - Signature fix verified!")
else:
    print("❌ API call failed - check credentials and permissions")
print("=" * 80)
