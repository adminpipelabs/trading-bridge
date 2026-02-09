#!/usr/bin/env python3
"""
Check which bot(s) are associated with a wallet address.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

# Fix Railway postgres:// format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

wallet_address = "4vGfe6sSdXiNYL9SjuHqt3xaubPcSvyPzVBcX2r1VoE5"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print(f"🔍 Searching for bots associated with wallet: {wallet_address}\n")
    
    # Check bot_wallets table
    print("1. Checking bot_wallets table...")
    bot_wallets = db.execute(text("""
        SELECT bw.bot_id, bw.wallet_address, bw.created_at, b.name, b.bot_type, b.status, b.account
        FROM bot_wallets bw
        LEFT JOIN bots b ON bw.bot_id = b.id
        WHERE bw.wallet_address = :wallet_address
    """), {"wallet_address": wallet_address}).fetchall()
    
    if bot_wallets:
        print(f"   ✅ Found {len(bot_wallets)} bot(s) in bot_wallets:")
        for row in bot_wallets:
            print(f"      - Bot ID: {row[0]}")
            print(f"        Name: {row[3]}")
            print(f"        Type: {row[4]}")
            print(f"        Status: {row[5]}")
            print(f"        Account: {row[6]}")
            print(f"        Created: {row[2]}")
            print()
    else:
        print("   ❌ No bots found in bot_wallets table")
    
    # Check trading_keys table
    print("2. Checking trading_keys table...")
    trading_keys = db.execute(text("""
        SELECT tk.client_id, tk.wallet_address, tk.added_by, tk.created_at, c.name as client_name, c.account_identifier
        FROM trading_keys tk
        LEFT JOIN clients c ON tk.client_id = c.id
        WHERE tk.wallet_address = :wallet_address
    """), {"wallet_address": wallet_address}).fetchall()
    
    if trading_keys:
        print(f"   ✅ Found {len(trading_keys)} key(s) in trading_keys:")
        for row in trading_keys:
            print(f"      - Client ID: {row[0]}")
            print(f"        Client Name: {row[4]}")
            print(f"        Account: {row[5]}")
            print(f"        Added By: {row[2]}")
            print(f"        Created: {row[3]}")
            print()
    else:
        print("   ❌ No keys found in trading_keys table")
    
    # Check if this wallet is a client login wallet
    print("3. Checking if wallet is a client login wallet...")
    client_wallets = db.execute(text("""
        SELECT w.client_id, w.address, w.chain, c.name, c.account_identifier
        FROM wallets w
        LEFT JOIN clients c ON w.client_id = c.id
        WHERE w.address = :wallet_address
    """), {"wallet_address": wallet_address}).fetchall()
    
    if client_wallets:
        print(f"   ✅ Found {len(client_wallets)} client wallet(s):")
        for row in client_wallets:
            print(f"      - Client ID: {row[0]}")
            print(f"        Client Name: {row[3]}")
            print(f"        Account: {row[4]}")
            print(f"        Chain: {row[2]}")
            print()
    else:
        print("   ❌ Not found as client login wallet")
    
    # Find all bots for clients that have this wallet
    if trading_keys or client_wallets:
        print("4. Finding all bots for associated clients...")
        client_ids = set()
        if trading_keys:
            client_ids.update([row[0] for row in trading_keys])
        if client_wallets:
            client_ids.update([row[0] for row in client_wallets])
        
        if client_ids:
            placeholders = ','.join([f"'{cid}'" for cid in client_ids])
            bots = db.execute(text(f"""
                SELECT b.id, b.name, b.bot_type, b.status, b.account, b.created_at
                FROM bots b
                WHERE b.client_id IN ({placeholders})
                ORDER BY b.created_at DESC
            """)).fetchall()
            
            if bots:
                print(f"   ✅ Found {len(bots)} bot(s) for these clients:")
                for row in bots:
                    print(f"      - Bot ID: {row[0]}")
                    print(f"        Name: {row[1]}")
                    print(f"        Type: {row[2]}")
                    print(f"        Status: {row[3]}")
                    print(f"        Account: {row[4]}")
                    print(f"        Created: {row[5]}")
                    print()
            else:
                print("   ❌ No bots found for these clients")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
