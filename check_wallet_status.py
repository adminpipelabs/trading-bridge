#!/usr/bin/env python3
"""
Check wallet status by wallet address.
Shows if wallet is in bot_wallets and trading_keys tables.
"""
import os
import sys
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def check_by_wallet_address(wallet_address: str):
    """Check wallet status by wallet address."""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        wallet_lower = wallet_address.lower()
        
        print("\n" + "="*60)
        print(f"CHECKING WALLET: {wallet_address}")
        print("="*60)
        
        # Find client
        client = await conn.fetchrow("""
            SELECT c.id, c.name, c.account_identifier
            FROM clients c
            JOIN wallets w ON w.client_id = c.id
            WHERE LOWER(w.address) = $1
        """, wallet_lower)
        
        if not client:
            print("❌ No client found with this wallet address")
            return
        
        print(f"\n✅ Client Found:")
        print(f"   Client ID: {client['id']}")
        print(f"   Name: {client['name']}")
        print(f"   Account: {client['account_identifier']}")
        
        # Check bot_wallets
        bot_wallets = await conn.fetch("""
            SELECT 
                bw.bot_id,
                b.name as bot_name,
                b.bot_type,
                b.status
            FROM bot_wallets bw
            JOIN bots b ON b.id = bw.bot_id
            WHERE LOWER(bw.wallet_address) = $1
        """, wallet_lower)
        
        print(f"\n📦 Bot Wallets (bot_wallets table):")
        if bot_wallets:
            for bw in bot_wallets:
                print(f"   ✅ Bot: {bw['bot_name']} ({bw['bot_id']})")
                print(f"      Type: {bw['bot_type']}, Status: {bw['status']}")
        else:
            print("   ❌ No wallets found in bot_wallets table")
        
        # Check trading_keys
        trading_key = await conn.fetchrow("""
            SELECT 
                client_id,
                chain,
                wallet_address,
                added_by,
                created_at
            FROM trading_keys
            WHERE LOWER(wallet_address) = $1
        """, wallet_lower)
        
        print(f"\n🔑 Trading Keys (trading_keys table):")
        if trading_key:
            print(f"   ✅ Key exists")
            print(f"      Chain: {trading_key['chain']}")
            print(f"      Added by: {trading_key['added_by']}")
            print(f"      Created: {trading_key['created_at']}")
        else:
            print("   ❌ No key found in trading_keys table")
        
        # Diagnosis
        print(f"\n" + "="*60)
        print("DIAGNOSIS:")
        print("="*60)
        
        if bot_wallets and trading_key:
            print("✅ STATUS: OK")
            print("   Wallet is in both tables")
            print("   Client dashboard should show 'Start Bot' button")
        elif bot_wallets and not trading_key:
            print("⚠️  ISSUE FOUND:")
            print("   Wallet is in bot_wallets but NOT in trading_keys")
            print("   This causes 'Connect Wallet' message to show")
            print()
            print("💡 SOLUTION:")
            print(f"   Run: python fix_missing_trading_keys.py {client['id']}")
        elif not bot_wallets and trading_key:
            print("⚠️  ISSUE:")
            print("   Wallet is in trading_keys but NOT in bot_wallets")
            print("   Bot cannot execute trades")
        else:
            print("❌ ISSUE:")
            print("   Wallet not found in either table")
            print("   Need to add wallet to bot")
        
        print("="*60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python check_wallet_status.py <wallet_address>")
        print()
        print("Example:")
        print("  python check_wallet_status.py 4vGfe6sSdXiNYL9SjuHqt3xaubPcSvyPzVBcX2r1VoE5")
        sys.exit(1)
    
    wallet_address = sys.argv[1]
    asyncio.run(check_by_wallet_address(wallet_address))
