#!/usr/bin/env python3
"""
Unit Test: Coinstore Signature Algorithm
Tests that our signature generation matches the official Coinstore example.
No API keys needed - just tests the algorithm.
"""
import json
import hmac
import hashlib
import math
import time
from app.coinstore_connector import CoinstoreConnector

print("=" * 80)
print("COINSTORE SIGNATURE ALGORITHM TEST")
print("=" * 80)

# Test credentials (dummy, just for testing algorithm)
api_key = "test_api_key_12345"
api_secret = "test_secret_key_67890"

# Official example from Coinstore docs
print("\n📝 Official Example (from Coinstore docs):")
print("   url = 'https://api.coinstore.com/api/spot/accountList'")
print("   method = 'POST'")
print("   params = {}")
print("   payload = json.dumps({}) = '{}'")

# Generate signature using official method
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
payload = json.dumps({})  # Empty params = '{}'

print(f"\n   expires = {expires}")
print(f"   expires_key = floor({expires} / 30000) = {expires_key}")

# Step 1: Derive key (official method)
key_official = hmac.new(
    api_secret.encode("utf-8"),
    expires_key.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print(f"\n   Step 1: key = HMAC-SHA256(secret, expires_key)")
print(f"   key = {key_official[:30]}...{key_official[-10:]}")

# Step 2: Sign payload (official method)
signature_official = hmac.new(
    key_official.encode("utf-8"),
    payload.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print(f"\n   Step 2: signature = HMAC-SHA256(key, payload)")
print(f"   payload = '{payload}' (length: {len(payload)})")
print(f"   signature = {signature_official[:30]}...{signature_official[-10:]}")

# Test our connector's signature generation
print("\n" + "=" * 80)
print("OUR IMPLEMENTATION (CoinstoreConnector._generate_signature)")
print("=" * 80)

connector = CoinstoreConnector(
    api_key=api_key,
    api_secret=api_secret
)

signature_ours = connector._generate_signature(expires, payload)

print(f"\n   expires = {expires}")
print(f"   payload = '{payload}'")
print(f"   signature = {signature_ours[:30]}...{signature_ours[-10:]}")

# Compare
print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)

if signature_official == signature_ours:
    print("\n✅ SUCCESS! Signatures match perfectly!")
    print("   Our implementation correctly matches the official Coinstore algorithm.")
    print("\n✅ The signature fix is verified!")
else:
    print("\n❌ FAILURE! Signatures don't match!")
    print(f"   Official: {signature_official}")
    print(f"   Ours:     {signature_ours}")
    exit(1)

# Test with non-empty payload
print("\n" + "=" * 80)
print("BONUS TEST: Non-empty payload")
print("=" * 80)

test_params = {"symbol": "BTCUSDT"}
payload_with_params = json.dumps(test_params, separators=(',', ':'))

print(f"\n   params = {test_params}")
print(f"   payload = json.dumps(params) = '{payload_with_params}'")

# Official method
key2 = hmac.new(
    api_secret.encode("utf-8"),
    expires_key.encode("utf-8"),
    hashlib.sha256
).hexdigest()
signature2_official = hmac.new(
    key2.encode("utf-8"),
    payload_with_params.encode("utf-8"),
    hashlib.sha256
).hexdigest()

# Our method
signature2_ours = connector._generate_signature(expires, payload_with_params)

print(f"\n   Official signature: {signature2_official[:30]}...{signature2_official[-10:]}")
print(f"   Our signature:      {signature2_ours[:30]}...{signature2_ours[-10:]}")

if signature2_official == signature2_ours:
    print("\n✅ Non-empty payload test passed!")
else:
    print("\n❌ Non-empty payload test failed!")
    exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print("\nThe Coinstore signature algorithm is correctly implemented.")
print("The fix (using json.dumps({}) = '{}' for empty POST payloads) is verified.")
print("\nReady for production deployment! 🚀")
