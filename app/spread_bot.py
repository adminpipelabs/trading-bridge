"""
Spread Bot — Places LIMIT buy and sell orders around the mid price.

Each cycle:
1. Cancel ALL existing open orders for this symbol
2. Get current mid price
3. Place a BUY limit order at (mid - spread)
4. Place a SELL limit order at (mid + spread)
5. Sleep for refresh_interval_seconds, then repeat

This is cancel-and-replace — no orders are left behind between cycles.
"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class SpreadBot:
    def __init__(self, bot_id: str, exchange, symbol: str, config: dict, db_session=None):
        self.bot_id = bot_id
        self.exchange = exchange
        self.symbol = symbol
        self.config = config
        self.db_session = db_session
        self._running = False
        self._active_order_ids: list[str] = []

        # Parse config
        # spread: support both spread_bps (basis points) and spread_percent
        if 'spread_percent' in config:
            self.spread_pct = config['spread_percent'] / 100.0
        elif 'spread_bps' in config:
            self.spread_pct = config['spread_bps'] / 10000.0
        else:
            self.spread_pct = 0.03  # 3% default

        self.order_size_usd = config.get('order_size_usdt', config.get('order_size_usd', 10))
        self.refresh_seconds = config.get('refresh_interval_seconds', config.get('refresh_seconds', 60))
        self.price_decimals = config.get('price_decimals', 6)
        self.amount_decimals = config.get('amount_decimals', 2)

        # Detect exchange name from the exchange object
        self.exchange_name = ""
        if hasattr(exchange, 'id'):
            self.exchange_name = exchange.id  # ccxt
        elif hasattr(exchange, 'exchange_name'):
            self.exchange_name = exchange.exchange_name
        # Check for coinstore adapter
        if hasattr(exchange, '_connector'):
            self.exchange_name = "coinstore"

        logger.info(f"SpreadBot {bot_id} created: {symbol} on {self.exchange_name}")
        logger.info(f"  Spread: {self.spread_pct*100:.2f}%, Order size: ${self.order_size_usd}")
        logger.info(f"  Refresh: {self.refresh_seconds}s, Price decimals: {self.price_decimals}, Amount decimals: {self.amount_decimals}")

    async def start(self):
        """Main loop: cancel-and-replace each cycle."""
        self._running = True
        logger.info(f"SpreadBot {self.bot_id} starting main loop")

        while self._running:
            try:
                await self._run_cycle()
            except asyncio.CancelledError:
                logger.info(f"SpreadBot {self.bot_id} cancelled")
                break
            except Exception as e:
                logger.error(f"SpreadBot {self.bot_id} cycle error: {e}", exc_info=True)
                # Update health but keep running
                await self._update_health(f"Cycle error: {str(e)[:100]}", status='stale')

            if self._running:
                logger.info(f"SpreadBot {self.bot_id} sleeping {self.refresh_seconds}s")
                await asyncio.sleep(self.refresh_seconds)

        # Final cleanup: cancel all orders when stopping
        await self._cancel_all_orders()
        logger.info(f"SpreadBot {self.bot_id} stopped, all orders cancelled")

    async def stop(self):
        """Stop the bot and cancel all open orders."""
        logger.info(f"SpreadBot {self.bot_id} stop requested")
        self._running = False
        await self._cancel_all_orders()

    async def _run_cycle(self):
        """Single cycle: cancel old orders, get price, place new orders."""

        # Step 1: Cancel ALL open orders for this symbol
        await self._cancel_all_orders()

        # Step 2: Get current mid price
        price = await self._get_mid_price()
        if not price:
            logger.warning(f"SpreadBot {self.bot_id} — could not get price, skipping cycle")
            return

        # Step 3: Calculate buy and sell prices
        buy_price = round(price * (1 - self.spread_pct / 2), self.price_decimals)
        sell_price = round(price * (1 + self.spread_pct / 2), self.price_decimals)

        # Step 4: Calculate quantity from USD size
        buy_qty = round(self.order_size_usd / buy_price, self.amount_decimals)
        sell_qty = round(self.order_size_usd / sell_price, self.amount_decimals)

        logger.info(f"SpreadBot {self.bot_id} placing orders:")
        logger.info(f"  Mid: {price:.6f} | BUY {buy_qty} @ {buy_price} | SELL {sell_qty} @ {sell_price}")

        # Step 5: Place orders (skip balance check — let exchange reject if insufficient)
        buy_order_id = await self._place_limit_order("buy", buy_qty, buy_price)
        sell_order_id = await self._place_limit_order("sell", sell_qty, sell_price)

        placed = []
        if buy_order_id:
            self._active_order_ids.append(buy_order_id)
            placed.append(f"BUY {buy_qty}@{buy_price}")
        if sell_order_id:
            self._active_order_ids.append(sell_order_id)
            placed.append(f"SELL {sell_qty}@{sell_price}")

        if placed:
            msg = f"Orders placed: {', '.join(placed)}"
            await self._update_health(msg, status='healthy')
            logger.info(f"SpreadBot {self.bot_id} — {msg}")
        else:
            await self._update_health("No orders placed this cycle", status='stale')
            logger.warning(f"SpreadBot {self.bot_id} — no orders placed")

    # ── Price ──────────────────────────────────────────────────────

    async def _get_mid_price(self) -> Optional[float]:
        """Get current mid price for the symbol."""
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            # Try bid/ask mid first, fall back to last
            bid = ticker.get("bid")
            ask = ticker.get("ask")
            if bid and ask and bid > 0 and ask > 0:
                return (bid + ask) / 2
            return ticker.get("last") or ticker.get("close")
        except Exception as e:
            logger.error(f"SpreadBot {self.bot_id} — fetch_ticker error: {e}")
            return None

    # ── Order placement ────────────────────────────────────────────

    async def _place_limit_order(self, side: str, amount: float, price: float) -> Optional[str]:
        """Place a single LIMIT order. Returns order ID or None."""
        try:
            if self.exchange_name == "coinstore":
                return await self._place_coinstore_limit(side, amount, price)
            else:
                # ccxt path
                order = await self.exchange.create_limit_order(
                    symbol=self.symbol,
                    side=side,
                    amount=amount,
                    price=price,
                )
                order_id = order.get("id") or order.get("orderId")
                logger.info(f"  {side.upper()} LIMIT placed: id={order_id}")
                return str(order_id) if order_id else None
        except Exception as e:
            logger.error(f"  {side.upper()} LIMIT failed: {e}")
            return None

    async def _place_coinstore_limit(self, side: str, amount: float, price: float) -> Optional[str]:
        """Place a LIMIT order on Coinstore via the connector."""
        try:
            # Coinstore uses its own adapter; get the connector
            connector = None
            if hasattr(self.exchange, '_connector'):
                connector = self.exchange._connector
            elif hasattr(self.exchange, 'connector'):
                connector = self.exchange.connector

            if not connector:
                # Try create_limit_order on the adapter directly
                order = await self.exchange.create_limit_order(self.symbol, side, amount, price)
                order_id = order.get("id") or order.get("orderId") or order.get("data", {}).get("ordId")
                logger.info(f"  Coinstore {side.upper()} LIMIT placed: id={order_id}")
                return str(order_id) if order_id else None

            # Direct connector path
            coinstore_symbol = self.symbol.replace("/", "")  # SHARP/USDT -> SHARPUSDT
            params = {
                "symbol": coinstore_symbol,
                "side": side.upper(),
                "ordType": "LIMIT",
                "ordPrice": str(price),
                "ordQty": str(amount),
                "timestamp": int(time.time() * 1000),
            }

            result = await connector._request("POST", "/trade/order/place", params, authenticated=True)
            code = result.get("code", -1)

            if code == 0:
                order_id = result.get("data", {}).get("ordId")
                logger.info(f"  Coinstore {side.upper()} LIMIT placed: id={order_id}")
                return str(order_id) if order_id else None
            else:
                logger.error(f"  Coinstore {side.upper()} LIMIT rejected: code={code}, msg={result.get('message')}")
                return None

        except Exception as e:
            logger.error(f"  Coinstore {side.upper()} LIMIT error: {e}")
            return None

    # ── Cancel orders ──────────────────────────────────────────────

    async def _cancel_all_orders(self):
        """Cancel ALL open orders for this symbol. Belt-and-suspenders approach."""
        cancelled = 0

        # 1. Cancel tracked order IDs
        for order_id in list(self._active_order_ids):
            try:
                if self.exchange_name == "coinstore":
                    await self._cancel_coinstore_order(order_id)
                else:
                    await self.exchange.cancel_order(order_id, self.symbol)
                cancelled += 1
            except Exception as e:
                logger.debug(f"Cancel order {order_id} failed (may already be filled/cancelled): {e}")
        self._active_order_ids.clear()

        # 2. Fetch and cancel any remaining open orders (catch stragglers)
        try:
            if self.exchange_name == "coinstore":
                await self._cancel_all_coinstore_orders()
            else:
                open_orders = await self.exchange.fetch_open_orders(self.symbol)
                for order in open_orders:
                    try:
                        await self.exchange.cancel_order(order['id'], self.symbol)
                        cancelled += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Fetch open orders failed: {e}")

        if cancelled > 0:
            logger.info(f"SpreadBot {self.bot_id} — cancelled {cancelled} orders")

    async def _cancel_coinstore_order(self, order_id: str):
        """Cancel a single Coinstore order by ID."""
        connector = getattr(self.exchange, '_connector', None) or getattr(self.exchange, 'connector', None)
        if connector:
            await connector._request("POST", "/trade/order/cancel", {"ordId": int(order_id)}, authenticated=True)
        else:
            await self.exchange.cancel_order(order_id, self.symbol)

    async def _cancel_all_coinstore_orders(self):
        """Cancel all open orders on Coinstore for this symbol."""
        connector = getattr(self.exchange, '_connector', None) or getattr(self.exchange, 'connector', None)
        if not connector:
            return

        coinstore_symbol = self.symbol.replace("/", "")
        try:
            result = await connector._request("GET", "/trade/order/active", {"symbol": coinstore_symbol}, authenticated=True)
            orders = result.get("data", [])
            for o in orders:
                oid = o.get("ordId")
                if oid:
                    try:
                        await connector._request("POST", "/trade/order/cancel", {"ordId": oid}, authenticated=True)
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Coinstore fetch open orders failed: {e}")

    # ── Health updates ─────────────────────────────────────────────

    async def _update_health(self, message: str, status: str = 'healthy'):
        """Update bot health in the database."""
        if not self.db_session:
            return
        try:
            from sqlalchemy import text
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db_session.execute(text("""
                UPDATE bots SET
                    health_status = :status,
                    health_message = :msg,
                    status_updated_at = :now
                WHERE id = :bot_id
            """), {"status": status, "msg": message, "now": now, "bot_id": self.bot_id})
            self.db_session.commit()
        except Exception as e:
            logger.debug(f"Failed to update health: {e}")
