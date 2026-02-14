"""
Spread Bot — Two-sided market maker using GTC limit orders.

Each cycle:
1. If no active orders: get mid price, place BUY below and SELL above
2. If orders exist: check if either side filled
3. On fill: cancel the unfilled side, re-quote around new mid
4. On price drift beyond threshold: cancel stale orders, re-quote
5. Otherwise: do nothing, let orders sit
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

        # Active order tracking
        self._buy_order_id: Optional[str] = None
        self._sell_order_id: Optional[str] = None
        self._buy_price: Optional[float] = None
        self._sell_price: Optional[float] = None
        self._last_mid: Optional[float] = None

        # Parse config
        if 'spread_percent' in config:
            self.spread_pct = config['spread_percent'] / 100.0
        elif 'spread_bps' in config:
            self.spread_pct = config['spread_bps'] / 10000.0
        else:
            self.spread_pct = 0.03  # 3% default

        self.order_size_usd = config.get('order_size_usd', config.get('order_size_usdt', 10))
        self.poll_seconds = config.get('poll_interval_seconds', config.get('refresh_seconds',
                            config.get('refresh_interval_seconds', config.get('refresh_interval', 30))))
        self.price_decimals = config.get('price_decimals', 6)
        self.amount_decimals = config.get('amount_decimals', 2)

        # Drift threshold: re-quote if mid moves more than this fraction of spread
        # Default: half the spread — e.g. 0.5% spread, re-quote if mid moves 0.25%
        self.drift_threshold_pct = config.get('drift_threshold_pct', self.spread_pct / 2)

        # ── Safety: circuit breaker ──
        self.circuit_breaker_pct = config.get('circuit_breaker_pct', 30.0)  # Pause if price drops >30%
        self._session_start_price: Optional[float] = None
        self._circuit_breaker_triggered = False

        # ── Volatility-aware spread widening ──
        self._recent_mids: list = []  # Track recent mid prices for volatility calc
        self._max_recent_mids = 60    # ~5 minutes of data at 5s polls
        self._base_spread_pct = self.spread_pct  # Original configured spread
        self._vol_widen_factor = config.get('volatility_widen_factor', 2.0)  # Max spread multiplier

        # ── Stats tracking ──
        self._buy_fills = 0
        self._sell_fills = 0
        self._cycles = 0

        # Detect exchange
        self.exchange_name = ""
        if hasattr(exchange, 'id'):
            self.exchange_name = exchange.id
        elif hasattr(exchange, 'name'):
            self.exchange_name = exchange.name
        elif hasattr(exchange, 'exchange_name'):
            self.exchange_name = exchange.exchange_name
        # Both custom adapters set .id ("coinstore" / "bitmart"), so the
        # detection above via exchange.id / exchange.name is sufficient.

        logger.info(f"SpreadBot {bot_id} created: {symbol} on {self.exchange_name}")
        logger.info(f"  Spread: {self.spread_pct*100:.2f}%, Size: ${self.order_size_usd}, Poll: {self.poll_seconds}s")
        logger.info(f"  Drift threshold: {self.drift_threshold_pct*100:.3f}%, Price decimals: {self.price_decimals}, Amount decimals: {self.amount_decimals}")

    async def start(self):
        """Main loop: poll for fills, re-quote when needed."""
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
                await self._update_health(f"Cycle error: {str(e)[:100]}", status='stale')

            if self._running:
                await asyncio.sleep(self.poll_seconds)

        # Cleanup
        await self._cancel_all()
        logger.info(f"SpreadBot {self.bot_id} stopped, all orders cancelled")

    async def stop(self):
        """Stop the bot and cancel all open orders."""
        logger.info(f"SpreadBot {self.bot_id} stop requested")
        self._running = False
        await self._cancel_all()

    # ── Main cycle ─────────────────────────────────────────────────

    async def _run_cycle(self):
        """Single poll cycle."""
        self._cycles += 1

        # ── CIRCUIT BREAKER ──
        if self._circuit_breaker_triggered:
            # Check if price recovered (every 12 cycles = ~60s)
            if self._cycles % 12 == 0:
                mid = await self._get_mid_price()
                if mid and self._session_start_price:
                    change = ((mid - self._session_start_price) / self._session_start_price) * 100
                    if change >= -(self.circuit_breaker_pct * 0.5):
                        self._circuit_breaker_triggered = False
                        self._session_start_price = mid
                        logger.info(f"SpreadBot {self.bot_id} — circuit breaker reset, price recovered to ${mid:.6f}")
                    else:
                        logger.debug(f"SpreadBot {self.bot_id} — circuit breaker still active ({change:.1f}%)")
            return  # Skip cycle while breaker is active

        # No active orders — place fresh spread
        if not self._buy_order_id and not self._sell_order_id:
            await self._place_spread()
            return

        # Check fills
        buy_filled = False
        sell_filled = False

        if self._buy_order_id:
            buy_filled = await self._is_filled(self._buy_order_id)
        if self._sell_order_id:
            sell_filled = await self._is_filled(self._sell_order_id)

        # Both filled (rare — happened between polls)
        if buy_filled and sell_filled:
            self._buy_fills += 1
            self._sell_fills += 1
            logger.info(f"SpreadBot {self.bot_id} — both sides filled! Re-quoting. (total fills: {self._buy_fills}B/{self._sell_fills}S)")
            self._buy_order_id = None
            self._sell_order_id = None
            await self._place_spread()
            return

        # One side filled — cancel the other, re-quote
        if buy_filled:
            self._buy_fills += 1
            logger.info(f"SpreadBot {self.bot_id} — BUY filled @ {self._buy_price}. Cancelling SELL, re-quoting. (total fills: {self._buy_fills}B/{self._sell_fills}S)")
            await self._cancel_order(self._sell_order_id)
            self._buy_order_id = None
            self._sell_order_id = None
            await self._update_health(f"BUY filled @ {self._buy_price} ({self._buy_fills}B/{self._sell_fills}S)", status='healthy')
            await self._place_spread()
            return

        if sell_filled:
            self._sell_fills += 1
            logger.info(f"SpreadBot {self.bot_id} — SELL filled @ {self._sell_price}. Cancelling BUY, re-quoting. (total fills: {self._buy_fills}B/{self._sell_fills}S)")
            await self._cancel_order(self._buy_order_id)
            self._buy_order_id = None
            self._sell_order_id = None
            await self._update_health(f"SELL filled @ {self._sell_price} ({self._buy_fills}B/{self._sell_fills}S)", status='healthy')
            await self._place_spread()
            return

        # Neither filled — check if price drifted too far
        mid = await self._get_mid_price()
        if mid and self._last_mid:
            drift = abs(mid - self._last_mid) / self._last_mid
            if drift >= self.drift_threshold_pct:
                logger.info(f"SpreadBot {self.bot_id} — mid drifted {drift*100:.3f}% ({self._last_mid:.6f} -> {mid:.6f}), re-quoting")
                await self._cancel_all()
                await self._place_spread()
                return

        # Orders still live, price hasn't drifted. Do nothing.

    # ── Place spread ───────────────────────────────────────────────

    async def _place_spread(self):
        """Get mid price, place BUY and SELL limit orders around it.
        
        Safety features:
        - Circuit breaker: pauses if price drops >X% from session start
        - Volatility-aware spread: widens spread during high volatility
        """
        mid = await self._get_mid_price()
        if not mid:
            logger.warning(f"SpreadBot {self.bot_id} — could not get price, skipping")
            return

        # ── Record session start price for circuit breaker ──
        if self._session_start_price is None:
            self._session_start_price = mid
            logger.info(f"SpreadBot {self.bot_id} — session start price: ${mid:.6f}")

        # ── Circuit breaker check ──
        if self.circuit_breaker_pct > 0 and self._session_start_price > 0:
            change_pct = ((mid - self._session_start_price) / self._session_start_price) * 100
            if change_pct < -self.circuit_breaker_pct:
                if not self._circuit_breaker_triggered:
                    self._circuit_breaker_triggered = True
                    await self._cancel_all()
                    logger.warning(
                        f"🛑 SpreadBot {self.bot_id} CIRCUIT BREAKER: price dropped {change_pct:.1f}% "
                        f"(${self._session_start_price:.6f} → ${mid:.6f}, threshold: -{self.circuit_breaker_pct}%). "
                        f"Orders cancelled, bot paused. Stats: {self._buy_fills} buy fills, {self._sell_fills} sell fills"
                    )
                return

        # ── Volatility-aware spread widening ──
        self._recent_mids.append(mid)
        if len(self._recent_mids) > self._max_recent_mids:
            self._recent_mids = self._recent_mids[-self._max_recent_mids:]

        effective_spread = self._base_spread_pct
        if len(self._recent_mids) >= 10:
            # Calculate recent volatility (std dev of % changes)
            changes = []
            for i in range(1, len(self._recent_mids)):
                if self._recent_mids[i - 1] > 0:
                    changes.append(abs(self._recent_mids[i] - self._recent_mids[i - 1]) / self._recent_mids[i - 1])
            if changes:
                avg_change = sum(changes) / len(changes)
                # If average tick-to-tick change > half the base spread, widen
                if avg_change > self._base_spread_pct / 2:
                    widen_ratio = min(avg_change / (self._base_spread_pct / 2), self._vol_widen_factor)
                    effective_spread = self._base_spread_pct * widen_ratio
                    logger.info(
                        f"SpreadBot {self.bot_id} — volatility widening: "
                        f"base {self._base_spread_pct*100:.2f}% → {effective_spread*100:.2f}% "
                        f"(avg tick change: {avg_change*100:.3f}%)"
                    )

        buy_price = round(mid * (1 - effective_spread / 2), self.price_decimals)
        sell_price = round(mid * (1 + effective_spread / 2), self.price_decimals)
        buy_qty = round(self.order_size_usd / buy_price, self.amount_decimals)
        sell_qty = round(self.order_size_usd / sell_price, self.amount_decimals)

        logger.info(f"SpreadBot {self.bot_id} placing spread:")
        logger.info(f"  Mid: {mid:.6f} | BUY {buy_qty} @ {buy_price} | SELL {sell_qty} @ {sell_price}")

        self._buy_order_id = await self._place_limit_order("buy", buy_qty, buy_price)
        self._sell_order_id = await self._place_limit_order("sell", sell_qty, sell_price)
        self._buy_price = buy_price
        self._sell_price = sell_price
        self._last_mid = mid

        placed = []
        if self._buy_order_id:
            placed.append(f"BUY {buy_qty}@{buy_price}")
        if self._sell_order_id:
            placed.append(f"SELL {sell_qty}@{sell_price}")

        if placed:
            msg = f"Spread live: {', '.join(placed)}"
            await self._update_health(msg, status='healthy')
            logger.info(f"SpreadBot {self.bot_id} — {msg}")
        else:
            await self._update_health("Failed to place orders", status='stale')
            logger.warning(f"SpreadBot {self.bot_id} — no orders placed")

    # ── Price ──────────────────────────────────────────────────────

    async def _get_mid_price(self) -> Optional[float]:
        """Get current mid price for the symbol."""
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            bid = ticker.get("bid")
            ask = ticker.get("ask")
            if bid and ask and bid > 0 and ask > 0:
                return (bid + ask) / 2
            return ticker.get("last") or ticker.get("close")
        except Exception as e:
            logger.error(f"SpreadBot {self.bot_id} — fetch_ticker error: {e}")
            return None

    # ── Fill detection ─────────────────────────────────────────────

    async def _is_filled(self, order_id: str) -> bool:
        """Check if an order has been fully filled."""
        try:
            if self.exchange_name == "coinstore":
                return await self._is_coinstore_order_filled(order_id)
            else:
                order = await self.exchange.fetch_order(order_id, self.symbol)
                status = order.get("status", "")
                return status in ("closed", "filled")
        except Exception as e:
            # If we can't check, assume not filled (safe — we'll check again next cycle)
            logger.debug(f"SpreadBot {self.bot_id} — could not check order {order_id}: {e}")
            return False

    async def _is_coinstore_order_filled(self, order_id: str) -> bool:
        """Check Coinstore order status. If not in active orders, it's filled or cancelled."""
        connector = getattr(self.exchange, 'connector', None) or getattr(self.exchange, '_connector', None)
        if not connector:
            return False

        try:
            coinstore_symbol = self.symbol.replace("/", "")
            result = await connector._request("GET", "/trade/order/active", {"symbol": coinstore_symbol}, authenticated=True)
            active_orders = result.get("data", [])

            # If our order ID is NOT in the active list, it was filled or cancelled
            for o in active_orders:
                if str(o.get("ordId")) == str(order_id):
                    return False  # Still active
            return True  # Not found — filled (or cancelled, but we only cancel explicitly)
        except Exception as e:
            logger.debug(f"SpreadBot {self.bot_id} — Coinstore active orders check failed: {e}")
            return False

    # ── Order placement ────────────────────────────────────────────

    async def _place_limit_order(self, side: str, amount: float, price: float) -> Optional[str]:
        """Place a single LIMIT order. Returns order ID or None."""
        try:
            if self.exchange_name == "coinstore":
                return await self._place_coinstore_limit(side, amount, price)
            else:
                order = await self.exchange.create_limit_order(
                    symbol=self.symbol, side=side, amount=amount, price=price,
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
            connector = getattr(self.exchange, 'connector', None) or getattr(self.exchange, '_connector', None)

            if not connector:
                order = await self.exchange.create_limit_order(self.symbol, side, amount, price)
                order_id = order.get("id") or order.get("orderId") or (order.get("data", {}) or {}).get("ordId")
                logger.info(f"  Coinstore {side.upper()} LIMIT placed: id={order_id}")
                return str(order_id) if order_id else None

            result = await connector.place_order(
                symbol=self.symbol, side=side.lower(), order_type="limit",
                amount=amount, price=price
            )
            logger.info(f"  Coinstore {side.upper()} LIMIT response: {result}")
            code = result.get("code", -1)

            if code == 0 or code == "0":
                order_id = (result.get("data", {}) or {}).get("ordId")
                logger.info(f"  Coinstore {side.upper()} LIMIT placed: id={order_id}")
                return str(order_id) if order_id else None
            else:
                logger.error(f"  Coinstore {side.upper()} LIMIT rejected: code={code}, msg={result.get('message')}")
                return None

        except Exception as e:
            logger.error(f"  Coinstore {side.upper()} LIMIT error: {e}")
            return None

    # ── Cancel orders ──────────────────────────────────────────────

    async def _cancel_order(self, order_id: Optional[str]):
        """Cancel a single order by ID."""
        if not order_id:
            return
        try:
            if self.exchange_name == "coinstore":
                connector = getattr(self.exchange, 'connector', None) or getattr(self.exchange, '_connector', None)
                if connector:
                    await connector._request("POST", "/trade/order/cancel", {"ordId": int(order_id)}, authenticated=True)
                else:
                    await self.exchange.cancel_order(order_id, self.symbol)
            else:
                await self.exchange.cancel_order(order_id, self.symbol)
            logger.debug(f"SpreadBot {self.bot_id} — cancelled order {order_id}")
        except Exception as e:
            logger.debug(f"SpreadBot {self.bot_id} — cancel {order_id} failed (may already be filled): {e}")

    async def _cancel_all(self):
        """Cancel both active orders and clear state."""
        await self._cancel_order(self._buy_order_id)
        await self._cancel_order(self._sell_order_id)
        self._buy_order_id = None
        self._sell_order_id = None
        self._buy_price = None
        self._sell_price = None

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
