#!/usr/bin/env python3
from decimal import Decimal

order_size_usd = Decimal('10')
mid_price = Decimal('0.007182')
spread_percent = Decimal('1.0')

spread_multiplier = spread_percent / Decimal('100')
bid_price = mid_price * (Decimal('1') - spread_multiplier)
ask_price = mid_price * (Decimal('1') + spread_multiplier)

bid_qty = (order_size_usd / bid_price).quantize(Decimal('0.01'), rounding='ROUND_DOWN')
ask_qty = (order_size_usd / ask_price).quantize(Decimal('0.01'), rounding='ROUND_DOWN')

print('=' * 80)
print('UPDATED SPREAD BOT CONFIG:')
print('=' * 80)
print(f'  Spread: {spread_percent}%')
print(f'  Order size: ${order_size_usd} USDT')
print()
print('CALCULATED ORDERS (at current price ~$0.007182):')
print('=' * 80)
print(f'  BUY:  {bid_qty} SHARP @ ${bid_price:.6f} = ${float(bid_price * bid_qty):.2f} USDT')
print(f'  SELL: {ask_qty} SHARP @ ${ask_price:.6f} = ${float(ask_price * ask_qty):.2f} USDT')
print()
print(f'Spread: ${float(ask_price - bid_price):.6f} ({float((ask_price - bid_price) / mid_price * 100):.2f}%)')
print('=' * 80)
