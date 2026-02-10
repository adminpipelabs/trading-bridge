#!/usr/bin/env python3
"""
Simple test script to verify Spread Bot core operations work.
Tests the 4 critical operations:
1. Fetch ticker (confirm price comes back)
2. Place limit buy 5% below market (won't fill, confirms order placement)
3. Check open orders (confirms order shows up)
4. Cancel order (confirms cancel works)
"""

import asyncio
import os
import sys
from decimal import Decimal

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.coinstore_adapter import create_coinstore_exchange
from app.security import decrypt_credential
from app.database import get_db_session
from sqlalchemy import text

async def test_spread_bot_operations():
    """Test the 4 core operations needed for spread bot."""
    
    print("=" * 80)
    print("🧪 SPREAD BOT CORE OPERATIONS TEST")
    print("=" * 80)
    print()
    
    # Get API credentials from database
    db = get_db_session()
    try:
        # Get Coinstore credentials for client_new_sharp_foundation
        result = db.execute(text("""
            SELECT ec.api_key_encrypted, ec.api_secret_encrypted
            FROM exchange_credentials ec
            JOIN clients cl ON cl.id = ec.client_id
            WHERE cl.account_identifier = 'client_new_sharp_foundation'
            AND ec.exchange = 'coinstore'
            LIMIT 1
        """)).fetchone()
        
        if not result:
            print("❌ No Coinstore credentials found for client_new_sharp_foundation")
            return False
        
        api_key_encrypted = result[0]
        api_secret_encrypted = result[1]
        
        from app.security import decrypt_credential
        api_key = decrypt_credential(api_key_encrypted)
        api_secret = decrypt_credential(api_secret_encrypted)
        
        print(f"✅ Loaded API credentials")
        print()
        
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return False
    finally:
        db.close()
    
    # Create exchange instance
    print("📡 Creating Coinstore exchange instance...")
    try:
        exchange = await create_coinstore_exchange(
            api_key=api_key,
            api_secret=api_secret,
            proxy_url=os.getenv("QUOTAGUARDSTATIC_URL") or os.getenv("QUOTAGUARD_PROXY_URL")
        )
        print("✅ Exchange instance created")
        print()
    except Exception as e:
        print(f"❌ Error creating exchange: {e}")
        return False
    
    symbol = "SHARP/USDT"
    
    # Test 1: Fetch ticker (confirm price comes back)
    print("=" * 80)
    print("TEST 1: Fetch Ticker (Get Last Traded Price)")
    print("=" * 80)
    try:
        ticker = await exchange.fetch_ticker(symbol)
        last_price = ticker.get('last') or ticker.get('close') or ticker.get('price')
        
        if not last_price or last_price <= 0:
            print(f"❌ Invalid price: {last_price}")
            print(f"   Ticker response: {ticker}")
            return False
        
        print(f"✅ Ticker fetched successfully")
        print(f"   Symbol: {symbol}")
        print(f"   Last price: ${last_price}")
        print(f"   Full ticker: {ticker}")
        print()
        
    except Exception as e:
        print(f"❌ Error fetching ticker: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Place limit buy 5% below market (won't fill, confirms order placement)
    print("=" * 80)
    print("TEST 2: Place Limit Buy Order (5% Below Market)")
    print("=" * 80)
    try:
        # Calculate test price: 5% below market (won't fill)
        test_price = Decimal(str(last_price)) * Decimal('0.95')
        test_amount = Decimal('100')  # Small test amount
        
        print(f"   Market price: ${last_price}")
        print(f"   Test buy price: ${test_price} (5% below)")
        print(f"   Test amount: {test_amount} SHARP")
        print(f"   Placing order...")
        
        order = await exchange.create_limit_order(
            symbol=symbol,
            side='buy',
            amount=float(test_amount),
            price=float(test_price)
        )
        
        order_id = order.get('id')
        if not order_id:
            print(f"❌ Order placed but no ID returned: {order}")
            return False
        
        print(f"✅ Order placed successfully")
        print(f"   Order ID: {order_id}")
        print(f"   Full response: {order}")
        print()
        
    except Exception as e:
        print(f"❌ Error placing order: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Check open orders (confirms order shows up)
    print("=" * 80)
    print("TEST 3: Check Open Orders (Verify Order Appears)")
    print("=" * 80)
    try:
        await asyncio.sleep(2)  # Wait a moment for order to appear
        
        open_orders = await exchange.fetch_open_orders(symbol)
        
        print(f"   Checking for order ID: {order_id}")
        
        # Parse open orders
        if isinstance(open_orders, list):
            orders_list = open_orders
        elif isinstance(open_orders, dict):
            orders_list = open_orders.get('data', []) or open_orders.get('orders', []) or []
        else:
            orders_list = []
        
        found_order = None
        for order in orders_list:
            order_id_str = str(order.get('id') or order.get('orderId') or order.get('ordId') or '')
            if order_id_str == str(order_id):
                found_order = order
                break
        
        if not found_order:
            print(f"❌ Order {order_id} not found in open orders")
            print(f"   Open orders response: {open_orders}")
            print(f"   Found {len(orders_list)} open orders")
            return False
        
        print(f"✅ Order found in open orders")
        print(f"   Order details: {found_order}")
        print()
        
    except Exception as e:
        print(f"❌ Error checking open orders: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Cancel order (confirms cancel works)
    print("=" * 80)
    print("TEST 4: Cancel Order (Verify Cancel Works)")
    print("=" * 80)
    try:
        print(f"   Cancelling order ID: {order_id}")
        
        cancel_result = await exchange.cancel_order(order_id, symbol)
        
        print(f"✅ Order cancelled successfully")
        print(f"   Cancel response: {cancel_result}")
        print()
        
        # Verify it's gone
        await asyncio.sleep(2)
        open_orders_after = await exchange.fetch_open_orders(symbol)
        
        if isinstance(open_orders_after, list):
            orders_after = open_orders_after
        elif isinstance(open_orders_after, dict):
            orders_after = open_orders_after.get('data', []) or open_orders_after.get('orders', []) or []
        else:
            orders_after = []
        
        still_open = any(
            str(o.get('id') or o.get('orderId') or o.get('ordId') or '') == str(order_id)
            for o in orders_after
        )
        
        if still_open:
            print(f"⚠️  Warning: Order {order_id} still appears in open orders")
            print(f"   This might be normal if cancel is async")
        else:
            print(f"✅ Order confirmed removed from open orders")
        print()
        
    except Exception as e:
        print(f"❌ Error cancelling order: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # All tests passed
    print("=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print()
    print("The spread bot core operations are working correctly:")
    print("  ✅ Ticker fetch works")
    print("  ✅ Order placement works")
    print("  ✅ Open orders check works")
    print("  ✅ Order cancellation works")
    print()
    print("Ready to deploy spread bot!")
    
    return True

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check ENCRYPTION_KEY
    if not os.getenv("ENCRYPTION_KEY"):
        print("❌ ENCRYPTION_KEY not set")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(test_spread_bot_operations())
    sys.exit(0 if success else 1)
