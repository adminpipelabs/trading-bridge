#!/usr/bin/env python3
"""
Check BitMart balance for a client.
Tests if API keys are working and balances can be fetched.
"""
import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def check_bitmart_balance(account_identifier: str = None, wallet_address: str = None):
    """Check BitMart balance for a client."""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find client
        if account_identifier:
            client = await conn.fetchrow("""
                SELECT id, name, account_identifier FROM clients WHERE account_identifier = $1
            """, account_identifier)
        elif wallet_address:
            client = await conn.fetchrow("""
                SELECT c.id, c.name, c.account_identifier
                FROM clients c
                JOIN wallets w ON w.client_id = c.id
                WHERE w.address = $1 OR w.address = $2
            """, wallet_address, wallet_address.lower())
        else:
            print("❌ Must provide account_identifier or wallet_address")
            return
        
        if not client:
            print("❌ Client not found")
            return
        
        print(f"\nClient: {client['name']} ({client['account_identifier']})")
        print(f"Client ID: {client['id']}")
        
        # Check connectors
        connectors = await conn.fetch("""
            SELECT name, api_key, api_secret, memo, created_at
            FROM connectors
            WHERE client_id = $1
        """, client['id'])
        
        if not connectors:
            print("\n❌ NO CONNECTORS FOUND")
            print("   BitMart API keys are not stored in database")
            print("   Need to add via admin UI or API")
            return
        
        print(f"\nFound {len(connectors)} connector(s):")
        for conn_row in connectors:
            api_key_preview = conn_row['api_key'][:10] + "..." if conn_row['api_key'] else "None"
            print(f"  - {conn_row['name']}: API Key: {api_key_preview}, Memo: {conn_row['memo'] or 'None'}")
        
        # Test BitMart connection
        bitmart_connector = next((c for c in connectors if c['name'].lower() == 'bitmart'), None)
        if not bitmart_connector:
            print("\n❌ NO BITMART CONNECTOR FOUND")
            print("   Need to add BitMart connector")
            return
        
        if not bitmart_connector['api_key'] or not bitmart_connector['api_secret']:
            print("\n❌ BITMART CONNECTOR INCOMPLETE")
            print("   API key or secret is missing")
            return
        
        # Test fetching balance
        print("\n🔍 Testing BitMart API connection...")
        try:
            import ccxt.async_support as ccxt
            
            exchange = ccxt.bitmart({
                'apiKey': bitmart_connector['api_key'],
                'secret': bitmart_connector['api_secret'],
                'enableRateLimit': True,
            })
            
            if bitmart_connector['memo']:
                exchange.uid = bitmart_connector['memo']
            
            # Load markets
            await exchange.load_markets()
            print("✅ Markets loaded successfully")
            
            # Fetch balance
            balance = await exchange.fetch_balance()
            
            # Show non-zero balances
            print("\n💰 BITMART BALANCES:")
            print("="*60)
            non_zero = []
            for currency, amounts in balance.get("total", {}).items():
                total = float(amounts) if amounts else 0
                if total > 0:
                    free = float(balance.get("free", {}).get(currency, 0))
                    used = float(balance.get("used", {}).get(currency, 0))
                    non_zero.append({
                        "currency": currency,
                        "total": total,
                        "free": free,
                        "used": used
                    })
            
            if non_zero:
                for bal in sorted(non_zero, key=lambda x: x['total'], reverse=True):
                    print(f"  {bal['currency']:10} Total: {bal['total']:>15,.8f}  Free: {bal['free']:>15,.8f}  Used: {bal['used']:>15,.8f}")
                print("="*60)
                print(f"✅ Found {len(non_zero)} token(s) with balance")
            else:
                print("  ⚠️  All balances are zero")
                print("="*60)
            
            await exchange.close()
            
        except Exception as e:
            print(f"❌ Failed to fetch balance: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python check_bitmart_balance.py --account <account_identifier>")
        print("  python check_bitmart_balance.py --wallet <wallet_address>")
        print()
        print("Example:")
        print("  python check_bitmart_balance.py --account client_new_sharp_foundation")
        print("  python check_bitmart_balance.py --wallet 0xB4E3Abb212bfA5D790dc44287073E0b9974885Ae")
        sys.exit(1)
    
    arg_type = sys.argv[1]
    arg_value = sys.argv[2] if len(sys.argv) > 2 else None
    
    if arg_type == "--account":
        asyncio.run(check_bitmart_balance(account_identifier=arg_value))
    elif arg_type == "--wallet":
        asyncio.run(check_bitmart_balance(wallet_address=arg_value))
    else:
        print("Invalid argument. Use --account or --wallet")
        sys.exit(1)
