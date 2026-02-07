#!/usr/bin/env python3
"""
Test BitMart balance fetching for New Sharp Foundation.
Checks API keys, connection, and balance retrieval.
"""
import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def test_new_sharp_balance():
    """Test balance fetching for New Sharp Foundation."""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
    
    # Convert to asyncpg format
    db_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find New Sharp Foundation client
        wallet_address = "0xB4E3Abb212bfA5D790dc44287073E0b9974885Ae"
        
        client = await conn.fetchrow("""
            SELECT c.id, c.name, c.account_identifier
            FROM clients c
            JOIN wallets w ON w.client_id = c.id
            WHERE w.address = $1 OR w.address = $2
        """, wallet_address, wallet_address.lower())
        
        if not client:
            print(f"❌ Client not found for wallet: {wallet_address}")
            return
        
        print("="*70)
        print("TESTING BITMART BALANCE FOR NEW SHARP FOUNDATION")
        print("="*70)
        print(f"Client ID: {client['id']}")
        print(f"Client Name: {client['name']}")
        print(f"Account: {client['account_identifier']}")
        print(f"Wallet: {wallet_address}")
        print()
        
        # Check connectors
        connectors = await conn.fetch("""
            SELECT name, api_key, api_secret, memo, created_at
            FROM connectors
            WHERE client_id = $1
        """, client['id'])
        
        if not connectors:
            print("❌ NO CONNECTORS FOUND")
            print("   BitMart API keys are not stored in database")
            print("   Need to add via admin UI")
            return
        
        print(f"✅ Found {len(connectors)} connector(s):")
        for conn_row in connectors:
            api_key_preview = conn_row['api_key'][:15] + "..." if conn_row['api_key'] and len(conn_row['api_key']) > 15 else (conn_row['api_key'] or "None")
            memo_display = conn_row['memo'] or "None"
            print(f"  - {conn_row['name']}:")
            print(f"      API Key: {api_key_preview}")
            print(f"      Memo: {memo_display}")
            print(f"      Created: {conn_row['created_at']}")
        
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
        
        print("\n" + "="*70)
        print("TESTING BITMART API CONNECTION")
        print("="*70)
        
        try:
            import ccxt.async_support as ccxt
            
            # Create exchange instance
            exchange_config = {
                'apiKey': bitmart_connector['api_key'],
                'secret': bitmart_connector['api_secret'],
                'enableRateLimit': True,
            }
            
            if bitmart_connector['memo']:
                exchange_config['uid'] = bitmart_connector['memo']
            
            exchange = ccxt.bitmart(exchange_config)
            
            # Test 1: Load markets
            print("\n1️⃣  Testing: Load markets...")
            try:
                markets = await exchange.load_markets()
                print(f"   ✅ Markets loaded: {len(markets)} trading pairs")
            except Exception as e:
                print(f"   ❌ Failed to load markets: {e}")
                await exchange.close()
                return
            
            # Test 2: Fetch balance
            print("\n2️⃣  Testing: Fetch balance...")
            try:
                balance = await exchange.fetch_balance()
                print("   ✅ Balance fetched successfully")
                
                # Show all balances (including zero)
                print("\n   📊 ALL BALANCES:")
                print("   " + "-"*66)
                all_balances = []
                for currency, amounts in balance.get("total", {}).items():
                    total = float(amounts) if amounts else 0
                    free = float(balance.get("free", {}).get(currency, 0))
                    used = float(balance.get("used", {}).get(currency, 0))
                    all_balances.append({
                        "currency": currency,
                        "total": total,
                        "free": free,
                        "used": used
                    })
                
                # Sort by total (descending)
                all_balances.sort(key=lambda x: x['total'], reverse=True)
                
                for bal in all_balances:
                    status = "💰" if bal['total'] > 0 else "⚪"
                    print(f"   {status} {bal['currency']:10} Total: {bal['total']:>20,.8f}  Free: {bal['free']:>20,.8f}  Used: {bal['used']:>20,.8f}")
                
                print("   " + "-"*66)
                
                # Show non-zero balances
                non_zero = [b for b in all_balances if b['total'] > 0]
                if non_zero:
                    print(f"\n   ✅ Found {len(non_zero)} token(s) with balance:")
                    for bal in non_zero:
                        print(f"      • {bal['currency']}: {bal['total']:,.8f} (Free: {bal['free']:,.8f})")
                    
                    # Check for expected tokens
                    usdt_bal = next((b for b in non_zero if b['currency'] == 'USDT'), None)
                    sharp_bal = next((b for b in non_zero if b['currency'] == 'SHARP'), None)
                    
                    print("\n   🔍 Expected tokens:")
                    if usdt_bal:
                        print(f"      ✅ USDT: {usdt_bal['total']:,.2f} (Expected: 1,500)")
                        if abs(usdt_bal['total'] - 1500) > 100:
                            print(f"         ⚠️  Mismatch! Expected ~1,500 USDT")
                    else:
                        print(f"      ❌ USDT: Not found (Expected: 1,500)")
                    
                    if sharp_bal:
                        print(f"      ✅ SHARP: {sharp_bal['total']:,.2f} (Expected: 8,000,000)")
                        if abs(sharp_bal['total'] - 8000000) > 1000000:
                            print(f"         ⚠️  Mismatch! Expected ~8,000,000 SHARP")
                    else:
                        print(f"      ❌ SHARP: Not found (Expected: 8,000,000)")
                        # Check for similar token names
                        sharp_variants = [b for b in non_zero if 'SHARP' in b['currency'].upper() or 'SHARP' in b['currency']]
                        if sharp_variants:
                            print(f"      💡 Found similar tokens:")
                            for v in sharp_variants:
                                print(f"         • {v['currency']}: {v['total']:,.2f}")
                else:
                    print("\n   ⚠️  All balances are zero")
                    print("   Possible reasons:")
                    print("      - API keys don't have balance access")
                    print("      - Wrong BitMart account")
                    print("      - IP whitelist issue")
                    print("      - API keys are for different account")
                
            except Exception as e:
                print(f"   ❌ Failed to fetch balance: {e}")
                import traceback
                traceback.print_exc()
            
            await exchange.close()
            
        except Exception as e:
            print(f"\n❌ Failed to create BitMart connection: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_new_sharp_balance())
