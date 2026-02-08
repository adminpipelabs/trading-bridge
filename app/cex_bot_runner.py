"""
CEX Volume Bot Runner
Background task that runs all active CEX volume bots.

Similar to the Solana bot runner pattern.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

from app.cex_volume_bot import CEXVolumeBot, create_bot_from_db

logger = logging.getLogger("cex_bot_runner")


class CEXBotRunner:
    """
    Manages running CEX volume bots.
    
    Runs as a background task, checking for active bots and executing trades.
    """
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.active_bots: Dict[str, CEXVolumeBot] = {}
        self.running = False
    
    async def start(self):
        """Start the bot runner."""
        self.running = True
        logger.info("CEX Bot Runner started")
        
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Bot runner cycle error: {e}", exc_info=True)
            
            # Short sleep between cycles
            await asyncio.sleep(10)
    
    async def stop(self):
        """Stop the bot runner."""
        self.running = False
        
        # Close all active bots
        for bot_id, bot in self.active_bots.items():
            try:
                await bot.close()
            except:
                pass
        
        self.active_bots.clear()
        logger.info("CEX Bot Runner stopped")
    
    async def run_cycle(self):
        """
        Run a single cycle:
        1. Load active CEX bots from database
        2. Initialize any new bots
        3. Execute trades for bots whose interval has elapsed
        4. Clean up stopped bots
        """
        async with self.db_pool.acquire() as conn:
            # Get all running CEX volume bots
            # Use connectors table (where BitMart API keys are stored)
            # NOTE: exchange column may not exist, so detect CEX from bot name as fallback
            try:
                # Try query with exchange column first
                try:
                    bots = await conn.fetch("""
                        SELECT b.*, 
                               c.api_key,
                               c.api_secret,
                               c.memo
                        FROM bots b
                        JOIN clients cl ON cl.account_identifier = b.account
                        JOIN connectors c ON c.client_id = cl.id AND LOWER(c.name) = LOWER(COALESCE(b.exchange, 'bitmart'))
                        WHERE b.status = 'running'
                          AND b.bot_type = 'volume'
                          AND (b.exchange IS NULL OR (b.exchange IS NOT NULL AND b.exchange != 'jupiter'))
                          AND (b.chain IS NULL OR b.chain != 'solana')
                    """)
                except Exception as exchange_col_error:
                    # Exchange column doesn't exist - use bot name fallback
                    logger.warning(f"exchange column doesn't exist, using bot name fallback: {exchange_col_error}")
                    # Get all volume bots and filter by name
                    all_bots = await conn.fetch("""
                        SELECT b.*, 
                               c.api_key,
                               c.api_secret,
                               c.memo
                        FROM bots b
                        JOIN clients cl ON cl.account_identifier = b.account
                        LEFT JOIN connectors c ON c.client_id = cl.id AND LOWER(c.name) = 'bitmart'
                        WHERE b.status = 'running'
                          AND b.bot_type = 'volume'
                    """)
                    # Filter for CEX bots (name contains bitmart, binance, etc.)
                    cex_keywords = ['bitmart', 'binance', 'kucoin', 'coinstore', 'gateio', 'mexc', 'bybit', 'okx']
                    bots = [
                        bot for bot in all_bots 
                        if bot.get("name") and any(kw in bot["name"].lower() for kw in cex_keywords)
                        and bot.get("api_key") and bot.get("api_secret")  # Must have API keys
                    ]
                    logger.info(f"Found {len(bots)} CEX bots using name fallback")
            except Exception as e:
                # If query fails completely, log and skip
                logger.error(f"❌ Could not fetch CEX bots: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return
            
            active_bot_ids = set()
            
            for bot_record in bots:
                bot_id = bot_record["id"]
                active_bot_ids.add(bot_id)
                
                # Initialize new bots
                if bot_id not in self.active_bots:
                    # Use connectors table (API keys are plaintext in connectors, not encrypted)
                    from app.cex_volume_bot import CEXVolumeBot
                    import json
                    
                    # Check if API keys exist
                    if not bot_record.get("api_key") or not bot_record.get("api_secret"):
                        logger.warning(f"Bot {bot_id} missing API keys in connectors table")
                        await conn.execute("""
                            UPDATE bots SET health_status = 'error', 
                                health_message = 'Missing API keys - add BitMart connector'
                            WHERE id = $1
                        """, bot_id)
                        continue
                    
                    # Build symbol from base/quote or pair
                    if bot_record.get("base_asset") and bot_record.get("quote_asset"):
                        symbol = f"{bot_record['base_asset']}/{bot_record['quote_asset']}"
                    else:
                        symbol = bot_record.get("pair", "").replace("_", "/").replace("-", "/")
                    
                    if not symbol:
                        logger.warning(f"Bot {bot_id} missing symbol (need base_asset/quote_asset or pair)")
                        await conn.execute("""
                            UPDATE bots SET health_status = 'error', 
                                health_message = 'Missing trading pair - set base_asset and quote_asset'
                            WHERE id = $1
                        """, bot_id)
                        continue
                    
                    config = bot_record.get("config", {})
                    if isinstance(config, str):
                        config = json.loads(config)
                    
                    # Ensure exchange_name is never None
                    exchange_name = bot_record.get("exchange") or bot_record.get("connector") or "bitmart"
                    if not exchange_name or not isinstance(exchange_name, str):
                        exchange_name = "bitmart"
                    
                    bot = CEXVolumeBot(
                        bot_id=bot_record["id"],
                        exchange_name=exchange_name.lower(),  # Ensure lowercase
                        symbol=symbol,
                        api_key=bot_record["api_key"],  # Plaintext from connectors table
                        api_secret=bot_record["api_secret"],  # Plaintext from connectors table
                        passphrase=None,  # BitMart doesn't use passphrase
                        memo=bot_record.get("memo"),  # BitMart memo/uid from connectors table
                        config=config,
                    )
                    
                    if await bot.initialize():
                        self.active_bots[bot_id] = bot
                        logger.info(f"Initialized CEX bot: {bot_id} ({bot_record.get('name', 'Unknown')})")
                    else:
                        # Mark bot as error
                        await conn.execute("""
                            UPDATE bots SET health_status = 'error', 
                                health_message = 'Failed to initialize exchange connection'
                            WHERE id = $1
                        """, bot_id)
                        continue
                
                bot = self.active_bots.get(bot_id)
                if not bot:
                    continue
                
                # Check if it's time to trade
                last_trade = bot_record.get("last_trade_time")
                interval = bot.get_next_interval()
                
                should_trade = False
                if last_trade is None:
                    should_trade = True
                else:
                    # Handle timezone awareness - ensure UTC
                    try:
                        if last_trade.tzinfo is None:
                            # Naive datetime - make it UTC-aware
                            last_trade = last_trade.replace(tzinfo=timezone.utc)
                        else:
                            # Already timezone-aware - convert to UTC
                            last_trade = last_trade.astimezone(timezone.utc)
                        
                        elapsed = (datetime.now(timezone.utc) - last_trade).total_seconds()
                        should_trade = elapsed >= interval
                    except Exception as e:
                        logger.error(f"Error calculating trade interval for bot {bot_id}: {e}")
                        # If datetime comparison fails, allow trade (safer)
                        should_trade = True
                
                if should_trade:
                    # Execute trade
                    result = await bot.run_single_cycle()
                    
                    if result:
                        # Update database
                        # Convert timezone-aware datetime to naive UTC for PostgreSQL
                        now_utc = datetime.now(timezone.utc)
                        now_naive = now_utc.replace(tzinfo=None)
                        await conn.execute("""
                            UPDATE bots SET 
                                last_trade_time = $1,
                                health_status = 'healthy',
                                health_message = $2,
                                status_updated_at = $1
                            WHERE id = $3
                        """, 
                            now_naive,
                            f"Trade executed: {result['side']} ${result['cost_usd']:.2f} | Daily: ${result['daily_volume_total']:.2f}/{result['daily_target']}",
                            bot_id
                        )
                        
                        # Log trade
                        try:
                            await conn.execute("""
                                INSERT INTO trade_logs (bot_id, side, amount, price, cost_usd, order_id, created_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                                bot_id, result["side"], result["amount"],
                                result["price"], result["cost_usd"], result.get("order_id"),
                                now_naive
                            )
                        except Exception as e:
                            # Table might not exist yet - log but don't fail
                            logger.warning(f"Could not log trade (table may not exist): {e}")
                        
                        logger.info(f"Bot {bot_id} trade: {result['side']} ${result['cost_usd']:.2f}")
                    else:
                        # Check if daily target reached
                        # Convert timezone-aware datetime to naive UTC for PostgreSQL
                        now_utc = datetime.now(timezone.utc)
                        now_naive = now_utc.replace(tzinfo=None)
                        if not bot.should_continue():
                            await conn.execute("""
                                UPDATE bots SET 
                                    health_status = 'healthy',
                                    health_message = 'Daily volume target reached',
                                    status_updated_at = $1
                                WHERE id = $2
                            """, now_naive, bot_id)
                        else:
                            await conn.execute("""
                                UPDATE bots SET 
                                    health_status = 'stale',
                                    health_message = 'Trade skipped — check balance',
                                    status_updated_at = $1
                                WHERE id = $2
                            """, now_naive, bot_id)
            
            # Clean up stopped bots
            stopped_ids = set(self.active_bots.keys()) - active_bot_ids
            for bot_id in stopped_ids:
                bot = self.active_bots.pop(bot_id, None)
                if bot:
                    await bot.close()
                    logger.info(f"Stopped CEX bot: {bot_id}")
