#!/usr/bin/env python3
"""
Test Coinstore Signature with EXACT Railway Parameters
This will prove if the signature generation is correct or not.
"""
import json
import hmac
import hashlib
import math
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.security import decrypt_credential

print("=" * 80)
print("COINSTORE SIGNATURE VERIFICATION - EXACT RAILWAY PARAMETERS")
print("=" * 80)

# Exact values from Railway logs (22:58:18 UTC)
RAILWAY_EXPIRES = 1770677890477
RAILWAY_EXPIRES_KEY = 59022596
RAILWAY_PAYLOAD = '{}'
RAILWAY_SIGNATURE = 'b681b1dfb4fe23effc5815ebfbdc214ded6db952254d63762c1fb70c7060bb5f'
RAILWAY_API_KEY = '42b5c7c40bf625e7fcffd16a654b6ed0'

print(f"\nRailway Request Parameters:")
print(f"  Expires: {RAILWAY_EXPIRES}")
print(f"  Expires Key: {RAILWAY_EXPIRES_KEY}")
print(f"  Payload: '{RAILWAY_PAYLOAD}'")
print(f"  Expected Signature: {RAILWAY_SIGNATURE}")
print(f"  API Key: {RAILWAY_API_KEY}")
print()

# Get secret from database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("   Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
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
    
    print(f"✅ Decrypted keys from database:")
    print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"   Secret Length: {len(api_secret)}")
    print()
    
    # Verify API key matches
    if api_key != RAILWAY_API_KEY:
        print(f"❌ API KEY MISMATCH!")
        print(f"   Database: {api_key}")
        print(f"   Railway:  {RAILWAY_API_KEY}")
        sys.exit(1)
    else:
        print(f"✅ API Key matches Railway logs")
    
    # Generate signature with EXACT Railway parameters
    print()
    print("=" * 80)
    print("GENERATING SIGNATURE WITH EXACT RAILWAY PARAMETERS")
    print("=" * 80)
    
    expires_key_str = str(RAILWAY_EXPIRES_KEY)
    print(f"Expires Key (string): '{expires_key_str}'")
    print(f"Payload: '{RAILWAY_PAYLOAD}'")
    print(f"Secret Length: {len(api_secret)}")
    print()
    
    # Step 1: Derive key
    secret_bytes = api_secret.encode('utf-8')
    expires_key_bytes = expires_key_str.encode('utf-8')
    
    print(f"Step 1: HMAC-SHA256(secret, expires_key)")
    print(f"  secret_bytes length: {len(secret_bytes)}")
    print(f"  expires_key_bytes: {expires_key_bytes}")
    
    derived_key = hmac.new(
        secret_bytes,
        expires_key_bytes,
        hashlib.sha256
    ).hexdigest()
    
    print(f"  Derived Key: {derived_key}")
    print()
    
    # Step 2: Sign payload
    key_bytes = derived_key.encode('utf-8')
    payload_bytes = RAILWAY_PAYLOAD.encode('utf-8')
    
    print(f"Step 2: HMAC-SHA256(derived_key, payload)")
    print(f"  key_bytes length: {len(key_bytes)}")
    print(f"  payload_bytes: {payload_bytes}")
    print(f"  payload_bytes repr: {repr(payload_bytes)}")
    
    signature = hmac.new(
        key_bytes,
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    print(f"  Generated Signature: {signature}")
    print()
    
    # Compare
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Generated: {signature}")
    print(f"Railway:  {RAILWAY_SIGNATURE}")
    print()
    
    if signature == RAILWAY_SIGNATURE:
        print("✅ SIGNATURES MATCH!")
        print()
        print("CONCLUSION:")
        print("  ✅ Signature generation is CORRECT")
        print("  ✅ Code is CORRECT")
        print("  ❌ Issue is EXTERNAL (Coinstore API key configuration)")
        print()
        print("Possible causes:")
        print("  1. IP whitelist (but you tried both IPs)")
        print("  2. API key permissions (but you confirmed Read/Trade enabled)")
        print("  3. Coinstore API issue or account status")
        print("  4. Something else Coinstore requires that we're missing")
    else:
        print("❌ SIGNATURES DO NOT MATCH!")
        print()
        print("This means:")
        print("  ❌ Secret in database doesn't match Coinstore")
        print("  OR")
        print("  ❌ There's an encoding/corruption issue")
        print()
        print("Next steps:")
        print("  1. Verify secret in database matches Coinstore dashboard")
        print("  2. Check if secret has any hidden characters")
        print("  3. Re-enter API secret in database")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
