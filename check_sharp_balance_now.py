#!/usr/bin/env python3
"""
Check Sharp's BitMart balance RIGHT NOW using API keys from database.
"""
import os
import sys
import asyncio
import asyncpg
import ccxt.async_support as ccxt

# Get DATABASE_URL from Railway CLI
import subprocess
try:
    result = subprocess.run(['railway', 'variables', '--json'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        import json
        data = json.loads(result.stdout)
        DATABASE_URL = data.get('DATABASE_URL', '')
    else:
        DATABASE_URL = os.getenv("DATABASE_URL", "")
except:
    DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

async def check_balance():
    """Check Sharp's BitMart balance."""
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find Sharp's client
        print("🔍 Finding Sharp's client...")
        client = await conn.fetchrow("""
            SELECT id, name, account_identifier 
            FROM clients 
            WHERE name ILIKE '%sharp%' OR account_identifier ILIKE '%sharp%'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        if not client:
            print("❌ Sharp's client not found")
            return
        
        print(f"✅ Found: {client['name']} ({client['account_identifier']})")
        
        # Get BitMart connector
        print("\n🔍 Getting BitMart API keys...")
        connector = await conn.fetchrow("""
            SELECT api_key, api_secret, memo
            FROM connectors
            WHERE client_id = $1 AND name = 'bitmart'
        """, client['id'])
        
        if not connector:
            print("❌ No BitMart connector found")
            print("   Need to add API keys via admin dashboard")
            return
        
        if not connector['api_key'] or not connector['api_secret']:
            print("❌ BitMart connector incomplete (missing API key or secret)")
            return
        
        print("✅ Found BitMart connector")
        print(f"   API Key: {connector['api_key'][:15]}...")
        print(f"   Memo/UID: {connector['memo'] or 'None'}")
        
        # Connect to BitMart and fetch balance
        print("\n🔍 Connecting to BitMart API...")
        exchange_params = {
            'apiKey': connector['api_key'],
            'secret': connector['api_secret'],
            'enableRateLimit': True,
        }
        
        if connector['memo']:
            exchange_params['uid'] = connector['memo']
            print(f"   Using UID: {connector['memo']}")
        
        exchange = ccxt.bitmart(exchange_params)
        
        try:
            print("   Loading markets...")
            await exchange.load_markets()
            print("✅ Markets loaded")
            
            print("\n💰 Fetching balance...")
            balance = await exchange.fetch_balance()
            
            # Display balances
            print("\n" + "="*70)
            print("💰 BITMART BALANCE FOR SHARP FOUNDATION")
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
                
                # Calculate total USD (USDT = 1:1)
                usdt_bal = next((b for b in non_zero if b['currency'] == 'USDT'), None)
                total_usd = usdt_bal['total'] if usdt_bal else 0
                
                print(f"\n💵 Total USD Value: ${total_usd:,.2f}")
                
                # Check specifically for SHARP and USDT
                sharp_bal = next((b for b in non_zero if b['currency'] == 'SHARP'), None)
                if sharp_bal:
                    print(f"\n📊 SHARP Balance: {sharp_bal['total']:,.8f} SHARP")
                    print(f"   Free: {sharp_bal['free']:,.8f} SHARP")
                else:
                    print("\n⚠️  SHARP balance: 0")
                
                if usdt_bal:
                    print(f"\n💵 USDT Balance: ${usdt_bal['total']:,.2f} USDT")
                    print(f"   Free: ${usdt_bal['free']:,.2f} USDT")
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
    asyncio.run(check_balance())
