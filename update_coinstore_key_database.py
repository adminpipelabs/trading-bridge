#!/usr/bin/env python3
"""
Update Coinstore API Key in Database
Updates exchange_credentials table to use the new key that matches Railway IP.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.security import encrypt_credential, decrypt_credential

print("=" * 80)
print("UPDATE COINSTORE API KEY IN DATABASE")
print("=" * 80)

# New key (matches Railway IP 54.205.35.75)
NEW_API_KEY = "f2f0cb9e70c135e2cddfadc45c818cff"

print(f"\nNew API Key: {NEW_API_KEY}")
print(f"IP Whitelist: 54.205.35.75 (matches Railway)")
print()

# Get secret from user
print("⚠️  ACTION REQUIRED:")
print("   You need to provide the API SECRET for the new key.")
print(f"   Key: {NEW_API_KEY}")
print()
api_secret = input("Enter API Secret for the new key (or press Enter to skip): ").strip()

if not api_secret:
    print("\n❌ Secret not provided. Exiting.")
    print("\nTo update manually:")
    print("1. Get secret from Coinstore dashboard for key: f2f0cb9e70c135e2cddfadc45c818cff")
    print("2. Update via frontend/UI or use this script again with the secret")
    sys.exit(0)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("\n❌ DATABASE_URL not set")
    print("   Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Find current Coinstore credentials
    print("\nChecking current Coinstore credentials...")
    current_creds = db.execute(text("""
        SELECT client_id, api_key_encrypted, api_secret_encrypted
        FROM exchange_credentials
        WHERE exchange = 'coinstore'
    """)).fetchall()
    
    if not current_creds:
        print("❌ No Coinstore credentials found in database")
        print("   Creating new entry...")
        
        # Need client_id - try to find one
        client = db.execute(text("""
            SELECT id FROM clients LIMIT 1
        """)).fetchone()
        
        if not client:
            print("❌ No clients found. Cannot create credentials.")
            sys.exit(1)
        
        client_id = client[0]
        print(f"   Using client_id: {client_id}")
    else:
        client_id = current_creds[0].client_id
        print(f"✅ Found credentials for client: {client_id}")
        
        # Show current key
        old_key = decrypt_credential(current_creds[0].api_key_encrypted).strip()
        print(f"   Current Key: {old_key[:10]}...{old_key[-5:]}")
    
    # Encrypt new credentials
    print("\nEncrypting new credentials...")
    new_key_enc = encrypt_credential(NEW_API_KEY.strip())
    new_secret_enc = encrypt_credential(api_secret.strip())
    
    # Update database
    print("\nUpdating database...")
    from datetime import datetime, timezone
    
    db.execute(text("""
        INSERT INTO exchange_credentials 
            (client_id, exchange, api_key_encrypted, api_secret_encrypted, updated_at)
        VALUES (:client_id, :exchange, :api_key, :api_secret, :updated_at)
        ON CONFLICT (client_id, exchange)
        DO UPDATE SET 
            api_key_encrypted = :api_key,
            api_secret_encrypted = :api_secret,
            updated_at = :updated_at
    """), {
        "client_id": client_id,
        "exchange": "coinstore",
        "api_key": new_key_enc,
        "api_secret": new_secret_enc,
        "updated_at": datetime.now(timezone.utc)
    })
    
    db.commit()
    
    print("✅ Database updated successfully!")
    print(f"\nNew API Key: {NEW_API_KEY}")
    print("IP Whitelist: 54.205.35.75")
    print("\nNext steps:")
    print("1. Wait 1-2 minutes for changes to propagate")
    print("2. Refresh dashboard")
    print("3. Check Railway logs - balances should appear")
    
    db.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
