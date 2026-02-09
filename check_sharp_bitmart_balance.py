#!/usr/bin/env python3
"""
Check BitMart balance for Sharp Foundation.
Finds Sharp's account and checks balance using stored API keys.
"""
import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def check_sharp_bitmart_balance():
    """Check BitMart balance for Sharp Foundation."""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        print("   Set it from Railway or use: export DATABASE_URL='postgresql://...'")
        return
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find Sharp's client
        print("🔍 Looking for Sharp Foundation client...")
        client = await conn.fetchrow("""
            SELECT id, name, account_identifier 
            FROM clients 
            WHERE name ILIKE '%sharp%' OR account_identifier ILIKE '%sharp%'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        if not client:
            print("❌ Sharp Foundation client not found")
            print("\nAvailable clients:")
            all_clients = await conn.fetch("SELECT name, account_identifier FROM clients LIMIT 10")
            for c in all_clients:
                print(f"  - {c['name']} ({c['account_identifier']})")
            return
        
        print(f"\n✅ Found: {client['name']} ({client['account_identifier']})")
        print(f"   Client ID: {client['id']}")
        
        # Check connectors
        print("\n🔍 Checking BitMart connector...")
        connectors = await conn.fetch("""
            SELECT name, api_key, api_secret, memo, created_at
            FROM connectors
            WHERE client_id = $1
        """, client['id'])
        
        if not connectors:
            print("\n❌ NO CONNECTORS FOUND")
            print("   BitMart API keys are not stored in database")
            print("   Need to add via admin UI or API endpoint")
            return
        
        print(f"\n✅ Found {len(connectors)} connector(s):")
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
        print("\n🔍 Connecting to BitMart API...")
        try:
            import ccxt.async_support as ccxt
            
            exchange_params = {
                'apiKey': bitmart_connector['api_key'],
                'secret': bitmart_connector['api_secret'],
                'enableRateLimit': True,
            }
            
            if bitmart_connector['memo']:
                exchange_params['uid'] = bitmart_connector['memo']
                print(f"   Using UID/Memo: {bitmart_connector['memo']}")
            
            exchange = ccxt.bitmart(exchange_params)
            
            # Load markets
            print("   Loading markets...")
            await exchange.load_markets()
            print("✅ Markets loaded successfully")
            
            # Fetch balance
            print("\n💰 Fetching balance...")
            balance = await exchange.fetch_balance()
            
            # Show non-zero balances
            print("\n" + "="*70)
            print("💰 BITMART BALANCES FOR SHARP FOUNDATION")
            print("="*70)
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
                print(f"\n{'Currency':<12} {'Total':>20} {'Free':>20} {'Used':>20}")
                print("-" * 70)
                for bal in sorted(non_zero, key=lambda x: x['total'], reverse=True):
                    print(f"{bal['currency']:<12} {bal['total']:>20,.8f} {bal['free']:>20,.8f} {bal['used']:>20,.8f}")
                print("="*70)
                print(f"\n✅ Found {len(non_zero)} token(s) with balance")
                
                # Check specifically for SHARP and USDT
                sharp_balance = next((b for b in non_zero if b['currency'] == 'SHARP'), None)
                usdt_balance = next((b for b in non_zero if b['currency'] == 'USDT'), None)
                
                if sharp_balance:
                    print(f"\n📊 SHARP Balance: {sharp_balance['total']:,.8f} SHARP")
                    print(f"   Free: {sharp_balance['free']:,.8f} SHARP")
                else:
                    print("\n⚠️  SHARP balance: 0")
                
                if usdt_balance:
                    print(f"\n💵 USDT Balance: ${usdt_balance['total']:,.2f} USDT")
                    print(f"   Free: ${usdt_balance['free']:,.2f} USDT")
                else:
                    print("\n⚠️  USDT balance: $0")
            else:
                print("\n⚠️  All balances are zero")
                print("="*70)
            
            await exchange.close()
            
        except Exception as e:
            print(f"\n❌ Failed to fetch balance: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_sharp_bitmart_balance())
