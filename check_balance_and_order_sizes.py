#!/usr/bin/env python3
"""
Check balance and order size requirements for LIMIT orders
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')
from app.coinstore_adapter import create_coinstore_exchange
from app.security import decrypt_credential
from sqlalchemy import create_engine, text
from decimal import Decimal

async def check():
    DATABASE_URL = os.getenv('DATABASE_URL')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT api_key_encrypted, api_secret_encrypted FROM exchange_credentials WHERE exchange = \'coinstore\' LIMIT 1'))
        row = result.fetchone()
        api_key = decrypt_credential(row[0])
        api_secret = decrypt_credential(row[1])
    
    exchange = await create_coinstore_exchange(api_key, api_secret, None)
    
    try:
        # Try to get balance (may fail with 1401)
        try:
            balance = await exchange.fetch_balance()
            sharp_free = balance.get('free', {}).get('SHARP', 0)
            usdt_free = balance.get('free', {}).get('USDT', 0)
            print('=' * 80)
            print('BALANCE (if available):')
            print('=' * 80)
            print(f'  SHARP available: {sharp_free}')
            print(f'  USDT available: {usdt_free}')
        except Exception as e:
            print('=' * 80)
            print('BALANCE CHECK FAILED (expected):')
            print('=' * 80)
            print(f'  Error: {e}')
            print('  Note: Balance endpoint also returns 1401')
            sharp_free = None
            usdt_free = None
        
        print()
        print('=' * 80)
        print('ORDER SIZE ANALYSIS:')
        print('=' * 80)
        
        # Get current price
        ticker = await exchange.fetch_ticker('SHARP/USDT')
        mid_price = Decimal(str(ticker.get('last') or ticker.get('close') or 0.007182))
        
        # Spread bot config
        order_size_usd = Decimal('10')
        spread_percent = Decimal('0.3')
        
        # Calculate bid/ask
        spread_multiplier = spread_percent / Decimal('100')
        bid_price = mid_price * (Decimal('1') - spread_multiplier)
        ask_price = mid_price * (Decimal('1') + spread_multiplier)
        
        # Calculate quantities
        bid_qty = (order_size_usd / bid_price).quantize(Decimal('0.01'), rounding='ROUND_DOWN')
        ask_qty = (order_size_usd / ask_price).quantize(Decimal('0.01'), rounding='ROUND_DOWN')
        
        print(f'Spread Bot would place:')
        print(f'  BUY: {bid_qty} SHARP @ ${bid_price:.6f} = ${float(bid_price * bid_qty):.2f} USDT')
        print(f'  SELL: {ask_qty} SHARP @ ${ask_price:.6f} = ${float(ask_price * ask_qty):.2f} USDT')
        print()
        
        # Test script order
        test_qty = Decimal('1740.34')
        test_price = Decimal('0.005746')
        test_value = test_qty * test_price
        
        print(f'Test script order:')
        print(f'  BUY: {test_qty} SHARP @ ${test_price:.6f} = ${float(test_value):.2f} USDT')
        print()
        
        # Check minimums
        import requests
        import json
        url = 'https://api.coinstore.com/api/v2/public/config/spot/symbols'
        payload = json.dumps({'symbolCodes': ['SHARPUSDT']})
        r = requests.post(url, data=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('code') == 0:
                symbol = data['data'][0]
                min_price = Decimal(symbol.get('minLmtPr', '0'))
                min_size = Decimal(symbol.get('minLmtSz', '0'))
                
                print('Minimum Requirements:')
                print(f'  Min price: ${min_price}')
                print(f'  Min size: {min_size} SHARP')
                print()
                print('Order Validation:')
                print(f'  Test price ({test_price:.6f}) >= min ({min_price}): {test_price >= min_price}')
                print(f'  Test qty ({test_qty}) >= min ({min_size}): {test_qty >= min_size}')
                print(f'  Spread bid price ({bid_price:.6f}) >= min ({min_price}): {bid_price >= min_price}')
                print(f'  Spread bid qty ({bid_qty}) >= min ({min_size}): {bid_qty >= min_size}')
                
                if sharp_free is not None:
                    print()
                    print('Balance Check:')
                    print(f'  BUY order needs ${float(test_value):.2f} USDT, available: ${usdt_free}')
                    print(f'  SELL order needs {test_qty} SHARP, available: {sharp_free}')
                    print(f'  BUY sufficient: {usdt_free >= float(test_value) if usdt_free else "Unknown"}')
                    print(f'  SELL sufficient: {sharp_free >= float(test_qty) if sharp_free else "Unknown"}')
        
    finally:
        await exchange.close()

asyncio.run(check())
