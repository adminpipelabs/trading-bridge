#!/usr/bin/env python3
"""
Check if a bot has wallets properly stored in both bot_wallets and trading_keys tables.
Useful for debugging "Connect Wallet" issues.
"""
import os
import sys
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def check_bot_wallet_status(bot_id: str = None, client_id: str = None, account: str = None):
    """Check wallet status for a bot or client."""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Build query
        if bot_id:
            query = """
                SELECT 
                    b.id as bot_id,
                    b.name as bot_name,
                    b.account,
                    b.client_id,
                    c.name as client_name,
                    COUNT(DISTINCT bw.id) as bot_wallets_count,
                    COUNT(DISTINCT tk.id) as trading_keys_count,
                    STRING_AGG(DISTINCT bw.wallet_address, ', ') as bot_wallet_addresses,
                    STRING_AGG(DISTINCT tk.wallet_address, ', ') as trading_key_addresses
                FROM bots b
                JOIN clients c ON c.id = b.client_id
                LEFT JOIN bot_wallets bw ON bw.bot_id = b.id
                LEFT JOIN trading_keys tk ON tk.client_id = b.client_id
                WHERE b.id = $1
                GROUP BY b.id, b.name, b.account, b.client_id, c.name
            """
            result = await conn.fetchrow(query, bot_id)
        elif client_id:
            query = """
                SELECT 
                    c.id as client_id,
                    c.name as client_name,
                    c.account_identifier,
                    COUNT(DISTINCT bw.id) as bot_wallets_count,
                    COUNT(DISTINCT tk.id) as trading_keys_count,
                    STRING_AGG(DISTINCT bw.wallet_address, ', ') as bot_wallet_addresses,
                    STRING_AGG(DISTINCT tk.wallet_address, ', ') as trading_key_addresses
                FROM clients c
                LEFT JOIN bots b ON b.client_id = c.id
                LEFT JOIN bot_wallets bw ON bw.bot_id = b.id
                LEFT JOIN trading_keys tk ON tk.client_id = c.id
                WHERE c.id = $1
                GROUP BY c.id, c.name, c.account_identifier
            """
            result = await conn.fetchrow(query, client_id)
        elif account:
            query = """
                SELECT 
                    c.id as client_id,
                    c.name as client_name,
                    c.account_identifier,
                    COUNT(DISTINCT bw.id) as bot_wallets_count,
                    COUNT(DISTINCT tk.id) as trading_keys_count,
                    STRING_AGG(DISTINCT bw.wallet_address, ', ') as bot_wallet_addresses,
                    STRING_AGG(DISTINCT tk.wallet_address, ', ') as trading_key_addresses
                FROM clients c
                LEFT JOIN bots b ON b.client_id = c.id
                LEFT JOIN bot_wallets bw ON bw.bot_id = b.id
                LEFT JOIN trading_keys tk ON tk.client_id = c.id
                WHERE c.account_identifier = $1
                GROUP BY c.id, c.name, c.account_identifier
            """
            result = await conn.fetchrow(query, account)
        else:
            print("❌ Must provide bot_id, client_id, or account")
            return
        
        if not result:
            print("❌ No results found")
            return
        
        print("\n" + "="*60)
        print("WALLET STATUS CHECK")
        print("="*60)
        
        if 'bot_id' in result:
            print(f"Bot ID: {result['bot_id']}")
            print(f"Bot Name: {result['bot_name']}")
        print(f"Client ID: {result.get('client_id', 'N/A')}")
        print(f"Client Name: {result.get('client_name', 'N/A')}")
        print(f"Account: {result.get('account') or result.get('account_identifier', 'N/A')}")
        print()
        print(f"Bot Wallets (bot_wallets table): {result['bot_wallets_count']}")
        print(f"  Addresses: {result['bot_wallet_addresses'] or 'None'}")
        print()
        print(f"Trading Keys (trading_keys table): {result['trading_keys_count']}")
        print(f"  Addresses: {result['trading_key_addresses'] or 'None'}")
        print()
        
        # Diagnosis
        if result['bot_wallets_count'] > 0 and result['trading_keys_count'] == 0:
            print("⚠️  ISSUE FOUND:")
            print("   Bot has wallets in bot_wallets but NOT in trading_keys")
            print("   This will cause 'Connect Wallet' message to show")
            print()
            print("💡 SOLUTION:")
            print("   Copy wallet from bot_wallets to trading_keys table")
            print("   Or use the fix script: fix_missing_trading_keys.py")
        elif result['bot_wallets_count'] == 0:
            print("⚠️  ISSUE:")
            print("   Bot has NO wallets in bot_wallets table")
            print("   Bot cannot execute trades without wallets")
        elif result['bot_wallets_count'] > 0 and result['trading_keys_count'] > 0:
            print("✅ STATUS: OK")
            print("   Bot has wallets in both tables")
            print("   Client dashboard should show 'Start Bot' button")
        
        print("="*60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python check_bot_wallet_status.py --bot-id <bot_id>")
        print("  python check_bot_wallet_status.py --client-id <client_id>")
        print("  python check_bot_wallet_status.py --account <account_identifier>")
        sys.exit(1)
    
    arg_type = sys.argv[1]
    arg_value = sys.argv[2] if len(sys.argv) > 2 else None
    
    if arg_type == "--bot-id":
        asyncio.run(check_bot_wallet_status(bot_id=arg_value))
    elif arg_type == "--client-id":
        asyncio.run(check_bot_wallet_status(client_id=arg_value))
    elif arg_type == "--account":
        asyncio.run(check_bot_wallet_status(account=arg_value))
    else:
        print("Invalid argument. Use --bot-id, --client-id, or --account")
        sys.exit(1)
