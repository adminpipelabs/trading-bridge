#!/usr/bin/env python3
"""
Fix missing trading_keys entries for bots that have wallets in bot_wallets.
Copies wallet info from bot_wallets to trading_keys table.
"""
import os
import sys
import asyncpg
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def fix_missing_trading_keys(client_id: str):
    """Copy wallets from bot_wallets to trading_keys for a client."""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Check if trading_keys table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'trading_keys'
            )
        """)
        
        if not table_exists:
            print("❌ trading_keys table doesn't exist")
            print("   Run migration: migrations/add_cex_volume_bot.sql")
            return
        
        # Get client info
        client = await conn.fetchrow("""
            SELECT id, name, account_identifier FROM clients WHERE id = $1
        """, client_id)
        
        if not client:
            print(f"❌ Client {client_id} not found")
            return
        
        print(f"\nClient: {client['name']} ({client['account_identifier']})")
        
        # Get all bot_wallets for this client's bots
        bot_wallets = await conn.fetch("""
            SELECT DISTINCT
                bw.wallet_address,
                bw.encrypted_private_key,
                b.chain,
                b.bot_type
            FROM bot_wallets bw
            JOIN bots b ON b.id = bw.bot_id
            WHERE b.client_id = $1
            ORDER BY bw.wallet_address
        """, client_id)
        
        if not bot_wallets:
            print("❌ No bot_wallets found for this client")
            return
        
        print(f"\nFound {len(bot_wallets)} wallet(s) in bot_wallets:")
        for bw in bot_wallets:
            print(f"  - {bw['wallet_address']} (chain: {bw['chain'] or 'solana'})")
        
        # Check which ones are missing from trading_keys
        missing = []
        for bw in bot_wallets:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM trading_keys 
                    WHERE client_id = $1 AND wallet_address = $2
                )
            """, client_id, bw['wallet_address'])
            
            if not exists:
                missing.append(bw)
        
        if not missing:
            print("\n✅ All wallets already in trading_keys table")
            return
        
        print(f"\n⚠️  Found {len(missing)} wallet(s) missing from trading_keys:")
        for bw in missing:
            print(f"  - {bw['wallet_address']}")
        
        # Insert missing wallets
        print("\n📝 Copying wallets to trading_keys...")
        for bw in missing:
            chain = bw['chain'] or 'solana'
            try:
                await conn.execute("""
                    INSERT INTO trading_keys 
                        (client_id, encrypted_key, chain, wallet_address, added_by, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, 'admin', NOW(), NOW())
                    ON CONFLICT (client_id) DO UPDATE SET
                        encrypted_key = EXCLUDED.encrypted_key,
                        wallet_address = EXCLUDED.wallet_address,
                        chain = EXCLUDED.chain,
                        updated_at = NOW()
                """, client_id, bw['encrypted_private_key'], chain, bw['wallet_address'])
                print(f"  ✅ Added {bw['wallet_address']}")
            except Exception as e:
                print(f"  ❌ Failed to add {bw['wallet_address']}: {e}")
        
        print("\n✅ Done! Client dashboard should now show 'Start Bot' button")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_missing_trading_keys.py <client_id>")
        print()
        print("Example:")
        print("  python fix_missing_trading_keys.py abc123-def456-...")
        sys.exit(1)
    
    client_id = sys.argv[1]
    asyncio.run(fix_missing_trading_keys(client_id))
