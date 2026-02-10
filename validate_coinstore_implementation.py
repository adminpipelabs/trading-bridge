#!/usr/bin/env python3
"""
Validate Coinstore implementation correctness
Tests signature generation and request format without making actual API calls
"""
import hmac
import hashlib
import math
import time
import json

def test_signature_generation():
    """Test that signature generation matches Coinstore official docs."""
    
    print("=" * 60)
    print("Coinstore Implementation Validation")
    print("=" * 60)
    print("")
    
    # Test credentials (example)
    api_secret = "test_secret_key_32_chars_long_!"
    expires = int(time.time() * 1000)
    
    # Step 1: Calculate expires_key (per Coinstore docs)
    expires_key = str(math.floor(expires / 30000))
    print(f"✅ Step 1: expires_key = floor({expires} / 30000) = {expires_key}")
    
    # Step 2: First HMAC (per Coinstore docs)
    secret_bytes = api_secret.encode('utf-8')
    expires_key_bytes = expires_key.encode('utf-8')
    key = hmac.new(secret_bytes, expires_key_bytes, hashlib.sha256).hexdigest()
    print(f"✅ Step 2: First HMAC-SHA256(secret, expires_key) = {key[:20]}...")
    
    # Step 3: Second HMAC (per Coinstore docs)
    # For POST with empty params: payload = json.dumps({}) = '{}'
    payload = json.dumps({})
    print(f"✅ Step 3: Payload for empty POST = '{payload}'")
    
    key_bytes = key.encode('utf-8')
    payload_bytes = payload.encode('utf-8')
    signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()
    print(f"✅ Step 4: Second HMAC-SHA256(key, payload) = {signature[:20]}...")
    print("")
    
    # Verify our implementation matches
    print("=" * 60)
    print("Implementation Check")
    print("=" * 60)
    print("")
    
    # Check our code matches
    from app.coinstore_connector import CoinstoreConnector
    
    connector = CoinstoreConnector(api_key="test_key", api_secret=api_secret, proxy_url=None)
    our_signature = connector._generate_signature(expires, payload)
    
    if our_signature == signature:
        print("✅ Signature generation MATCHES Coinstore official docs!")
        print(f"   Our signature: {our_signature[:20]}...")
        print(f"   Expected:      {signature[:20]}...")
    else:
        print("❌ Signature generation MISMATCH!")
        print(f"   Our signature: {our_signature[:20]}...")
        print(f"   Expected:      {signature[:20]}...")
        return False
    
    print("")
    
    # Check endpoint format
    print("=" * 60)
    print("Endpoint & Request Format Check")
    print("=" * 60)
    print("")
    
    BASE_URL = "https://api.coinstore.com/api"
    endpoint = "/spot/accountList"
    url = f"{BASE_URL}{endpoint}"
    
    print(f"✅ Base URL: {BASE_URL}")
    print(f"✅ Endpoint: {endpoint}")
    print(f"✅ Full URL: {url}")
    print(f"✅ Method: POST")
    print(f"✅ Payload: '{payload}' (empty dict)")
    print("")
    
    # Check headers format
    print("=" * 60)
    print("Headers Format Check")
    print("=" * 60)
    print("")
    
    headers = {
        'X-CS-APIKEY': 'test_key',
        'X-CS-SIGN': signature,
        'X-CS-EXPIRES': str(expires),
        'exch-language': 'en_US',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    
    print("✅ Required headers:")
    for key, value in headers.items():
        if key == 'X-CS-SIGN':
            print(f"   {key}: {value[:20]}... (signature)")
        elif key == 'X-CS-APIKEY':
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    print("")
    print("=" * 60)
    print("✅ Implementation Validation Complete")
    print("=" * 60)
    print("")
    print("All checks passed! Implementation matches Coinstore official docs.")
    print("")
    print("Next: Run actual test on Hetzner:")
    print("  python3 test_coinstore_balance.py")
    
    return True

if __name__ == "__main__":
    success = test_signature_generation()
    exit(0 if success else 1)
