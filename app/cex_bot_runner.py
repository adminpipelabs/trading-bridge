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
            # Check if exchange_credentials table exists
            try:
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'exchange_credentials'
                    )
                """)
                
                if not table_exists:
                    # Table doesn't exist yet - migration not run
                    # Silently skip this cycle (don't spam errors)
                    return
            except Exception as e:
                # If check fails, assume table doesn't exist
                logger.debug(f"Could not check for exchange_credentials table: {e}")
                return
            
            # Get all running CEX volume bots
            try:
                bots = await conn.fetch("""
                    SELECT b.*, ec.api_key_encrypted, ec.api_secret_encrypted, ec.passphrase_encrypted
                    FROM bots b
                    JOIN clients c ON c.account_identifier = b.account
                    JOIN exchange_credentials ec ON ec.client_id = c.id AND ec.exchange = b.exchange
                    WHERE b.status = 'running'
                      AND b.bot_type = 'volume'
                      AND b.exchange IS NOT NULL
                      AND b.exchange != 'jupiter'
                      AND (b.chain IS NULL OR b.chain != 'solana')
                """)
            except Exception as e:
                # If query fails (table doesn't exist), skip silently
                if "exchange_credentials" in str(e).lower() or "does not exist" in str(e).lower():
                    logger.debug(f"exchange_credentials table not found - migration may not have run")
                    return
                else:
                    # Other error - re-raise
                    raise
            
            active_bot_ids = set()
            
            for bot_record in bots:
                bot_id = bot_record["id"]
                active_bot_ids.add(bot_id)
                
                # Initialize new bots
                if bot_id not in self.active_bots:
                    bot = await create_bot_from_db(
                        dict(bot_record),
                        {
                            "api_key_encrypted": bot_record["api_key_encrypted"],
                            "api_secret_encrypted": bot_record["api_secret_encrypted"],
                            "passphrase_encrypted": bot_record.get("passphrase_encrypted"),
                        }
                    )
                    if bot:
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
                    # Handle timezone awareness
                    if last_trade.tzinfo is None:
                        last_trade = last_trade.replace(tzinfo=timezone.utc)
                    
                    elapsed = (datetime.now(timezone.utc) - last_trade).total_seconds()
                    should_trade = elapsed >= interval
                
                if should_trade:
                    # Execute trade
                    result = await bot.run_single_cycle()
                    
                    if result:
                        # Update database
                        await conn.execute("""
                            UPDATE bots SET 
                                last_trade_time = $1,
                                health_status = 'healthy',
                                health_message = $2,
                                status_updated_at = $1
                            WHERE id = $3
                        """, 
                            datetime.now(timezone.utc),
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
                                datetime.now(timezone.utc)
                            )
                        except Exception as e:
                            # Table might not exist yet - log but don't fail
                            logger.warning(f"Could not log trade (table may not exist): {e}")
                        
                        logger.info(f"Bot {bot_id} trade: {result['side']} ${result['cost_usd']:.2f}")
                    else:
                        # Check if daily target reached
                        if not bot.should_continue():
                            await conn.execute("""
                                UPDATE bots SET 
                                    health_status = 'healthy',
                                    health_message = 'Daily volume target reached',
                                    status_updated_at = $1
                                WHERE id = $2
                            """, datetime.now(timezone.utc), bot_id)
                        else:
                            await conn.execute("""
                                UPDATE bots SET 
                                    health_status = 'stale',
                                    health_message = 'Trade skipped — check balance',
                                    status_updated_at = $1
                                WHERE id = $2
                            """, datetime.now(timezone.utc), bot_id)
            
            # Clean up stopped bots
            stopped_ids = set(self.active_bots.keys()) - active_bot_ids
            for bot_id in stopped_ids:
                bot = self.active_bots.pop(bot_id, None)
                if bot:
                    await bot.close()
                    logger.info(f"Stopped CEX bot: {bot_id}")
