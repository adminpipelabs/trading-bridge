#!/usr/bin/env python3
"""
Update Coinstore API Key to Match Railway IP
Updates the database to use the "second key" (f2f0cb9e70c135e2cddfadc45c818cff)
which is whitelisted for Railway's current IP (54.205.35.75)
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.security import encrypt_credential, decrypt_credential

print("=" * 80)
print("UPDATE COINSTORE API KEY TO MATCH RAILWAY IP")
print("=" * 80)

# New key details (from screenshot)
NEW_API_KEY = "f2f0cb9e70c135e2cddfadc45c818cff"
NEW_IP = "54.205.35.75"

# Old key (currently in database)
OLD_API_KEY = "42b5c7c40bf625e7fcffd16a654b6ed0"
OLD_IP = "3.222.129.4"

print(f"\nCurrent Key (Pipe Labs):")
print(f"  API Key: {OLD_API_KEY}")
print(f"  IP: {OLD_IP}")
print(f"\nNew Key (second key):")
print(f"  API Key: {NEW_API_KEY}")
print(f"  IP: {NEW_IP}")
print()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("   Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Find current Coinstore credentials
    print("Checking current Coinstore credentials...")
    current_creds = db.execute(text("""
        SELECT client_id, api_key_encrypted, api_secret_encrypted
        FROM exchange_credentials
        WHERE exchange = 'coinstore'
    """)).fetchall()
    
    if not current_creds:
        print("❌ No Coinstore credentials found in database")
        sys.exit(1)
    
    print(f"✅ Found {len(current_creds)} Coinstore credential(s)")
    print()
    
    # Verify current key matches old key
    for cred in current_creds:
        api_key = decrypt_credential(cred.api_key_encrypted).strip()
        print(f"Client: {cred.client_id}")
        print(f"  Current API Key: {api_key[:10]}...{api_key[-5:]}")
        
        if api_key == OLD_API_KEY:
            print(f"  ✅ Matches 'Pipe Labs' key")
        else:
            print(f"  ⚠️  Different key found")
    
    print()
    print("=" * 80)
    print("⚠️  ACTION REQUIRED")
    print("=" * 80)
    print()
    print("To update to the new key, you need to:")
    print()
    print("1. Get the API SECRET for the new key:")
    print(f"   Key: {NEW_API_KEY}")
    print(f"   IP: {NEW_IP}")
    print()
    print("2. Update via API endpoint:")
    print("   POST /api/cex/credentials")
    print("   Body: {")
    print(f'     "exchange": "coinstore",')
    print(f'     "api_key": "{NEW_API_KEY}",')
    print(f'     "api_secret": "<SECRET_FOR_NEW_KEY>"')
    print("   }")
    print()
    print("3. OR update directly in database (if you have secret):")
    print("   UPDATE exchange_credentials")
    print(f"   SET api_key_encrypted = encrypt('{NEW_API_KEY}'),")
    print("       api_secret_encrypted = encrypt('<SECRET>')")
    print("   WHERE exchange = 'coinstore'")
    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()
    print("Option 1: Update via UI/Frontend")
    print("  - Go to your frontend")
    print("  - Update Coinstore API credentials")
    print(f"  - Use new key: {NEW_API_KEY}")
    print("  - Enter the secret for this key")
    print()
    print("Option 2: Keep both keys, update 'Pipe Labs' key IP")
    print("  - Edit 'Pipe Labs' key in Coinstore dashboard")
    print("  - Add BOTH IPs to whitelist:")
    print(f"    - {OLD_IP}")
    print(f"    - {NEW_IP}")
    print("  - This way both keys work")
    print()
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
