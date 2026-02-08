"""
Bot Health Monitor Service
Runs periodic health checks on all bots marked as "running" by verifying
recent trade activity on the exchange via ccxt.

Add to: trading-bridge/app/bot_health.py
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import ccxt.async_support as ccxt
from app.solana_health import SolanaHealthChecker

logger = logging.getLogger("bot_health")

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

HEALTH_CHECK_INTERVAL_SECONDS = 300     # Check every 5 minutes
STALE_THRESHOLD_MINUTES = 30            # No trades in 30 min → stale
STOPPED_THRESHOLD_MINUTES = 120         # No trades in 2 hours → stopped
HEARTBEAT_TIMEOUT_MINUTES = 15          # No heartbeat in 15 min → stale


class BotHealthMonitor:
    """
    Monitors bot health by checking recent trade activity on exchanges.
    
    Logic:
    1. Every HEALTH_CHECK_INTERVAL, query all bots with status='running'
    2. For each bot, check recent trades on the exchange via ccxt
    3. If trades found recently → healthy
    4. If no trades within STALE_THRESHOLD → stale (might be normal in low-vol)
    5. If no trades within STOPPED_THRESHOLD → mark as stopped
    6. Log all transitions to bot_health_logs
    """

    def __init__(self, db_pool):
        """
        Args:
            db_pool: asyncpg connection pool (or whatever DB driver you use)
        """
        self.db_pool = db_pool
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._exchange_cache = {}  # client_id → ccxt exchange instance
        self.solana_checker = SolanaHealthChecker()

    # ──────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────

    async def start(self):
        """Start the background health check loop."""
        if self._running:
            logger.warning("Health monitor already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(
            f"Bot health monitor started "
            f"(interval={HEALTH_CHECK_INTERVAL_SECONDS}s, "
            f"stale={STALE_THRESHOLD_MINUTES}m, "
            f"stopped={STOPPED_THRESHOLD_MINUTES}m)"
        )

    async def stop(self):
        """Stop the background health check loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Close all cached exchange connections
        for exchange in self._exchange_cache.values():
            try:
                await exchange.close()
            except Exception:
                pass
        self._exchange_cache.clear()
        # Close Solana checker
        await self.solana_checker.close()
        logger.info("Bot health monitor stopped")

    # ──────────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────────

    async def _health_check_loop(self):
        """Run health checks on a fixed interval."""
        while self._running:
            try:
                await self._run_health_checks()
            except Exception as e:
                # Don't crash the app if health checks fail (e.g., missing tables)
                error_msg = str(e)
                if "does not exist" in error_msg or "UndefinedTableError" in error_msg:
                    logger.warning(
                        f"Health check skipped - database tables not ready: {error_msg}. "
                        "Run migrations/add_bot_health_tracking.sql to enable health monitoring."
                    )
                else:
                    logger.error(f"Health check cycle failed: {e}", exc_info=True)
            await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    async def _run_health_checks(self):
        """Check all bots that claim to be running."""
        async with self.db_pool.acquire() as conn:
            # Get all bots marked as running (by user action)
            # Include chain and wallet info for Solana routing
            bots = await conn.fetch("""
                SELECT b.id, b.account, b.name, b.pair, b.base_asset, b.quote_asset, b.base_mint,
                       b.connector, b.exchange, b.status,
                       b.health_status, b.last_trade_time, b.last_heartbeat,
                       b.bot_type, b.chain, b.config,
                       c.api_key, c.api_secret, c.memo,
                       w.address as wallet_address
                FROM bots b
                LEFT JOIN clients cl ON cl.account_identifier = b.account
                LEFT JOIN connectors c ON c.client_id = cl.id 
                    AND (LOWER(c.name) = LOWER(COALESCE(b.exchange, b.connector)) 
                         OR (b.exchange IS NULL AND b.connector IS NULL))
                LEFT JOIN wallets w ON w.client_id = cl.id
                WHERE b.reported_status = 'running' OR b.status = 'running'
            """)

            logger.info(f"Health check: {len(bots)} bots to verify")

            for bot in bots:
                try:
                    # Route to appropriate checker based on chain
                    chain = (bot.get('chain') or '').lower()
                    connector = (bot.get('connector') or '').lower()
                    exchange = (bot.get('exchange') or '').lower()

                    # CEX bots (BitMart, etc.) go to regular health check
                    # Solana/Jupiter bots go to Solana-specific check
                    if chain == 'solana' or connector == 'jupiter' or exchange == 'jupiter':
                        await self._check_solana_bot_health(conn, bot)
                    elif exchange and exchange not in ['', 'jupiter']:
                        # CEX bot - check health via exchange API
                        await self._check_bot_health(conn, bot)
                    elif connector and connector not in ['', 'jupiter']:
                        # Legacy connector-based bot
                        await self._check_bot_health(conn, bot)
                    else:
                        # Unknown bot type - mark as error
                        await self._update_health(
                            conn, bot['id'], bot['status'],
                            health_status='error',
                            new_status=None,
                            reason="Unknown bot type - missing exchange/connector"
                        )
                except Exception as e:
                    logger.error(
                        f"Health check failed for bot {bot['id']} "
                        f"({bot['name']}): {e}"
                    )
                    await self._update_health(
                        conn, bot['id'], bot['status'],
                        health_status='error',
                        new_status=None,
                        reason=f"Health check error: {str(e)}"
                    )

    # ──────────────────────────────────────────────────────────
    # Solana bot health check
    # ──────────────────────────────────────────────────────────

    async def _check_solana_bot_health(self, conn, bot):
        """
        Check health of a Solana/Jupiter bot using on-chain data.
        """
        bot_id = bot['id']
        wallet_address = bot.get('wallet_address')
        config_raw = bot.get('config') or {}
        
        # Handle config as string (JSONB from PostgreSQL might be returned as string)
        if isinstance(config_raw, str):
            import json
            try:
                config = json.loads(config_raw)
            except (json.JSONDecodeError, TypeError):
                config = {}
        elif isinstance(config_raw, dict):
            config = config_raw
        else:
            config = {}

        # Config stores base_mint and quote_mint for Jupiter bots
        # Also check column directly (for newer bots that have base_mint column)
        base_mint = bot.get('base_mint') or config.get('base_mint')
        quote_mint = bot.get('quote_mint') or config.get('quote_mint')

        if not wallet_address:
            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='error',
                new_status=None,
                reason="No wallet address found for Solana bot"
            )
            return

        if not base_mint:
            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='error',
                new_status=None,
                reason="Bot missing pair configuration (no base_mint found in column or config)"
            )
            return

        # Run Solana health check
        try:
            result = await self.solana_checker.check_health(
                wallet_address=wallet_address,
                base_mint=base_mint,
                quote_mint=quote_mint,
                stale_minutes=STALE_THRESHOLD_MINUTES,
                stopped_minutes=STOPPED_THRESHOLD_MINUTES,
            )
        except Exception as e:
            logger.error(f"Solana health check failed for bot {bot_id}: {e}", exc_info=True)
            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='error',
                new_status=None,
                reason=f"Health check error: {str(e)[:100]}"
            )
            return

        # Validate result structure
        if not result or not isinstance(result, dict):
            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='error',
                new_status=None,
                reason="Health check returned invalid result"
            )
            return

        health_status = result.get('health_status', 'unknown')
        reason = result.get('reason', 'Unknown reason')

        # Map health to display status
        new_status = None
        if health_status == 'healthy':
            new_status = 'running'
        elif health_status == 'stopped':
            new_status = 'stopped'
        # 'stale' keeps current status

        # Safely get transactions data
        # Handle case where transactions might be a string (JSON) or dict
        transactions_raw = result.get('transactions', {})
        if isinstance(transactions_raw, str):
            import json
            try:
                transactions = json.loads(transactions_raw)
            except (json.JSONDecodeError, TypeError):
                transactions = {}
        elif isinstance(transactions_raw, dict):
            transactions = transactions_raw
        else:
            transactions = {}
        
        # Ensure transactions is a dict before calling .get()
        if not isinstance(transactions, dict):
            logger.warning(f"Transactions data is not a dict for bot {bot_id}: {type(transactions)}")
            transactions = {}
        
        last_trade = transactions.get('last_tx_time') if isinstance(transactions, dict) else None
        trade_count = transactions.get('count', 0) if isinstance(transactions, dict) else 0

        await self._update_health(
            conn, bot_id, bot['status'],
            health_status=health_status,
            new_status=new_status,
            reason=reason,
            trade_count=trade_count,
            last_trade=last_trade
        )

        logger.info(
            f"Solana bot {bot_id} ({bot['name']}): "
            f"{health_status} — {reason}"
        )

    # ──────────────────────────────────────────────────────────
    # Individual bot check
    # ──────────────────────────────────────────────────────────

    async def _check_bot_health(self, conn, bot):
        """
        Check a single bot's health by looking at recent trades
        and wallet balance.
        """
        now = datetime.now(timezone.utc)
        bot_id = bot['id']
        
        # Get pair from column OR config JSON (for backward compatibility)
        pair = bot.get('pair')
        config_raw = bot.get('config') or {}
        
        # Parse config if it's a string (JSONB from PostgreSQL)
        if isinstance(config_raw, str):
            import json
            try:
                config = json.loads(config_raw)
            except (json.JSONDecodeError, TypeError):
                config = {}
        elif isinstance(config_raw, dict):
            config = config_raw
        else:
            config = {}
        
        # Check config JSON for pair/token_mint if column is empty
        if not pair:
            # Try to get pair from config
            pair = config.get('pair') or config.get('token_mint')
            # Or build from base_asset/quote_asset
            if not pair and config.get('base_asset') and config.get('quote_asset'):
                pair = f"{config['base_asset']}/{config['quote_asset']}"
        
        connector = bot.get('connector') # e.g. "BitMart"

        # Validate required fields
        if not pair:
            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='error',
                new_status=None,
                reason="Bot missing pair configuration"
            )
            return

        # ── Check heartbeat first (if bot pushes heartbeats) ──
        if bot['last_heartbeat']:
            # Handle both timezone-aware and naive datetimes
            heartbeat = bot['last_heartbeat']
            if heartbeat.tzinfo is None:
                # Naive datetime - make it UTC-aware
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            else:
                # Already timezone-aware - ensure UTC
                heartbeat = heartbeat.astimezone(timezone.utc)
            heartbeat_age = now - heartbeat
            if heartbeat_age < timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES):
                await self._update_health(
                    conn, bot_id, bot['status'],
                    health_status='healthy',
                    new_status='running',
                    reason=f"Heartbeat received {heartbeat_age.seconds}s ago"
                )
                return

        # ── Get exchange connection ──
        exchange = await self._get_exchange(bot)
        if not exchange:
            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='unknown',
                new_status=None,
                reason="No exchange credentials available"
            )
            return

        # ── Check recent trades on exchange ──
        trades = None
        try:
            since_ms = int((now - timedelta(hours=3)).timestamp() * 1000)
            trades = await exchange.fetch_my_trades(pair, since=since_ms, limit=50)
        except Exception as e:
            logger.warning(f"Could not fetch trades for bot {bot_id}: {e}")

        # ── Check wallet balance ──
        balance_info = await self._check_balance(exchange, pair)

        # ── Evaluate: trades first, then balance for diagnosis ──
        if trades:
            last_trade_time = datetime.fromtimestamp(
                trades[-1]['timestamp'] / 1000, tz=timezone.utc
            )
            time_since_last = now - last_trade_time
            trade_count = len(trades)

            if time_since_last < timedelta(minutes=STALE_THRESHOLD_MINUTES):
                # Recent trades → healthy
                # But still warn if balance is getting low
                reason = f"{trade_count} trades in last 3h, latest {time_since_last.seconds // 60}m ago"
                health = 'healthy'
                if balance_info and balance_info['low_balance']:
                    reason += f" ⚠️ LOW BALANCE: {balance_info['summary']}"
                    health = 'healthy'  # Still healthy but message warns

                await self._update_health(
                    conn, bot_id, bot['status'],
                    health_status=health,
                    new_status='running',
                    reason=reason,
                    trade_count=trade_count,
                    last_trade=last_trade_time
                )
            elif time_since_last < timedelta(minutes=STOPPED_THRESHOLD_MINUTES):
                # No recent trades → check if balance is the reason
                if balance_info and balance_info['no_funds']:
                    reason = (
                        f"NO FUNDS — {balance_info['summary']}. "
                        f"Bot cannot trade. Last trade: {last_trade_time.isoformat()}"
                    )
                    await self._update_health(
                        conn, bot_id, bot['status'],
                        health_status='stopped',
                        new_status='stopped',
                        reason=reason,
                        trade_count=trade_count,
                        last_trade=last_trade_time
                    )
                else:
                    await self._update_health(
                        conn, bot_id, bot['status'],
                        health_status='stale',
                        new_status='running',
                        reason=f"No trades in {time_since_last.seconds // 60}m (last: {last_trade_time.isoformat()})",
                        trade_count=trade_count,
                        last_trade=last_trade_time
                    )
            else:
                # No trades beyond threshold
                reason = f"No trades in {time_since_last.total_seconds() // 3600:.1f}h"
                if balance_info and balance_info['no_funds']:
                    reason = f"NO FUNDS — {balance_info['summary']}. {reason}"
                elif balance_info and balance_info['low_balance']:
                    reason = f"LOW BALANCE — {balance_info['summary']}. {reason}"
                else:
                    reason += " — bot appears stopped"

                await self._update_health(
                    conn, bot_id, bot['status'],
                    health_status='stopped',
                    new_status='stopped',
                    reason=reason,
                    trade_count=trade_count,
                    last_trade=last_trade_time
                )
        else:
            # No trades at all in 3 hours
            reason = "No trades found in last 3 hours"
            if balance_info and balance_info['no_funds']:
                reason = f"NO FUNDS — {balance_info['summary']}. {reason}"
            elif balance_info and balance_info['low_balance']:
                reason = f"LOW BALANCE — {balance_info['summary']}. {reason}"
            else:
                reason += " — bot appears stopped"

            await self._update_health(
                conn, bot_id, bot['status'],
                health_status='stopped',
                new_status='stopped',
                reason=reason,
                trade_count=0,
                last_trade=None
            )

    # ──────────────────────────────────────────────────────────
    # Balance checking
    # ──────────────────────────────────────────────────────────

    async def _check_balance(self, exchange, pair: str) -> Optional[dict]:
        """
        Check if the wallet has sufficient balance to trade the given pair.
        Returns balance info dict or None if check failed.
        
        For a pair like SHARP/USDT:
          - base = SHARP (need this to sell)
          - quote = USDT (need this to buy)
          - If both are ~0, bot can't do anything
        """
        try:
            # BitMart requires type parameter - pass it explicitly
            connector_name = (bot.get('exchange') or bot.get('connector') or '').lower()
            if connector_name == 'bitmart':
                balance = await exchange.fetch_balance({'type': 'spot'})
            else:
                balance = await exchange.fetch_balance()
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")
            return None

        # Parse pair → base/quote
        if not pair:
            return None
        parts = pair.split('/')
        if len(parts) != 2:
            return None
        base, quote = parts

        base_free = float(balance.get(base, {}).get('free', 0) or 0)
        quote_free = float(balance.get(quote, {}).get('free', 0) or 0)
        base_total = float(balance.get(base, {}).get('total', 0) or 0)
        quote_total = float(balance.get(quote, {}).get('total', 0) or 0)

        # Thresholds — adjust per pair
        # For USDT quote, $1 is effectively nothing
        QUOTE_MIN = 1.0    # Minimum quote currency to place buys
        BASE_MIN = 0.001   # Minimum base currency (very small, varies by token)

        no_funds = (quote_free < QUOTE_MIN and base_free < BASE_MIN)
        low_balance = (quote_free < QUOTE_MIN * 10 or base_free < BASE_MIN * 10)

        summary = f"{base}: {base_free:.4f} free ({base_total:.4f} total), {quote}: {quote_free:.2f} free ({quote_total:.2f} total)"

        return {
            'base': base,
            'quote': quote,
            'base_free': base_free,
            'quote_free': quote_free,
            'base_total': base_total,
            'quote_total': quote_total,
            'no_funds': no_funds,
            'low_balance': low_balance,
            'summary': summary,
        }

    # ──────────────────────────────────────────────────────────
    # Database updates
    # ──────────────────────────────────────────────────────────

    async def _update_health(
        self, conn, bot_id: int, previous_status: str,
        health_status: str, new_status: Optional[str],
        reason: str, trade_count: int = 0,
        last_trade: Optional[datetime] = None
    ):
        """Update bot health in DB and log the check."""
        now = datetime.now(timezone.utc)
        
        # Convert timezone-aware datetime to naive for PostgreSQL compatibility
        # PostgreSQL TIMESTAMP columns don't store timezone info
        now_naive = now.replace(tzinfo=None) if now.tzinfo else now
        last_trade_naive = None
        if last_trade:
            last_trade_naive = last_trade.replace(tzinfo=None) if last_trade.tzinfo else last_trade

        try:
            # Update bots table (health columns may not exist if migration not run)
            if new_status and new_status != previous_status:
                await conn.execute("""
                    UPDATE bots 
                    SET health_status = $1,
                        status = $2,
                        last_trade_time = COALESCE($3, last_trade_time),
                        status_updated_at = $4,
                        health_message = $5
                    WHERE id = $6
                """, health_status, new_status, last_trade_naive, now_naive, reason, bot_id)
                logger.warning(
                    f"Bot {bot_id} status changed: {previous_status} → {new_status} "
                    f"(health: {health_status}, reason: {reason})"
                )
            else:
                await conn.execute("""
                    UPDATE bots 
                    SET health_status = $1,
                        last_trade_time = COALESCE($2, last_trade_time),
                        health_message = $3
                    WHERE id = $4
                """, health_status, last_trade_naive, reason, bot_id)
        except Exception as e:
            # Health columns may not exist - log but don't fail
            if "does not exist" in str(e) or "column" in str(e).lower():
                logger.debug(f"Health columns not available (migration not run): {e}")
                return
            raise

        # Log the health check (table may not exist)
        try:
            await conn.execute("""
                INSERT INTO bot_health_logs 
                    (bot_id, previous_status, new_status, health_status, reason,
                     trade_count_since_last, last_trade_found)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, bot_id, previous_status, new_status or previous_status,
                health_status, reason, trade_count, last_trade_naive)
        except Exception as e:
            # bot_health_logs table may not exist - log but don't fail
            if "does not exist" in str(e) or "UndefinedTableError" in str(e):
                logger.debug(f"bot_health_logs table not available (migration not run): {e}")
                return
            raise

    # ──────────────────────────────────────────────────────────
    # Exchange connection management
    # ──────────────────────────────────────────────────────────

    async def _get_exchange(self, bot) -> Optional[ccxt.Exchange]:
        """Get or create a ccxt exchange instance for a bot's connector."""
        cache_key = bot['account']

        if cache_key in self._exchange_cache:
            return self._exchange_cache[cache_key]

        if not bot['api_key'] or not bot['api_secret']:
            return None

        # Use exchange field if available (for CEX bots), otherwise fall back to connector
        connector_name = (bot.get('exchange') or bot.get('connector') or '').lower()

        # Map connector names to ccxt exchange classes
        exchange_map = {
            'bitmart': ccxt.bitmart,
            'binance': ccxt.binance,
            'kucoin': ccxt.kucoin,
            'gate': ccxt.gateio,
            'gateio': ccxt.gateio,
        }

        exchange_class = exchange_map.get(connector_name)
        if not exchange_class:
            logger.warning(f"Unknown exchange: {connector_name}")
            return None

        config = {
            'apiKey': bot['api_key'],
            'secret': bot['api_secret'],
            'enableRateLimit': True,
        }
        
        # BitMart requires defaultType option (spot, margin, futures)
        # Without this, ccxt calls .lower() on None account type → crash
        if connector_name == 'bitmart':
            config['options'] = {
                'defaultType': 'spot'  # REQUIRED - prevents NoneType.lower() error
            }
        
        # Add proxy if configured (for QuotaGuard static IP)
        import os
        proxy_url = os.getenv("QUOTAGUARD_PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if proxy_url:
            config['proxies'] = {
                'http': proxy_url,
                'https': proxy_url,
            }
        
        if bot['memo']:
            config['uid'] = bot['memo']  # BitMart uses memo/uid

        exchange = exchange_class(config)
        self._exchange_cache[cache_key] = exchange
        return exchange

    # ──────────────────────────────────────────────────────────
    # Heartbeat receiver (for push-based monitoring)
    # ──────────────────────────────────────────────────────────

    async def receive_heartbeat(self, bot_id: int, metadata: dict = None):
        """
        Called when a bot sends a heartbeat.
        Can be triggered via webhook endpoint.
        """
        async with self.db_pool.acquire() as conn:
            heartbeat_time = datetime.now(timezone.utc)
            # Convert to naive datetime for PostgreSQL compatibility
            heartbeat_naive = heartbeat_time.replace(tzinfo=None) if heartbeat_time.tzinfo else heartbeat_time
            await conn.execute("""
                UPDATE bots 
                SET last_heartbeat = $1,
                    health_status = 'healthy',
                    health_message = 'Heartbeat received'
                WHERE id = $2
            """, heartbeat_naive, bot_id)
            logger.debug(f"Heartbeat received for bot {bot_id}")

    # ──────────────────────────────────────────────────────────
    # Manual status check (on-demand)
    # ──────────────────────────────────────────────────────────

    async def check_bot_now(self, bot_id: int) -> dict:
        """
        Run an immediate health check on a specific bot.
        Returns the health result.
        """
        async with self.db_pool.acquire() as conn:
            bot = await conn.fetchrow("""
                SELECT b.id, b.account, b.name, b.pair, b.connector, b.status,
                       b.health_status, b.last_trade_time, b.last_heartbeat,
                       c.api_key, c.api_secret, c.memo
                FROM bots b
                LEFT JOIN connectors c ON c.client_id = (
                    SELECT cl.id FROM clients cl 
                    WHERE cl.account_identifier = b.account
                )
                WHERE b.id = $1
            """, bot_id)

            if not bot:
                return {"error": "Bot not found"}

            await self._check_bot_health(conn, bot)

            # Return updated status
            updated = await conn.fetchrow("""
                SELECT status, health_status, health_message, 
                       last_trade_time, last_heartbeat, status_updated_at
                FROM bots WHERE id = $1
            """, bot_id)

            return dict(updated) if updated else {"error": "Update failed"}
