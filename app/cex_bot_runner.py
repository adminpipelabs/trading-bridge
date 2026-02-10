"""
CEX Volume Bot Runner
Background task that runs all active CEX volume bots.

Similar to the Solana bot runner pattern.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

from app.cex_volume_bot import CEXVolumeBot, create_bot_from_db, extract_proxy_url_from_quotaguard_info

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
        logger.info(f"🔄 CEX Bot Runner cycle starting - Active bots: {len(self.active_bots)}")
        async with self.db_pool.acquire() as conn:
            # Get all running CEX volume bots
            # Use connectors table (where BitMart API keys are stored)
            # NOTE: exchange column may not exist, so detect CEX from bot name as fallback
            try:
                # Try query with exchange column first
                # Use LEFT JOIN so Coinstore bots (no connectors) are still found
                try:
                    bots = await conn.fetch("""
                        SELECT b.*, 
                               c.api_key,
                               c.api_secret,
                               c.memo,
                               c.name as connector_name,
                               cl.id as client_id,
                               b.exchange as bot_exchange
                        FROM bots b
                        JOIN clients cl ON cl.account_identifier = b.account
                        LEFT JOIN connectors c ON c.client_id = cl.id AND LOWER(c.name) = LOWER(COALESCE(b.connector, 'bitmart'))
                        WHERE b.status = 'running'
                          AND b.bot_type = 'volume'
                          AND (b.connector IS NULL OR (b.connector IS NOT NULL AND b.connector != 'jupiter'))
                          AND (b.chain IS NULL OR b.chain != 'solana')
                    """)
                    # Filter for CEX bots (exclude Jupiter/Solana)
                    bots = [b for b in bots if b.get("connector") != "jupiter" and b.get("chain") != "solana"]
                    logger.info(f"✅ Found {len(bots)} CEX bots from main query")
                    for bot in bots:
                        logger.info(f"   - Bot: {bot.get('id')} | Name: {bot.get('name')} | Exchange: {bot.get('bot_exchange')} | Status: {bot.get('status')}")
                except Exception as exchange_col_error:
                    # Connector column doesn't exist - use bot name fallback
                    logger.warning(f"connector column doesn't exist, using bot name fallback: {exchange_col_error}")
                    # Get all volume bots and filter by name
                    all_bots = await conn.fetch("""
                        SELECT b.*, 
                               c.api_key,
                               c.api_secret,
                               c.memo,
                               c.name as connector_name,
                               cl.id as client_id,
                               cl.account_identifier
                        FROM bots b
                        JOIN clients cl ON cl.account_identifier = b.account
                        LEFT JOIN connectors c ON c.client_id = cl.id
                        WHERE b.status = 'running'
                          AND b.bot_type = 'volume'
                    """)
                    
                    # DEBUG: Log what we found
                    logger.info(f"🔍 DEBUG: Found {len(all_bots)} volume bots before filtering")
                    for bot in all_bots:
                        logger.info(f"🔍 DEBUG: Bot {bot.get('id')} - account={bot.get('account_identifier')}, client_id={bot.get('client_id')}, connector_name={bot.get('connector_name')}, has_api_key={bool(bot.get('api_key'))}")
                    
                    # Filter for CEX bots (name contains bitmart, binance, etc.)
                    cex_keywords = ['bitmart', 'binance', 'kucoin', 'coinstore', 'gateio', 'mexc', 'bybit', 'okx']
                    bots = []
                    for bot in all_bots:
                        bot_name_lower = (bot.get("name") or "").lower()
                        is_cex_bot = any(kw in bot_name_lower for kw in cex_keywords)
                        has_keys = bot.get("api_key") and bot.get("api_secret")
                        connector_name = (bot.get("connector_name") or "").lower()
                        
                        logger.info(f"🔍 DEBUG: Bot {bot.get('id')} - is_cex={is_cex_bot}, has_keys={has_keys}, connector_name={connector_name}")
                        
                        if is_cex_bot:
                            # Extract expected exchange from bot name
                            expected_exchange = None
                            for kw in cex_keywords:
                                if kw in bot_name_lower:
                                    expected_exchange = kw
                                    break
                            
                            # Accept CEX bots even if keys don't match - we'll check exchange_credentials during initialization
                            # This allows bots like "SHARP-VB-Coinstore" to pass through even if they have BitMart keys
                            if not connector_name or connector_name == expected_exchange or expected_exchange in connector_name:
                                bots.append(bot)
                                logger.info(f"✅ Added bot {bot.get('id')} - connector '{connector_name}' matches exchange '{expected_exchange}'")
                            else:
                                # Connector doesn't match, but still add - will check exchange_credentials during init
                                logger.warning(f"⚠️  Bot {bot.get('id')} has connector '{connector_name}' but expected '{expected_exchange}' - will check exchange_credentials during init")
                                bots.append(bot)
                                logger.info(f"✅ Added bot {bot.get('id')} - will check exchange_credentials for '{expected_exchange}'")
                    
                    logger.info(f"Found {len(bots)} CEX bots using name fallback")
            except Exception as e:
                # If query fails completely, log and skip
                logger.error(f"❌ Could not fetch CEX bots: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return
            
            active_bot_ids = set()
            
            logger.info(f"📋 Processing {len(bots)} bot(s)...")
            for bot_record in bots:
                bot_id = bot_record["id"]
                bot_name = bot_record.get("name", "Unknown")
                active_bot_ids.add(bot_id)
                
                logger.info(f"🔍 Processing bot: {bot_id} ({bot_name})")
                logger.info(f"   Account: {bot_record.get('account')}")
                logger.info(f"   Exchange: {bot_record.get('bot_exchange')} | Connector: {bot_record.get('connector')}")
                logger.info(f"   Has API key: {bool(bot_record.get('api_key'))} | Has secret: {bool(bot_record.get('api_secret'))}")
                
                # Initialize new bots
                if bot_id not in self.active_bots:
                    logger.info(f"🔄 Bot {bot_id} not in active_bots - Initializing...")
                    # Use connectors table (API keys are plaintext in connectors, not encrypted)
                    from app.cex_volume_bot import CEXVolumeBot
                    import json
                    
                    # Determine expected exchange - check multiple sources
                    connector_name = (bot_record.get("connector_name") or bot_record.get("connector") or "").lower()
                    bot_name_lower = (bot_record.get("name") or "").lower()
                    
                    # Priority: 1) connector field, 2) extract from bot name, 3) use connector_name as-is
                    expected_exchange = None
                    cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
                    
                    # First, check if connector_name is already a valid exchange
                    if connector_name and connector_name in cex_keywords:
                        expected_exchange = connector_name
                        logger.info(f"✅ Bot {bot_id} - Using connector '{connector_name}' as exchange")
                    else:
                        # Extract from bot name as fallback
                        for kw in cex_keywords:
                            if kw in bot_name_lower:
                                expected_exchange = kw
                                logger.info(f"✅ Bot {bot_id} - Extracted exchange '{kw}' from bot name")
                                break
                        # If still not found, use connector_name if it exists
                        if not expected_exchange and connector_name:
                            expected_exchange = connector_name
                            logger.info(f"✅ Bot {bot_id} - Using connector '{connector_name}' as exchange (fallback)")
                    
                    # Check if API keys exist and if connector matches expected exchange
                    api_key = bot_record.get("api_key")
                    api_secret = bot_record.get("api_secret")
                    memo = bot_record.get("memo")
                    
                    # For Coinstore, ALWAYS check exchange_credentials first (not connectors)
                    # For other exchanges, check exchange_credentials if keys missing or connector doesn't match
                    client_id = bot_record.get("client_id")
                    if expected_exchange == "coinstore" or (not api_key or not api_secret) or (expected_exchange and connector_name and connector_name != expected_exchange):
                        if expected_exchange and client_id:
                            if expected_exchange == "coinstore":
                                logger.info(f"🔍 Bot {bot_id} - Coinstore bot, checking exchange_credentials table...")
                            else:
                                logger.warning(f"⚠️  Bot {bot_id} - connector '{connector_name}' doesn't match expected '{expected_exchange}' or missing keys, checking exchange_credentials...")
                            # Query exchange_credentials table
                            if client_id:
                                # Try exact match first
                                creds_result = await conn.fetchrow("""
                                    SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
                                    FROM exchange_credentials
                                    WHERE client_id = $1 AND LOWER(exchange) = LOWER($2)
                                """, client_id, expected_exchange)
                                
                                # If not found, try connector_name as fallback
                                if not creds_result and connector_name and connector_name != expected_exchange:
                                    logger.info(f"🔍 Bot {bot_id} - Trying connector_name '{connector_name}' as exchange...")
                                    creds_result = await conn.fetchrow("""
                                        SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
                                        FROM exchange_credentials
                                        WHERE client_id = $1 AND LOWER(exchange) = LOWER($2)
                                    """, client_id, connector_name)
                                
                                if creds_result:
                                    try:
                                        from app.security import decrypt_credential
                                        api_key = decrypt_credential(creds_result["api_key_encrypted"])
                                        api_secret = decrypt_credential(creds_result["api_secret_encrypted"])
                                        memo = decrypt_credential(creds_result["passphrase_encrypted"]) if creds_result.get("passphrase_encrypted") else None
                                        logger.info(f"✅ Found API keys in exchange_credentials table for {expected_exchange}")
                                        # Update bot_record with decrypted keys
                                        bot_record["api_key"] = api_key
                                        bot_record["api_secret"] = api_secret
                                        bot_record["memo"] = memo
                                        # Clear health error status since we found credentials
                                        await conn.execute("""
                                            UPDATE bots SET 
                                                health_status = NULL,
                                                health_message = NULL,
                                                error = NULL
                                            WHERE id = $1
                                        """, bot_id)
                                        logger.info(f"✅ Cleared health error for bot {bot_id} - credentials found")
                                    except Exception as decrypt_err:
                                        logger.error(f"❌ Failed to decrypt credentials: {decrypt_err}")
                                        api_key = None
                                        api_secret = None
                                else:
                                    # Log detailed debug info
                                    logger.warning(f"⚠️  No credentials found in exchange_credentials table")
                                    logger.warning(f"   Bot ID: {bot_id}")
                                    logger.warning(f"   Client ID: {client_id}")
                                    logger.warning(f"   Expected exchange: {expected_exchange}")
                                    logger.warning(f"   Connector name: {connector_name}")
                                    logger.warning(f"   Bot name: {bot_record.get('name')}")
                                    
                                    # Check what credentials exist for this client
                                    all_creds = await conn.fetch("""
                                        SELECT exchange FROM exchange_credentials WHERE client_id = $1
                                    """, client_id)
                                    if all_creds:
                                        logger.warning(f"   Available exchanges for this client: {[c['exchange'] for c in all_creds]}")
                                    else:
                                        logger.warning(f"   No credentials found for client_id: {client_id}")
                    
                    # Final check if API keys exist
                    if not api_key or not api_secret:
                        logger.warning(f"Bot {bot_id} missing API keys (checked connectors and exchange_credentials)")
                        logger.warning(f"   Bot name: {bot_record.get('name')}")
                        logger.warning(f"   Connector: {connector_name}")
                        logger.warning(f"   Expected exchange: {expected_exchange}")
                        logger.warning(f"   Client ID: {client_id}")
                        
                        # Set error status but DON'T stop the bot - let user fix via Edit button
                        await conn.execute("""
                            UPDATE bots SET 
                                health_status = 'error', 
                                health_message = 'Missing API keys - add connector or exchange credentials',
                                status = 'stopped'
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
                    # Try to detect from bot name if exchange column doesn't exist
                    exchange_name = bot_record.get("exchange") or bot_record.get("connector")
                    if not exchange_name or not isinstance(exchange_name, str):
                        # Fallback: detect from bot name
                        bot_name_lower = (bot_record.get("name") or "").lower()
                        cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
                        exchange_name = "bitmart"  # default
                        for kw in cex_keywords:
                            if kw in bot_name_lower:
                                exchange_name = kw
                                break
                    
                    exchange_name = exchange_name.lower()
                    
                    # Proxy URL is read from environment (QUOTAGUARDSTATIC_URL) for IP whitelisting
                    # Uses dedicated IP 3.222.129.4 via QuotaGuard
                    import os
                    raw_proxy = os.getenv("QUOTAGUARDSTATIC_URL") or os.getenv("QUOTAGUARD_PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
                    
                    # Extract actual URL if QuotaGuard connection info format
                    if raw_proxy:
                        proxy_url = extract_proxy_url_from_quotaguard_info(raw_proxy) or raw_proxy
                        if proxy_url != raw_proxy:
                            logger.info(f"🔍 Extracted proxy URL from QuotaGuard connection info")
                    else:
                        proxy_url = None
                    
                    # Debug logging for proxy configuration
                    if proxy_url:
                        logger.info(f"✅ Found proxy URL: {proxy_url.split('@')[0] if '@' in proxy_url else proxy_url[:20]}...")
                    else:
                        logger.warning(f"⚠️  No proxy URL found! Checked: QUOTAGUARDSTATIC_URL={bool(os.getenv('QUOTAGUARDSTATIC_URL'))}, QUOTAGUARD_PROXY_URL={bool(os.getenv('QUOTAGUARD_PROXY_URL'))}, HTTP_PROXY={bool(os.getenv('HTTP_PROXY'))}, HTTPS_PROXY={bool(os.getenv('HTTPS_PROXY'))}")
                    
                    bot = CEXVolumeBot(
                        bot_id=bot_record["id"],
                        exchange_name=exchange_name.lower(),  # Ensure lowercase
                        symbol=symbol,
                        api_key=bot_record["api_key"],  # Plaintext from connectors table
                        api_secret=bot_record["api_secret"],  # Plaintext from connectors table
                        passphrase=None,  # BitMart doesn't use passphrase
                        memo=bot_record.get("memo"),  # BitMart memo/uid from connectors table
                        config=config,
                        proxy_url=proxy_url,  # Explicitly pass proxy for IP whitelisting
                    )
                    
                    if proxy_url:
                        logger.info(f"Bot {bot_record['id']} will use proxy for IP whitelisting: {proxy_url.split('@')[0]}@...")
                    else:
                        logger.warning(f"⚠️  No proxy URL configured for bot {bot_record['id']} - IP whitelisting may not work")
                    
                    logger.info(f"🔄 Attempting to initialize CEX bot: {bot_id} ({bot_record.get('name', 'Unknown')})")
                    init_result = await bot.initialize()
                    if init_result:
                        self.active_bots[bot_id] = bot
                        logger.info(f"✅ SUCCESS: Initialized CEX bot: {bot_id} ({bot_record.get('name', 'Unknown')}) - Bot is now active")
                    else:
                        logger.error(f"❌ FAILED: Could not initialize CEX bot: {bot_id} ({bot_record.get('name', 'Unknown')}) - check logs above for initialization errors")
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
                
                # Ensure bot is initialized before using it
                if bot_id not in self.active_bots:
                    logger.warning(f"Bot {bot_id} not in active_bots - skipping cycle (initialization may have failed)")
                    continue
                
                bot = self.active_bots.get(bot_id)
                if not bot:
                    logger.warning(f"⚠️  Bot {bot_id} is None in active_bots - skipping cycle (initialization may have failed)")
                    continue
                
                logger.info(f"✅ Bot {bot_id} is active and ready - Checking if should trade...")
                
                # Check if it's time to trade
                last_trade = bot_record.get("last_trade_time")
                interval = bot.get_next_interval()
                
                logger.info(f"🔍 Bot {bot_id} - Checking trade timing: last_trade={last_trade}, interval={interval}s ({interval/60:.1f} min)")
                
                should_trade = False
                if last_trade is None:
                    should_trade = True
                    logger.info(f"✅ Bot {bot_id} - First trade (no last_trade_time) - WILL TRADE NOW")
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
                        logger.info(f"🔍 Bot {bot_id} - Elapsed: {elapsed:.0f}s / {interval}s - {'WILL TRADE' if should_trade else 'WAITING'}")
                    except Exception as e:
                        logger.error(f"Error calculating trade interval for bot {bot_id}: {e}")
                        # If datetime comparison fails, allow trade (safer)
                        should_trade = True
                        logger.info(f"✅ Bot {bot_id} - Interval calculation error - WILL TRADE (safer)")
                
                if should_trade:
                    # Execute trade
                    logger.info(f"🔄 EXECUTING TRADE NOW - Bot {bot_id} - Interval elapsed, calling run_single_cycle()")
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
