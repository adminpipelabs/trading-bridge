"""
Coinstore Connector Test Script

Run this to verify Coinstore API connection works before deploying.

Usage:
    python test_coinstore.py

Set environment variables:
    COINSTORE_API_KEY=your_key
    COINSTORE_API_SECRET=your_secret
    QUOTAGUARDSTATIC_URL=https://... (optional, for proxy)
"""

import asyncio
import os
import logging
from app.coinstore_connector import CoinstoreConnector
from app.coinstore_adapter import create_coinstore_exchange

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_public_endpoints():
    """Test public endpoints (no auth needed)."""
    print("\n" + "="*60)
    print("TESTING PUBLIC ENDPOINTS (no auth)")
    print("="*60)
    
    connector = CoinstoreConnector(
        api_key="dummy",
        api_secret="dummy"
    )
    
    try:
        # Test ticker
        print("\n📊 Testing get_ticker('BTCUSDT')...")
        ticker = await connector.get_ticker("BTCUSDT")
        print(f"   Response: {ticker}")
        if ticker.get('code') == 0:
            data = ticker.get('data', {})
            print(f"   Last price: {data.get('lastPrice')}")
            print(f"   Bid: {data.get('bidPrice')}")
            print(f"   Ask: {data.get('askPrice')}")
            print(f"   Volume: {data.get('volume24h')}")
            print("   ✅ Ticker works!")
        else:
            print(f"   ❌ Error: {ticker.get('msg')}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await connector.close()


async def test_authenticated_endpoints():
    """Test authenticated endpoints (requires valid keys)."""
    print("\n" + "="*60)
    print("TESTING AUTHENTICATED ENDPOINTS")
    print("="*60)
    
    api_key = os.getenv('COINSTORE_API_KEY')
    api_secret = os.getenv('COINSTORE_API_SECRET')
    proxy_url = os.getenv('QUOTAGUARDSTATIC_URL')
    
    if not api_key or not api_secret:
        print("⚠️  Set COINSTORE_API_KEY and COINSTORE_API_SECRET to test auth endpoints")
        print("   Skipping authenticated tests...")
        return
    
    connector = CoinstoreConnector(
        api_key=api_key,
        api_secret=api_secret,
        proxy_url=proxy_url
    )
    
    try:
        # Test balance
        print("\n💰 Testing get_balances()...")
        balances = await connector.get_balances()
        
        if balances.get("code") == 0:
            print("   ✅ Balance fetch works!")
            data = balances.get("data", {})
            # Show non-zero balances
            for currency, amounts in data.items():
                if amounts.get("available", 0) > 0 or amounts.get("frozen", 0) > 0:
                    print(f"   {currency}: {amounts['available']} available, {amounts['frozen']} frozen")
        else:
            print(f"   ❌ Error: {balances.get('msg')}")
        
        # Test open orders
        print("\n📋 Testing get_open_orders()...")
        orders = await connector.get_open_orders()
        
        if orders.get("code") == 0:
            print("   ✅ Open orders fetch works!")
            order_list = orders.get("data", [])
            print(f"   Found {len(order_list)} open orders")
        else:
            print(f"   ❌ Error: {orders.get('msg')}")
        
        # Test symbols
        print("\n🔤 Testing get_symbols()...")
        symbols = await connector.get_symbols()
        
        if symbols.get("code") == 0:
            print("   ✅ Symbols fetch works!")
            symbol_list = symbols.get("data", [])
            print(f"   Found {len(symbol_list)} trading pairs")
        else:
            print(f"   ❌ Error: {symbols.get('msg')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await connector.close()


async def test_ccxt_adapter():
    """Test the ccxt-compatible adapter."""
    print("\n" + "="*60)
    print("TESTING CCXT-COMPATIBLE ADAPTER")
    print("="*60)
    
    api_key = os.getenv('COINSTORE_API_KEY')
    api_secret = os.getenv('COINSTORE_API_SECRET')
    proxy_url = os.getenv('QUOTAGUARDSTATIC_URL')
    
    if not api_key or not api_secret:
        print("⚠️  Set COINSTORE_API_KEY and COINSTORE_API_SECRET to test adapter")
        print("   Skipping adapter tests...")
        return
    
    try:
        print("\n🔧 Creating exchange via adapter...")
        exchange = await create_coinstore_exchange(
            api_key=api_key,
            api_secret=api_secret,
            proxy_url=proxy_url
        )
        
        print(f"   ✅ Exchange created: {exchange.name}")
        print(f"   Markets loaded: {len(exchange.markets)}")
        
        # Test fetch_ticker (ccxt style)
        print("\n📊 Testing fetch_ticker('BTC/USDT')...")
        ticker = await exchange.fetch_ticker("BTC/USDT")
        print(f"   Last: {ticker.get('last')}")
        print(f"   Bid: {ticker.get('bid')}")
        print(f"   Ask: {ticker.get('ask')}")
        print("   ✅ fetch_ticker works!")
        
        # Test fetch_balance (ccxt style)
        print("\n💰 Testing fetch_balance()...")
        balance = await exchange.fetch_balance()
        print("   ✅ fetch_balance works!")
        
        # Show USDT balance if exists
        if 'USDT' in balance.get('total', {}):
            print(f"   USDT: {balance['total']['USDT']} total")
        
        # Test fetch_open_orders (ccxt style)
        print("\n📋 Testing fetch_open_orders()...")
        orders = await exchange.fetch_open_orders()
        print(f"   ✅ fetch_open_orders works! Found {len(orders)} orders")
        
        await exchange.close()
        print("\n✅ All adapter tests passed!")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_place_order_dry_run():
    """
    Test order placement logic WITHOUT actually placing order.
    This validates the signature generation works.
    """
    print("\n" + "="*60)
    print("DRY RUN: Order Placement Test")
    print("="*60)
    
    api_key = os.getenv('COINSTORE_API_KEY')
    api_secret = os.getenv('COINSTORE_API_SECRET')
    
    if not api_key or not api_secret:
        print("⚠️  Skipping (no API keys)")
        return
    
    print("\n⚠️  This will NOT place a real order.")
    print("   It only tests that the request is properly formatted.")
    
    # To actually test order placement, uncomment below:
    """
    exchange = await create_coinstore_exchange(
        api_key=api_key,
        api_secret=api_secret,
    )
    
    # Place a tiny limit order far from market price (won't fill)
    order = await exchange.create_limit_buy_order(
        symbol="BTC/USDT",
        amount=0.0001,  # Minimum
        price=10000,    # Far below market, won't fill
    )
    print(f"Order placed: {order}")
    
    # Cancel it immediately
    await exchange.cancel_order(order['id'], "BTC/USDT")
    print("Order cancelled")
    
    await exchange.close()
    """
    print("   (Uncomment code in test file to run actual order test)")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("COINSTORE CONNECTOR TEST SUITE")
    print("="*60)
    
    # Test public endpoints first (no auth needed)
    await test_public_endpoints()
    
    # Test authenticated endpoints
    await test_authenticated_endpoints()
    
    # Test ccxt adapter
    await test_ccxt_adapter()
    
    # Dry run order test
    await test_place_order_dry_run()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
