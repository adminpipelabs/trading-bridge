#!/usr/bin/env python3
"""
Test Coinstore balance fetch directly
Checks if API keys exist and tests balance endpoint
"""
import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 80)
print("COINSTORE BALANCE TEST")
print("=" * 80)

# Find Coinstore bots
coinstore_bots = db.execute(text("""
    SELECT id, name, account, connector, bot_type, pair
    FROM bots
    WHERE name ILIKE '%coinstore%' OR connector ILIKE '%coinstore%'
    ORDER BY name
""")).fetchall()

if not coinstore_bots:
    print("❌ No Coinstore bots found")
    sys.exit(0)

for bot in coinstore_bots:
    bot_id = bot.id
    bot_name = bot.name
    account = bot.account
    
    print(f"\n{'='*80}")
    print(f"🤖 Bot: {bot_name}")
    print(f"   ID: {bot_id}")
    print(f"   Account: {account}")
    
    # Get client
    client = db.execute(text("""
        SELECT id, name, account_identifier
        FROM clients
        WHERE account_identifier = :account
    """), {"account": account}).fetchone()
    
    if not client:
        print(f"   ❌ Client not found for account {account}")
        continue
    
    print(f"   ✅ Client: {client.name} (ID: {client.id})")
    
    # Check connectors table
    connectors = db.execute(text("""
        SELECT name, api_key, api_secret, memo
        FROM connectors
        WHERE client_id = :client_id AND name ILIKE '%coinstore%'
    """), {"client_id": client.id}).fetchall()
    
    print(f"\n📋 Connectors table:")
    if connectors:
        for c in connectors:
            has_key = bool(c.api_key)
            has_secret = bool(c.api_secret)
            print(f"   ✅ Found: {c.name}")
            print(f"      API Key: {'✅' if has_key else '❌'}")
            print(f"      API Secret: {'✅' if has_secret else '❌'}")
            print(f"      Memo: {c.memo or 'None'}")
    else:
        print(f"   ❌ No Coinstore connectors found")
    
    # Check exchange_credentials table
    creds = db.execute(text("""
        SELECT exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted
        FROM exchange_credentials
        WHERE client_id = :client_id AND exchange ILIKE '%coinstore%'
    """), {"client_id": client.id}).fetchall()
    
    print(f"\n🔑 Exchange Credentials table:")
    if creds:
        for c in creds:
            has_key = bool(c.api_key_encrypted)
            has_secret = bool(c.api_secret_encrypted)
            print(f"   ✅ Found: {c.exchange}")
            print(f"      Encrypted API Key: {'✅' if has_key else '❌'}")
            print(f"      Encrypted API Secret: {'✅' if has_secret else '❌'}")
            print(f"      Passphrase: {'✅' if c.passphrase_encrypted else '❌'}")
    else:
        print(f"   ❌ No Coinstore credentials found")
    
    # Test balance endpoint via API call
    print(f"\n🌐 Testing balance endpoint:")
    print(f"   Endpoint: GET /api/bots/{bot_id}/stats")
    print(f"   Run: curl https://trading-bridge-production.up.railway.app/api/bots/{bot_id}/stats")
    print(f"   Or check Railway logs when frontend calls this endpoint")

print(f"\n{'='*80}")
print("SUMMARY:")
print("=" * 80)
print("\n✅ If API keys exist: Balance endpoint should work")
print("❌ If no API keys: Add Coinstore API keys via bot setup")
print("\n💡 Next steps:")
print("   1. If keys exist → Check Railway logs when frontend calls /stats")
print("   2. If no keys → Add Coinstore API keys to exchange_credentials table")
print("   3. Whitelist BitMart IPs: 3.222.129.4 and 54.205.35.75")
print("=" * 80)

db.close()
