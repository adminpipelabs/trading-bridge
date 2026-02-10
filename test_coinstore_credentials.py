#!/usr/bin/env python3
"""
Test Coinstore credentials from database.
Run this on Hetzner to verify what credentials we're using.
"""
import os
import sys
from sqlalchemy import create_engine, text
from cryptography.fernet import Fernet

DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not DATABASE_URL or not ENCRYPTION_KEY:
    print("❌ DATABASE_URL or ENCRYPTION_KEY not set")
    sys.exit(1)

print("=" * 80)
print("COINSTORE CREDENTIALS CHECK")
print("=" * 80)

fernet = Fernet(ENCRYPTION_KEY.encode())
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get Coinstore credentials
    result = conn.execute(text("""
        SELECT 
            ec.api_key_encrypted, 
            ec.api_secret_encrypted,
            b.id as bot_id,
            b.name as bot_name,
            cl.account_identifier
        FROM exchange_credentials ec
        JOIN clients cl ON cl.id = ec.client_id
        JOIN bots b ON b.account = cl.account_identifier
        WHERE ec.exchange = 'coinstore' 
          AND b.connector = 'coinstore'
          AND b.status = 'running'
        ORDER BY b.name LIKE '%Coinstore%' DESC
        LIMIT 1
    """))
    
    row = result.fetchone()
    if not row:
        print("❌ No Coinstore credentials found")
        sys.exit(1)
    
    api_key_encrypted = row[0]
    api_secret_encrypted = row[1]
    bot_id = row[2]
    bot_name = row[3]
    account = row[4]
    
    # Decrypt
    api_key = fernet.decrypt(api_key_encrypted.encode()).decode()
    api_secret = fernet.decrypt(api_secret_encrypted.encode()).decode()

print(f"\n📋 Bot Info:")
print(f"   Bot ID: {bot_id}")
print(f"   Bot Name: {bot_name}")
print(f"   Account: {account}")

print(f"\n🔑 API Credentials:")
print(f"   API Key: {api_key}")
print(f"   API Key (first 10): {api_key[:10]}...{api_key[-5:]}")
print(f"   API Secret (first 10): {api_secret[:10]}...{api_secret[-5:]}")
print(f"   API Key Length: {len(api_key)}")
print(f"   API Secret Length: {len(api_secret)}")

print(f"\n🌐 Server IP:")
print(f"   Hetzner IP: 5.161.64.209")
print(f"   (This IP should be whitelisted on Coinstore for this API key)")

print(f"\n✅ Credentials loaded from database")
print(f"\n📝 Next Steps:")
print(f"   1. Log into Coinstore dashboard")
print(f"   2. Find API key: {api_key}")
print(f"   3. Check if IP 5.161.64.209 is whitelisted")
print(f"   4. Verify API secret matches")
print(f"   5. Check API key permissions (Read/Trade enabled)")
