"""
Spread Bot Implementation for CEX Market Making
Maintains bid/ask orders around mid-price with configurable spread
"""

import asyncio
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SpreadBot:
    """
    Market making bot that maintains bid/ask orders with a target spread.
    
    Strategy:
    1. Fetch current orderbook
    2. Calculate mid price
    3. Place bid at mid - (spread/2)
    4. Place ask at mid + (spread/2)
    5. Cancel stale orders, refresh periodically
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
        
        # Configuration with defaults
        self.spread_bps = Decimal(str(config.get('spread_bps', 200)))  # 2% default
        # Order size in USD - will be converted to base tokens based on price
        self.order_size_usd = Decimal(str(config.get('order_size_usd', 10)))
        self.refresh_interval = config.get('refresh_interval', 30)
        self.max_inventory_imbalance = Decimal(str(config.get('max_imbalance', 0.3)))  # 30%
        self.min_order_size = Decimal(str(config.get('min_order_size', 10)))
        self.price_decimals = config.get('price_decimals', 8)
        self.amount_decimals = config.get('amount_decimals', 2)
        
        # State tracking
        self.active_orders: Dict[str, dict] = {}  # order_id -> order_info
        self.last_mid_price: Optional[Decimal] = None
        self.inventory_base = Decimal('0')
        self.inventory_quote = Decimal('0')
        self.running = False
        
    async def start(self):
        """Start the spread bot main loop."""
        self.running = True
        logger.info(f"🚀 Spread bot {self.bot_id} starting for {self.symbol}")
        
        while self.running:
            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"❌ Spread bot {self.bot_id} cycle error: {e}", exc_info=True)
                # Don't crash the bot, continue after delay
            
            await asyncio.sleep(self.refresh_interval)
    
    async def stop(self):
        """Stop the bot and cancel all orders."""
        self.running = False
        logger.info(f"🛑 Stopping spread bot {self.bot_id}")
        await self._cancel_all_orders()
    
    async def _run_cycle(self):
        """Execute one cycle of the spread bot."""
        logger.info(f"📈 Spread bot {self.bot_id} - Running cycle")
        
        # Step 1: Fetch balance
        balance = await self._fetch_balance()
        if not balance:
            logger.warning(f"⚠️ Could not fetch balance, skipping cycle")
            return
        
        self.inventory_base = Decimal(str(balance.get('base_free', 0)))
        self.inventory_quote = Decimal(str(balance.get('quote_free', 0)))
        
        logger.info(f"💰 Balance: {self.inventory_base} base, {self.inventory_quote} quote")
        
        # Step 2: Fetch orderbook and calculate mid price
        mid_price = await self._get_mid_price()
        if not mid_price:
            logger.warning(f"⚠️ Could not get mid price, skipping cycle")
            return
        
        self.last_mid_price = mid_price
        logger.info(f"📊 Mid price: {mid_price}")
        
        # Step 3: Calculate bid/ask prices
        spread_multiplier = self.spread_bps / Decimal('10000')
        half_spread = mid_price * spread_multiplier / 2
        
        bid_price = (mid_price - half_spread).quantize(
            Decimal(10) ** -self.price_decimals, rounding=ROUND_DOWN
        )
        ask_price = (mid_price + half_spread).quantize(
            Decimal(10) ** -self.price_decimals, rounding=ROUND_DOWN
        )
        
        logger.info(f"📍 Target prices - Bid: {bid_price}, Ask: {ask_price}")
        
        # Step 4: Cancel stale orders
        await self._cancel_stale_orders(bid_price, ask_price)
        
        # Step 5: Calculate order sizes (in base tokens) from USD order size
        bid_size, ask_size = self._calculate_order_sizes()
        
        # Step 6: Place new orders
        # Bid (BUY): Spending USDT to buy SHARP tokens
        bid_cost_usd = bid_size * bid_price
        if bid_size >= self.min_order_size and self.inventory_quote >= bid_cost_usd:
            await self._place_order('buy', bid_price, bid_size)
            logger.info(f"✅ Bid placed: {bid_size} SHARP @ {bid_price} = ${bid_cost_usd:.2f} USDT")
        else:
            logger.info(f"⏭️ Skipping bid: size={bid_size} SHARP, cost=${bid_cost_usd:.2f}, have=${self.inventory_quote:.2f} USDT")
        
        # Ask (SELL): Selling SHARP tokens to get USDT
        if ask_size >= self.min_order_size and self.inventory_base >= ask_size:
            await self._place_order('sell', ask_price, ask_size)
            logger.info(f"✅ Ask placed: {ask_size} SHARP @ {ask_price} = ${ask_size * ask_price:.2f} USDT")
        else:
            logger.info(f"⏭️ Skipping ask: size={ask_size} SHARP, have={self.inventory_base} SHARP")
        
        logger.info(f"✅ Cycle complete. Active orders: {len(self.active_orders)}")
    
    async def _fetch_balance(self) -> Optional[dict]:
        """Fetch current balance from exchange."""
        try:
            # BitMart requires type parameter
            if hasattr(self.exchange, 'id') and self.exchange.id == 'bitmart':
                balance = await self.exchange.fetch_balance({'type': 'spot'})
            else:
                balance = await self.exchange.fetch_balance()
            
            # Parse symbol to get base/quote
            base, quote = self.symbol.split('/')
            
            base_free = Decimal(str(balance.get('free', {}).get(base, 0)))
            quote_free = Decimal(str(balance.get('free', {}).get(quote, 0)))
            
            return {
                'base_free': base_free,
                'quote_free': quote_free,
                'base_used': Decimal(str(balance.get('used', {}).get(base, 0))),
                'quote_used': Decimal(str(balance.get('used', {}).get(quote, 0))),
            }
        except Exception as e:
            # Log full error details for BitMart IP whitelist errors
            error_str = str(e)
            error_type = type(e).__name__
            
            # Check if it's a BitMart error with code
            if 'bitmart' in error_str.lower() or (hasattr(self.exchange, 'id') and self.exchange.id == 'bitmart'):
                logger.error(f"❌ Balance fetch error: {error_type}: {error_str}")
                # Try to get more details from ccxt exception
                if hasattr(e, 'args') and e.args:
                    logger.error(f"   Error args: {e.args}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"   HTTP response: {e.response}")
                logger.error(f"   Full traceback:", exc_info=True)
            else:
                logger.error(f"❌ Balance fetch error: {error_type}: {error_str}", exc_info=True)
            return None
    
    async def _get_mid_price(self) -> Optional[Decimal]:
        """Fetch orderbook and calculate mid price."""
        try:
            orderbook = await self.exchange.fetch_order_book(self.symbol, limit=5)
            
            if not orderbook.get('bids') or not orderbook.get('asks'):
                logger.warning(f"⚠️ Empty orderbook for {self.symbol}")
                return None
            
            best_bid = Decimal(str(orderbook['bids'][0][0]))
            best_ask = Decimal(str(orderbook['asks'][0][0]))
            
            mid_price = (best_bid + best_ask) / 2
            
            logger.info(f"📖 Orderbook: bid={best_bid}, ask={best_ask}, mid={mid_price}")
            
            return mid_price
        except Exception as e:
            logger.error(f"❌ Orderbook fetch error: {e}", exc_info=True)
            return None
    
    def _calculate_order_sizes(self) -> Tuple[Decimal, Decimal]:
        """
        Calculate bid/ask sizes in base tokens from USD order size.
        
        For spread bot:
        - Bid (BUY): Convert $10 USDT to SHARP tokens at bid_price
        - Ask (SELL): Convert $10 USDT to SHARP tokens at ask_price
        - Both orders have same USD value, different token amounts due to price spread
        """
        if not self.last_mid_price or self.last_mid_price <= 0:
            # Fallback: use mid price if available, otherwise skip
            logger.warning("⚠️ No mid price available for order size calculation")
            return Decimal('0'), Decimal('0')
        
        # Calculate bid/ask prices (same as in _run_cycle)
        spread_multiplier = self.spread_bps / Decimal('10000')
        half_spread = self.last_mid_price * spread_multiplier / 2
        bid_price = (self.last_mid_price - half_spread).quantize(
            Decimal(10) ** -self.price_decimals, rounding=ROUND_DOWN
        )
        ask_price = (self.last_mid_price + half_spread).quantize(
            Decimal(10) ** -self.price_decimals, rounding=ROUND_DOWN
        )
        
        # Convert USD order size to base tokens
        # Bid: $10 USDT / bid_price = SHARP tokens to buy
        bid_size_base = self.order_size_usd / bid_price
        
        # Ask: $10 USDT / ask_price = SHARP tokens to sell
        ask_size_base = self.order_size_usd / ask_price
        
        # Apply inventory management skewing
        base_value = self.inventory_base * self.last_mid_price
        total_value = base_value + self.inventory_quote
        
        if total_value > 0:
            base_ratio = base_value / total_value
            target_ratio = Decimal('0.5')
            imbalance = base_ratio - target_ratio
            
            if abs(imbalance) > self.max_inventory_imbalance:
                logger.warning(f"⚠️ Inventory imbalance: {imbalance:.2%}")
            
            # Skew: more base = bigger asks, less base = bigger bids
            skew = 1 + (imbalance * 2)
            bid_size = bid_size_base * max(Decimal('0.5'), 2 - skew)
            ask_size = ask_size_base * max(Decimal('0.5'), skew)
        else:
            bid_size = bid_size_base
            ask_size = ask_size_base
        
        return (
            bid_size.quantize(Decimal(10) ** -self.amount_decimals, rounding=ROUND_DOWN),
            ask_size.quantize(Decimal(10) ** -self.amount_decimals, rounding=ROUND_DOWN)
        )
    
    async def _place_order(self, side: str, price: Decimal, amount: Decimal):
        """Place a limit order on the exchange."""
        try:
            logger.info(f"📝 Placing {side} order: {amount} @ {price}")
            
            order = await self.exchange.create_limit_order(
                symbol=self.symbol,
                side=side,
                amount=float(amount),
                price=float(price)
            )
            
            order_id = order.get('id')
            if order_id:
                self.active_orders[order_id] = {
                    'id': order_id,
                    'side': side,
                    'price': price,
                    'amount': amount,
                    'created_at': datetime.now(timezone.utc)
                }
                logger.info(f"✅ Order placed: {order_id}")
                
                # Log to database if available
                await self._log_order(order, side, price, amount)
            
            return order
        except Exception as e:
            logger.error(f"❌ Order placement error ({side} {amount} @ {price}): {e}", exc_info=True)
            return None
    
    async def _cancel_order(self, order_id: str):
        """Cancel a specific order."""
        try:
            await self.exchange.cancel_order(order_id, self.symbol)
            if order_id in self.active_orders:
                del self.active_orders[order_id]
            logger.info(f"🗑️ Cancelled order: {order_id}")
        except Exception as e:
            # Order might already be filled or cancelled
            error_str = str(e).lower()
            if 'not found' in error_str or 'does not exist' in error_str or 'invalid' in error_str:
                if order_id in self.active_orders:
                    del self.active_orders[order_id]
            else:
                logger.error(f"❌ Cancel order error: {e}", exc_info=True)
    
    async def _cancel_all_orders(self):
        """Cancel all active orders."""
        logger.info(f"🗑️ Cancelling all {len(self.active_orders)} orders")
        for order_id in list(self.active_orders.keys()):
            await self._cancel_order(order_id)
    
    async def _cancel_stale_orders(self, new_bid: Decimal, new_ask: Decimal):
        """
        Cancel orders that are too far from current target prices.
        Threshold: 0.5% price deviation triggers cancel.
        """
        stale_threshold = Decimal('0.005')  # 0.5%
        
        for order_id, order in list(self.active_orders.items()):
            order_price = order['price']
            
            if order['side'] == 'buy':
                deviation = abs(order_price - new_bid) / new_bid if new_bid > 0 else Decimal('1')
            else:
                deviation = abs(order_price - new_ask) / new_ask if new_ask > 0 else Decimal('1')
            
            if deviation > stale_threshold:
                logger.info(f"🔄 Cancelling stale order {order_id}: deviation={deviation:.2%}")
                await self._cancel_order(order_id)
    
    async def _log_order(self, order: dict, side: str, price: Decimal, amount: Decimal):
        """Log order to database for tracking."""
        if not self.db_session:
            return
        
        try:
            # This would insert into bot_trades or orders table
            # Implementation depends on your database schema
            pass
        except Exception as e:
            logger.error(f"❌ Order logging error: {e}", exc_info=True)
