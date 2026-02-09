#!/usr/bin/env python3
"""
URGENT: Update Coinstore Key to Match Railway IP
This script updates the database to use the "second key" (f2f0cb9e70c135e2cddfadc45c818cff)
which is whitelisted for Railway's current IP (54.205.35.75)
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.security import encrypt_credential, decrypt_credential
from datetime import datetime, timezone

# New key from screenshot
NEW_API_KEY = "f2f0cb9e70c135e2cddfadc45c818cff"

print("=" * 80)
print("UPDATE COINSTORE KEY TO MATCH RAILWAY IP")
print("=" * 80)
print(f"\nNew API Key: {NEW_API_KEY}")
print(f"IP Whitelist: 54.205.35.75 (matches Railway)")
print()

# Get secret from environment or user input
api_secret = os.getenv("COINSTORE_NEW_SECRET")
if not api_secret:
    print("⚠️  COINSTORE_NEW_SECRET not set in environment")
    print("   Enter the API SECRET for the new key:")
    print(f"   Key: {NEW_API_KEY}")
    api_secret = input("\nSecret: ").strip()

if not api_secret:
    print("\n❌ Secret required. Exiting.")
    print("\nTo run with secret:")
    print("   export COINSTORE_NEW_SECRET='your_secret'")
    print("   python3 UPDATE_COINSTORE_KEY_NOW.py")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("\n❌ DATABASE_URL not set")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Find Coinstore credentials
    print("\nFinding Coinstore credentials...")
    creds = db.execute(text("""
        SELECT client_id, api_key_encrypted
        FROM exchange_credentials
        WHERE exchange = 'coinstore'
    """)).fetchall()
    
    if not creds:
        print("❌ No Coinstore credentials found")
        print("   Need to create new entry - which client_id?")
        client_id = input("Client ID: ").strip()
        if not client_id:
            print("❌ Client ID required")
            sys.exit(1)
    else:
        client_id = creds[0].client_id
        old_key = decrypt_credential(creds[0].api_key_encrypted).strip()
        print(f"✅ Found credentials for client: {client_id}")
        print(f"   Current Key: {old_key[:10]}...{old_key[-5:]}")
        
        if old_key == NEW_API_KEY:
            print("\n✅ Database already has the new key!")
            print("   No update needed.")
            sys.exit(0)
    
    # Encrypt and update
    print(f"\nUpdating to new key: {NEW_API_KEY[:10]}...{NEW_API_KEY[-5:]}")
    new_key_enc = encrypt_credential(NEW_API_KEY.strip())
    new_secret_enc = encrypt_credential(api_secret.strip())
    
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
    
    print("\n✅ DATABASE UPDATED SUCCESSFULLY!")
    print(f"\nNew Key: {NEW_API_KEY}")
    print("IP: 54.205.35.75 (matches Railway)")
    print("\nNext:")
    print("1. Wait 1-2 minutes")
    print("2. Refresh dashboard")
    print("3. Balances should appear!")
    
    db.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
