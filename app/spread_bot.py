"""
Spread Bot Implementation for CEX Market Making
Maintains bid/ask orders around last traded price with configurable spread
"""

import asyncio
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)


class SpreadBot:
    """
    Market making bot that maintains bid/ask orders with a target spread.
    
    Strategy:
    1. Fetch last traded price (mid price) from ticker
    2. Calculate bid at mid × (1 - spread)
    3. Calculate ask at mid × (1 + spread)
    4. Recalculate SHARP quantity from fixed USDT amount
    5. Place limit buy and limit sell orders
    6. Monitor for fills - when either fills, cancel other and restart
    """
    
    def __init__(
        self,
        bot_id: str,
        exchange,  # ccxt exchange instance
        symbol: str,  # e.g., "SHARP/USDT"
        config: dict,
        db_session=None
    ):
        self.bot_id = bot_id
        self.exchange = exchange
        self.symbol = symbol
        self.db_session = db_session
        
        # Configuration with defaults - support both old and new config formats
        # Old format: spread_bps (200 = 2%), order_size (1000), refresh_interval (30)
        # New format: spread_percent (0.3 = 0.3%), order_size_usdt (10), poll_interval_seconds (5), refresh_interval_seconds (60)
        
        # Spread: support both spread_bps (basis points) and spread_percent (percentage)
        if 'spread_percent' in config:
            self.spread_percent = Decimal(str(config.get('spread_percent', 0.3)))
        elif 'spread_bps' in config:
            # Convert basis points to percentage (200 bps = 2% = 0.02)
            spread_bps = Decimal(str(config.get('spread_bps', 200)))
            self.spread_percent = spread_bps / Decimal('10000') * Decimal('100')  # Convert to percentage
        else:
            self.spread_percent = Decimal('3.0')  # Default 3.0% (wider spread for testing)
        
        # Order size: support both order_size_usdt and order_size
        if 'order_size_usdt' in config:
            self.order_size_usd = Decimal(str(config.get('order_size_usdt', 10)))
        elif 'order_size' in config:
            # Old format might be in tokens, but we'll treat as USD for now
            order_size = Decimal(str(config.get('order_size', 1000)))
            # If it's > 100, assume it's old token-based config, convert to USD estimate
            if order_size > 100:
                logger.warning(f"⚠️ Old config format detected: order_size={order_size}. Assuming USD value.")
                self.order_size_usd = Decimal('10')  # Use safe default
            else:
                self.order_size_usd = order_size
        else:
            self.order_size_usd = Decimal('10')  # Default $10 USDT
        
        # Poll interval: support both poll_interval_seconds and default
        self.poll_interval = config.get('poll_interval_seconds', config.get('poll_interval', 5))
        
        # Refresh interval: support both refresh_interval_seconds and refresh_interval
        self.refresh_interval = config.get('refresh_interval_seconds', config.get('refresh_interval', 60))
        
        self.price_decimals = config.get('price_decimals', 6)  # SHARPUSDT tickSz=6 (per order book)
        self.amount_decimals = config.get('amount_decimals', 2)  # SHARPUSDT lotSz=2 (per order book)
        
        # State tracking
        self.active_bid_id: Optional[str] = None
        self.active_ask_id: Optional[str] = None
        self.running = False
        
    async def start(self):
        """Start the spread bot main loop."""
        self.running = True
        logger.info(f"🚀 Spread bot {self.bot_id} starting for {self.symbol}")
        logger.info(f"   Config: spread={self.spread_percent}%, size=${self.order_size_usd} USDT per side")
        
        while self.running:
            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"❌ Spread bot {self.bot_id} cycle error: {e}", exc_info=True)
                # Don't crash the bot, continue after delay
                await asyncio.sleep(10)
    
    async def stop(self):
        """Stop the bot and cancel all orders."""
        self.running = False
        logger.info(f"🛑 Stopping spread bot {self.bot_id}")
        await self._cancel_active_orders()
    
    async def _run_cycle(self):
        """Execute one cycle: fetch price, place orders, monitor for fills."""
        logger.info(f"📈 Spread bot {self.bot_id} - Starting cycle")
        
        # Step 1: Get last traded price (mid price) from ticker
        mid_price = await self._get_last_traded_price()
        if not mid_price or mid_price <= 0:
            logger.warning(f"⚠️ Could not get valid price, retrying in 5s...")
            await asyncio.sleep(5)
            return
        
        logger.info(f"📊 Last traded price (mid): {mid_price}")
        
        # Step 2: Calculate bid/ask prices at ±spread from mid
        spread_multiplier = self.spread_percent / Decimal('100')  # 0.003 for 0.3%
        bid_price = (mid_price * (Decimal('1') - spread_multiplier)).quantize(
            Decimal(10) ** -self.price_decimals, rounding=ROUND_DOWN
        )
        ask_price = (mid_price * (Decimal('1') + spread_multiplier)).quantize(
            Decimal(10) ** -self.price_decimals, rounding=ROUND_DOWN
        )
        
        # Step 3: Recalculate SHARP quantity from fixed USDT amount
        # $10 at different prices = different SHARP amounts
        bid_qty = (self.order_size_usd / bid_price).quantize(
            Decimal(10) ** -self.amount_decimals, rounding=ROUND_DOWN
        )
        ask_qty = (self.order_size_usd / ask_price).quantize(
            Decimal(10) ** -self.amount_decimals, rounding=ROUND_DOWN
        )
        
        logger.info(f"📍 Calculated levels:")
        logger.info(f"   Bid: {bid_qty} SHARP @ {bid_price} = ${self.order_size_usd} USDT")
        logger.info(f"   Ask: {ask_qty} SHARP @ {ask_price} = ${self.order_size_usd} USDT")
        
        # Step 4: Cancel any existing orders
        await self._cancel_active_orders()
        
        # Step 5: Place both limit orders
        try:
            bid_order = await self._place_order('buy', bid_price, bid_qty)
            ask_order = await self._place_order('sell', ask_price, ask_qty)
            
            if not bid_order or not ask_order:
                logger.error("❌ Failed to place orders, retrying cycle...")
                await asyncio.sleep(5)
                return
            
            self.active_bid_id = str(bid_order.get('id'))
            self.active_ask_id = str(ask_order.get('id'))
            
            logger.info(f"✅ Placed orders: bid #{self.active_bid_id}, ask #{self.active_ask_id}")
            
            # Log order placements for recent activity display
            await self._log_order_placement('buy', bid_qty, bid_price, self.active_bid_id)
            await self._log_order_placement('sell', ask_qty, ask_price, self.active_ask_id)
            
        except Exception as e:
            logger.error(f"❌ Error placing orders: {e}", exc_info=True)
            await asyncio.sleep(5)
            return
        
        # Step 6: Monitor for fills
        placed_time = time.time()
        
        while self.running:
            await asyncio.sleep(self.poll_interval)
            
            # Check if orders are still open
            try:
                open_orders = await self.exchange.fetch_open_orders(self.symbol)
                open_ids = set()
                
                # Parse open orders (handle different response formats)
                # CoinstoreAdapter.fetch_open_orders returns a list directly
                if isinstance(open_orders, list):
                    orders_list = open_orders
                elif isinstance(open_orders, dict):
                    # Handle dict format (e.g., {'data': [...], 'code': 0})
                    orders_list = open_orders.get('data', []) or open_orders.get('orders', []) or []
                else:
                    logger.warning(f"⚠️ Unexpected open_orders format: {type(open_orders)}")
                    orders_list = []
                
                for order in orders_list:
                    # Handle different order ID field names
                    order_id = str(
                        order.get('id') or 
                        order.get('orderId') or 
                        order.get('ordId') or
                        order.get('order_id') or
                        ''
                    )
                    if order_id and order_id != 'None' and order_id != '':
                        open_ids.add(order_id)
                
                bid_open = self.active_bid_id in open_ids if self.active_bid_id else False
                ask_open = self.active_ask_id in open_ids if self.active_ask_id else False
                
                logger.debug(f"🔍 Open orders check: bid_id={self.active_bid_id} (open={bid_open}), ask_id={self.active_ask_id} (open={ask_open}), total_open={len(open_ids)}")
                
                # Step 7: Handle fills
                if not bid_open or not ask_open:
                    if not bid_open and self.active_bid_id:
                        logger.info(f"✅ BID FILLED at {bid_price} ({bid_qty} SHARP)")
                        await self._log_trade('buy', bid_qty, bid_price, self.active_bid_id)
                    
                    if not ask_open and self.active_ask_id:
                        logger.info(f"✅ ASK FILLED at {ask_price} ({ask_qty} SHARP)")
                        await self._log_trade('sell', ask_qty, ask_price, self.active_ask_id)
                    
                    # Cancel remaining order
                    if bid_open and self.active_bid_id:
                        try:
                            await self.exchange.cancel_order(self.active_bid_id, self.symbol)
                            logger.info(f"🗑️ Cancelled unfilled bid #{self.active_bid_id}")
                        except Exception as e:
                            logger.debug(f"Could not cancel bid (may already be filled): {e}")
                    
                    if ask_open and self.active_ask_id:
                        try:
                            await self.exchange.cancel_order(self.active_ask_id, self.symbol)
                            logger.info(f"🗑️ Cancelled unfilled ask #{self.active_ask_id}")
                        except Exception as e:
                            logger.debug(f"Could not cancel ask (may already be filled): {e}")
                    
                    # Clear active order IDs
                    self.active_bid_id = None
                    self.active_ask_id = None
                    
                    # Break inner loop → restart cycle with new price
                    logger.info("🔄 Order filled, restarting cycle with new price...")
                    break
                
                # Step 8: Refresh stale orders
                elapsed = time.time() - placed_time
                if elapsed > self.refresh_interval:
                    logger.info(f"⏰ Orders stale ({elapsed:.0f}s), refreshing...")
                    await self._cancel_active_orders()
                    break  # Restart cycle with fresh price
            
            except Exception as e:
                logger.error(f"❌ Error monitoring orders: {e}", exc_info=True)
                await asyncio.sleep(5)
                # Continue monitoring
    
    async def _get_last_traded_price(self) -> Optional[Decimal]:
        """Fetch last traded price from ticker (public endpoint)."""
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            
            # Try different fields for last traded price
            last_price = (
                ticker.get('last') or 
                ticker.get('close') or 
                ticker.get('price') or
                0
            )
            
            if not last_price or last_price <= 0:
                logger.warning(f"⚠️ Invalid ticker price: {ticker}")
                return None
            
            return Decimal(str(last_price))
            
        except Exception as e:
            logger.error(f"❌ Error fetching ticker: {e}", exc_info=True)
            return None
    
    async def _place_order(self, side: str, price: Decimal, amount: Decimal) -> Optional[Dict]:
        """Place a limit order on the exchange."""
        try:
            logger.info(f"📝 Placing {side.upper()} order: {amount} SHARP @ {price}")
            
            order = await self.exchange.create_limit_order(
                symbol=self.symbol,
                side=side,
                amount=float(amount),
                price=float(price)
            )
            
            order_id = order.get('id')
            if order_id:
                logger.info(f"✅ Order placed: {side.upper()} #{order_id}")
                return order
            else:
                logger.error(f"❌ Order placed but no ID returned: {order}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Order placement error ({side} {amount} @ {price}): {e}", exc_info=True)
            return None
    
    async def _cancel_active_orders(self):
        """Cancel both active orders if they exist."""
        if self.active_bid_id:
            try:
                await self.exchange.cancel_order(self.active_bid_id, self.symbol)
                logger.info(f"🗑️ Cancelled bid #{self.active_bid_id}")
            except Exception as e:
                logger.debug(f"Could not cancel bid: {e}")
            self.active_bid_id = None
        
        if self.active_ask_id:
            try:
                await self.exchange.cancel_order(self.active_ask_id, self.symbol)
                logger.info(f"🗑️ Cancelled ask #{self.active_ask_id}")
            except Exception as e:
                logger.debug(f"Could not cancel ask: {e}")
            self.active_ask_id = None
    
    async def _log_order_placement(self, side: str, amount: Decimal, price: Decimal, order_id: str):
        """Log limit order placement to database for recent activity display."""
        if not self.db_session:
            return
        
        try:
            from sqlalchemy import text
            # Log order placement (will show in recent activity as "Buy order placed" / "Sell order placed")
            # Note: This creates a separate entry from filled trades, so both placement and fill will show
            self.db_session.execute(text("""
                INSERT INTO trade_logs (bot_id, side, amount, price, cost_usd, order_id, created_at)
                VALUES (:bot_id, :side, :amount, :price, :cost_usd, :order_id, NOW())
            """), {
                'bot_id': self.bot_id,
                'side': f"{side}_placed",  # Prefix to distinguish: "buy_placed" vs "buy" (filled)
                'amount': float(amount),
                'price': float(price),
                'cost_usd': float(amount * price),  # Estimated cost
                'order_id': order_id
            })
            self.db_session.commit()
            logger.debug(f"📝 Logged order placement: {side.upper()} {amount} @ {price} (order #{order_id})")
        except Exception as e:
            logger.warning(f"⚠️ Could not log order placement: {e}")
            self.db_session.rollback()
    
    async def _log_trade(self, side: str, amount: Decimal, price: Decimal, order_id: str):
        """Log filled trade to database."""
        if not self.db_session:
            return
        
        try:
            from sqlalchemy import text
            
            cost_usd = float(amount * price)
            
            self.db_session.execute(text("""
                INSERT INTO trade_logs (bot_id, side, amount, price, cost_usd, order_id, created_at)
                VALUES (:bot_id, :side, :amount, :price, :cost_usd, :order_id, NOW())
            """), {
                'bot_id': self.bot_id,
                'side': side,
                'amount': float(amount),
                'price': float(price),
                'cost_usd': cost_usd,
                'order_id': order_id
            })
            
            self.db_session.commit()
            logger.info(f"📝 Logged trade: {side} {amount} @ {price} = ${cost_usd:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error logging trade: {e}", exc_info=True)
            if self.db_session:
                self.db_session.rollback()
