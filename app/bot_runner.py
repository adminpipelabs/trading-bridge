"""
Bot Runner Service
Background service that executes Solana and EVM trading bots (volume and spread bots).
Runs continuously, executing trades based on bot configuration.
"""
import asyncio
import logging
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.database import get_db_session, Bot, BotWallet, BotTrade, Client, Connector
from app.wallet_encryption import decrypt_private_key
from app.solana.jupiter_client import JupiterClient
from app.solana.transaction_signer import SolanaTransactionSigner
from app.evm.chains import get_chain
from app.evm.evm_signer import EVMSigner
from app.evm.uniswap_client import UniswapClient
from circuitbreaker import CircuitBreakerError

logger = logging.getLogger(__name__)

# Initialize Jupiter client and signer (will be created per bot)
# Note: These should be created with proper RPC URL from environment


class BotRunner:
    """Manages running Solana and EVM trading bots"""
    
    def __init__(self):
        self.running_bots: Dict[str, asyncio.Task] = {}
        self.shutdown_event = asyncio.Event()
        logger.info("BotRunner initialized")
    
    async def start(self):
        """Start bot runner - load all running bots from database"""
        logger.info("=" * 80)
        logger.info("STARTING BOT RUNNER SERVICE")
        logger.info("=" * 80)
        
        try:
            db = get_db_session()
            try:
                # Load all bots with status='running'
                running_bots = db.query(Bot).filter(Bot.status == "running").all()
                logger.info(f"Found {len(running_bots)} bot(s) with status='running'")
                
                for bot in running_bots:
                    logger.info(f"  - Bot ID: {bot.id}, Name: {bot.name}, Type: {bot.bot_type}")
                    if bot.bot_type in ['volume', 'spread']:
                        try:
                            await self.start_bot(bot.id, db)
                        except Exception as bot_start_error:
                            # If transaction is aborted, rollback and continue with next bot
                            logger.error(f"❌ Failed to start bot {bot.id}: {bot_start_error}")
                            try:
                                db.rollback()
                            except Exception as rollback_error:
                                logger.error(f"Failed to rollback after bot start error: {rollback_error}")
                            # Continue with next bot instead of crashing entire startup
                            continue
                    else:
                        logger.warning(f"  ⚠️  Skipping bot {bot.id} - unknown bot_type: {bot.bot_type}")
                
                logger.info("=" * 80)
                logger.info("✅ BOT RUNNER SERVICE STARTED")
                logger.info(f"✅ Monitoring {len(self.running_bots)} bot(s)")
                logger.info("=" * 80)
            finally:
                db.close()
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ FAILED TO START BOT RUNNER")
            logger.error(f"Error: {e}")
            logger.error("=" * 80)
            raise
    
    async def start_bot(self, bot_id: str, db: Optional[Session] = None):
        """Start a specific bot"""
        if bot_id in self.running_bots:
            logger.warning(f"Bot {bot_id} is already running")
            return
        
        logger.info(f"🚀 Starting bot {bot_id}...")
        
        # Get bot from database
        if not db:
            db = get_db_session()
            should_close = True
        else:
            should_close = False
        
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                logger.error(f"Bot {bot_id} not found in database")
                return
            
            # Check if this is a CEX bot - CEX bots should NOT be handled by bot_runner
            # They are handled by CEXBotRunner automatically
            from sqlalchemy import text
            exchange = None
            chain = None
            try:
                bot_check = db.execute(text("""
                    SELECT connector, chain FROM bots WHERE id = :bot_id
                """), {"bot_id": bot_id}).first()
                
                if bot_check:
                    exchange = bot_check[0] if len(bot_check) > 0 else None
                    chain = bot_check[1] if len(bot_check) > 1 else None
            except Exception as sql_error:
                # Columns might not exist yet - rollback transaction and continue
                db.rollback()
                logger.warning(f"Could not check connector/chain columns: {sql_error}")
            
            # CEX bot check - check explicit CEX exchanges list
            # IMPORTANT: Chain must NOT be 'solana' for CEX bots
            cex_exchanges = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'okx', 'bybit']
            is_cex_bot = (
                bot.bot_type == 'volume' and 
                exchange and 
                exchange.lower() not in ['jupiter', ''] and
                exchange.lower() in cex_exchanges and
                (not chain or chain.lower() != 'solana')  # Chain must NOT be solana
            )
            
            # Fallback: If exchange is set and chain is explicitly NOT solana
            if not is_cex_bot and exchange and chain and chain.lower() not in ['solana', '']:
                if exchange.lower() not in ['jupiter', 'uniswap', 'pancakeswap']:
                    is_cex_bot = True
            
            if is_cex_bot:
                logger.error(f"❌ Bot {bot_id} is a CEX bot (exchange={exchange}) - should NOT be handled by bot_runner!")
                logger.error(f"   CEX bots are handled by CEXBotRunner automatically.")
                logger.error(f"   This bot should have been routed to CEX runner in bot_routes.py")
                return  # Don't start CEX bots here - CEX runner handles them
            
            # Determine chain (default to solana for backward compatibility)
            config = bot.config or {}
            chain = chain or config.get("chain", "solana")
            
            if bot.bot_type == 'volume':
                if chain == "solana":
                    task = asyncio.create_task(self._run_volume_bot_with_error_handling(bot_id))
                elif chain in ["polygon", "arbitrum", "base", "ethereum"]:
                    task = asyncio.create_task(self._run_evm_volume_bot_with_error_handling(bot_id))
                else:
                    logger.warning(f"Unknown chain '{chain}' for bot {bot_id}, defaulting to solana")
                    task = asyncio.create_task(self._run_volume_bot_with_error_handling(bot_id))
            elif bot.bot_type == 'spread':
                task = asyncio.create_task(self._run_spread_bot_with_error_handling(bot_id))
            else:
                logger.error(f"Unknown bot_type '{bot.bot_type}' for bot {bot_id}")
                return
            
            self.running_bots[bot_id] = task
            logger.info(f"✅ Bot {bot_id} started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start bot {bot_id}: {e}")
            logger.exception(e)
        finally:
            if should_close:
                db.close()
    
    async def stop_bot(self, bot_id: str):
        """Stop a running bot"""
        if bot_id not in self.running_bots:
            logger.warning(f"Bot {bot_id} is not running")
            return
        
        logger.info(f"🛑 Stopping bot {bot_id}...")
        task = self.running_bots[bot_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.running_bots[bot_id]
        logger.info(f"✅ Bot {bot_id} stopped")
    
    async def _run_volume_bot_with_error_handling(self, bot_id: str):
        """Wrapper to catch and log any exceptions in bot loop"""
        try:
            await self._run_volume_bot(bot_id)
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ CRITICAL: Volume bot {bot_id} crashed with unhandled exception")
            logger.error(f"Error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
            # Remove from running bots since it crashed
            if bot_id in self.running_bots:
                del self.running_bots[bot_id]
            # Update bot status in DB
            try:
                db = get_db_session()
                try:
                    bot = db.query(Bot).filter(Bot.id == bot_id).first()
                    if bot:
                        bot.status = "error"
                        bot.error = f"Bot crashed: {str(e)[:200]}"
                        db.commit()
                finally:
                    db.close()
            except Exception as db_error:
                logger.error(f"Failed to update bot status in DB: {db_error}")
    
    async def _run_evm_volume_bot_with_error_handling(self, bot_id: str):
        """Wrapper to catch and log any exceptions in EVM bot loop"""
        try:
            await self._run_evm_volume_bot(bot_id)
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ CRITICAL: EVM volume bot {bot_id} crashed with unhandled exception")
            logger.error(f"Error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
            # Remove from running bots since it crashed
            if bot_id in self.running_bots:
                del self.running_bots[bot_id]
            # Update bot status in DB
            try:
                db = get_db_session()
                try:
                    bot = db.query(Bot).filter(Bot.id == bot_id).first()
                    if bot:
                        bot.status = "error"
                        bot.error = f"Bot crashed: {str(e)[:200]}"
                        db.commit()
                finally:
                    db.close()
            except Exception as db_error:
                logger.error(f"Failed to update bot status in DB: {db_error}")
    
    async def _run_cex_volume_bot(self, bot_id: str, db: Optional[Session] = None):
        """Run CEX volume bot using ccxt (safety net routing)"""
        logger.info(f"🏦 Starting CEX volume bot for {bot_id}")
        
        # Use provided session or create new one
        should_close_db = False
        if db is None:
            db = get_db_session()
            should_close_db = True
        
        try:
            from sqlalchemy import text
            from app.cex_volume_bot import CEXVolumeBot
            import json
            
            # Fetch bot with connector info (API keys)
            # Handle missing exchange column - use connector or bot name fallback
            try:
                # First, get the bot to extract connector name from bot name if needed
                bot_info = db.execute(text("""
                    SELECT b.name, b.connector, b.account
                    FROM bots b
                    WHERE b.id = :bot_id
                """), {"bot_id": bot_id}).first()
                
                if not bot_info:
                    logger.error(f"Bot {bot_id} not found")
                    return
                
                bot_name = bot_info[0] or ''
                bot_connector = bot_info[1] or ''
                bot_account = bot_info[2] or ''
                
                # Extract connector name from bot name if connector field is empty
                connector_name = bot_connector.lower() if bot_connector else ''
                if not connector_name:
                    bot_name_lower = bot_name.lower()
                    cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
                    for kw in cex_keywords:
                        if kw in bot_name_lower:
                            connector_name = kw
                            logger.info(f"Extracted connector '{connector_name}' from bot name '{bot_name}'")
                            break
                
                # Default to 'bitmart' only if we couldn't extract from name
                if not connector_name:
                    connector_name = 'bitmart'
                    logger.warning(f"Could not determine connector for bot '{bot_name}', defaulting to 'bitmart'")
                
                # Now query with the determined connector name
                bot_record = db.execute(text("""
                    SELECT b.*, 
                           c.api_key,
                           c.api_secret,
                           c.memo
                    FROM bots b
                    JOIN clients cl ON cl.account_identifier = b.account
                    LEFT JOIN connectors c ON c.client_id = cl.id 
                        AND LOWER(c.name) = LOWER(:connector_name)
                    WHERE b.id = :bot_id
                """), {"bot_id": bot_id, "connector_name": connector_name}).first()
            except Exception as sql_error:
                # Exchange column doesn't exist - use connector name or bot name fallback
                db.rollback()
                logger.warning(f"exchange column doesn't exist, using connector/bot name fallback: {sql_error}")
                # Get bot first to extract name
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if not bot:
                    logger.error(f"Bot {bot_id} not found")
                    return
                
                # Detect exchange from bot name
                bot_name_lower = (bot.name or "").lower()
                exchange_from_name = "bitmart"  # default
                cex_keywords = ['bitmart', 'binance', 'kucoin', 'coinstore', 'gateio', 'mexc', 'bybit', 'okx']
                for kw in cex_keywords:
                    if kw in bot_name_lower:
                        exchange_from_name = kw
                        break
                
                # Use the extracted connector_name from the try block if available
                if 'connector_name' in locals() and connector_name:
                    exchange_from_name = connector_name
                    logger.info(f"Using connector_name '{connector_name}' extracted from bot name in exception handler")
                
                # Query with connector name matching
                bot_record = db.execute(text("""
                    SELECT b.*, 
                           c.api_key,
                           c.api_secret,
                           c.memo
                    FROM bots b
                    JOIN clients cl ON cl.account_identifier = b.account
                    LEFT JOIN connectors c ON c.client_id = cl.id 
                        AND LOWER(c.name) = LOWER(:exchange_name)
                    WHERE b.id = :bot_id
                """), {"bot_id": bot_id, "exchange_name": exchange_from_name}).first()
                
                # Set connector_name for later use
                connector_name = exchange_from_name
            
            if not bot_record:
                logger.error(f"Bot {bot_id} not found")
                return
            
            # Check if API keys were found - if not, try exchange_credentials table
            api_key = getattr(bot_record, 'api_key', None) if hasattr(bot_record, 'api_key') else (bot_record[8] if len(bot_record) > 8 else None)
            api_secret = getattr(bot_record, 'api_secret', None) if hasattr(bot_record, 'api_secret') else (bot_record[9] if len(bot_record) > 9 else None)
            
            # Check what connector was actually found in the query
            found_connector_name = None
            if hasattr(bot_record, 'name') and hasattr(bot_record, 'connector'):
                # Try to get connector name from the joined connector
                found_connector_name = getattr(bot_record, 'connector', None) if hasattr(bot_record, 'connector') else None
            # Also check if connector was joined (it might be in a different position)
            # The connector name might be in the connectors table result
            
            # If no keys found OR connector name doesn't match what we extracted, check exchange_credentials
            should_check_exchange_creds = (not api_key or not api_secret) or (connector_name and found_connector_name and found_connector_name.lower() != connector_name.lower())
            
            if should_check_exchange_creds:
                logger.warning(f"⚠️  Checking exchange_credentials table for connector '{connector_name}' (found connector: {found_connector_name}, has_keys: {bool(api_key and api_secret)})...")
                # Try exchange_credentials table (encrypted)
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    client = db.query(Client).filter(Client.account_identifier == bot.account).first()
                    if client:
                        from app.cex_volume_bot import decrypt_credential
                        from sqlalchemy import text
                        creds_result = db.execute(text("""
                            SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
                            FROM exchange_credentials
                            WHERE client_id = :client_id AND LOWER(exchange) = LOWER(:exchange_name)
                        """), {"client_id": client.id, "exchange_name": connector_name}).first()
                        
                        if creds_result:
                            try:
                                api_key = decrypt_credential(creds_result[0])
                                api_secret = decrypt_credential(creds_result[1])
                                memo = decrypt_credential(creds_result[2]) if creds_result[2] else None
                                logger.info(f"✅ Found API keys in exchange_credentials table for {connector_name}")
                                # Update bot_record with decrypted keys
                                if hasattr(bot_record, 'api_key'):
                                    bot_record.api_key = api_key
                                    bot_record.api_secret = api_secret
                                    bot_record.memo = memo
                                else:
                                    # bot_record is a tuple/row - create a new one with updated values
                                    bot_record = (*bot_record[:8], api_key, api_secret, memo)
                            except Exception as decrypt_err:
                                logger.error(f"❌ Failed to decrypt credentials: {decrypt_err}")
                        else:
                            logger.warning(f"⚠️  No credentials found in exchange_credentials table for exchange '{connector_name}'")
            
            # DEBUG: Log connector retrieval
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if bot:
                logger.info(f"🔍 DEBUG: bot.account = {bot.account}")
                client = db.query(Client).filter(Client.account_identifier == bot.account).first()
                logger.info(f"🔍 DEBUG: Looking for client with account_identifier = {bot.account}")
                logger.info(f"🔍 DEBUG: Found client = {client}, client.id = {client.id if client else None}")
                if client:
                    from app.database import Connector
                    connector = db.query(Connector).filter(
                        Connector.client_id == client.id,
                        Connector.name == connector_name  # Use extracted connector_name instead of hardcoded 'bitmart'
                    ).first()
                    logger.info(f"🔍 DEBUG: Found connector = {connector}, connector.name = {connector.name if connector else None}")
            
            # Check if API keys exist (re-read after potential exchange_credentials lookup)
            api_key = bot_record.api_key if hasattr(bot_record, 'api_key') else (bot_record[8] if len(bot_record) > 8 else None)
            api_secret = bot_record.api_secret if hasattr(bot_record, 'api_secret') else (bot_record[9] if len(bot_record) > 9 else None)
            
            logger.info(f"🔍 DEBUG: bot_record.api_key present = {bool(api_key)}")
            logger.info(f"🔍 DEBUG: bot_record.api_secret present = {bool(api_secret)}")
            logger.info(f"🔍 DEBUG: Using connector_name = '{connector_name}'")
            
            if not api_key or not api_secret:
                logger.error(f"Bot {bot_id} missing API keys for connector '{connector_name}'")
                logger.error(f"   Checked: connectors table AND exchange_credentials table")
                logger.error(f"   Bot name: {bot.name if bot else 'unknown'}")
                logger.error(f"   Client ID: {client.id if client else 'unknown'}")
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    bot.status = "error"
                    bot.error = f"Missing API keys for {connector_name} - add exchange connector or credentials"
                    db.commit()
                return
            
            # Build symbol
            # Ensure exchange_name is never None - use multiple fallbacks
            exchange_name = None
            if hasattr(bot_record, 'exchange') and bot_record.exchange:
                exchange_name = bot_record.exchange
            elif hasattr(bot_record, 'connector') and bot_record.connector:
                exchange_name = bot_record.connector
            else:
                # Fallback to bot name detection
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot and bot.name:
                    bot_name_lower = bot.name.lower()
                    cex_keywords = ['bitmart', 'binance', 'kucoin', 'coinstore', 'gateio', 'mexc', 'bybit', 'okx']
                    for kw in cex_keywords:
                        if kw in bot_name_lower:
                            exchange_name = kw
                            break
                exchange_name = exchange_name or "bitmart"  # Final fallback
            
            # Ensure it's a string and not None
            if not exchange_name or not isinstance(exchange_name, str):
                exchange_name = "bitmart"
            if hasattr(bot_record, 'base_asset') and hasattr(bot_record, 'quote_asset') and bot_record.base_asset and bot_record.quote_asset:
                symbol = f"{bot_record.base_asset}/{bot_record.quote_asset}"
            elif hasattr(bot_record, 'pair') and bot_record.pair:
                symbol = bot_record.pair.replace("_", "/").replace("-", "/")
            else:
                logger.error(f"Bot {bot_id} missing trading pair")
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    bot.status = "error"
                    bot.error = "Missing trading pair - set base_asset and quote_asset"
                    db.commit()
                return
            
            # Parse config
            config = {}
            if hasattr(bot_record, 'config') and bot_record.config:
                if isinstance(bot_record.config, str):
                    config = json.loads(bot_record.config)
                else:
                    config = bot_record.config
            
            # Create CEX bot instance
            # Proxy URL is read from environment (QUOTAGUARDSTATIC_URL) for IP whitelisting
            # Uses dedicated IP 3.222.129.4 via QuotaGuard
            import os
            proxy_url = os.getenv("QUOTAGUARDSTATIC_URL") or os.getenv("QUOTAGUARD_PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
            
            cex_bot = CEXVolumeBot(
                bot_id=bot_id,
                exchange_name=exchange_name,
                symbol=symbol,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=None,
                memo=bot_record.memo if hasattr(bot_record, 'memo') else None,
                config=config,
                proxy_url=proxy_url,  # Explicitly pass proxy for IP whitelisting
            )
            
            if proxy_url:
                logger.info(f"Bot {bot_id} will use proxy for IP whitelisting: {proxy_url.split('@')[0]}@...")
            else:
                logger.warning(f"⚠️  No proxy URL configured for bot {bot_id} - IP whitelisting may not work")
            
            # Initialize exchange connection
            if not await cex_bot.initialize():
                logger.error(f"Failed to initialize CEX bot {bot_id}")
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    bot.status = "error"
                    bot.error = "Failed to initialize exchange connection"
                    db.commit()
                return
            
            logger.info(f"✅ CEX Volume Bot initialized for {symbol} on {exchange_name}")
            logger.info(f"🔄 Starting trade cycle...")
            
            # Run bot in loop
            while not self.shutdown_event.is_set():
                try:
                    # Check if bot is still running
                    db_check = get_db_session()
                    try:
                        bot = db_check.query(Bot).filter(Bot.id == bot_id).first()
                        if not bot or bot.status != "running":
                            logger.info(f"Bot {bot_id} stopped - exiting CEX bot loop")
                            break
                    finally:
                        db_check.close()
                    
                    # Run single trade cycle
                    result = await cex_bot.run_single_cycle()
                    
                    if result:
                        logger.info(f"Bot {bot_id} trade: {result['side']} ${result['cost_usd']:.2f}")
                        
                        # Update database
                        db_update = get_db_session()
                        try:
                            from datetime import timezone
                            db_update.execute(text("""
                                UPDATE bots SET 
                                    last_trade_time = :now,
                                    health_status = 'healthy',
                                    health_message = :message,
                                    status_updated_at = :now
                                WHERE id = :bot_id
                            """), {
                                "now": datetime.now(timezone.utc),
                                "message": f"Trade executed: {result['side']} ${result['cost_usd']:.2f} | Daily: ${result['daily_volume_total']:.2f}/{result['daily_target']}",
                                "bot_id": bot_id
                            })
                            db_update.commit()
                        except Exception as db_err:
                            logger.warning(f"Could not update bot status: {db_err}")
                        finally:
                            db_update.close()
                    else:
                        # Check if daily target reached
                        if not cex_bot.should_continue():
                            logger.info(f"Bot {bot_id} daily target reached")
                            break
                    
                    # Wait for next interval
                    interval = cex_bot.get_next_interval()
                    await asyncio.sleep(interval)
                    
                except asyncio.CancelledError:
                    logger.info(f"CEX bot {bot_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in CEX bot {bot_id} loop: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(60)  # Wait before retrying
            
            # Cleanup
            await cex_bot.close()
            logger.info(f"CEX bot {bot_id} stopped")
            
        except Exception as e:
            logger.error(f"❌ Failed to start CEX bot {bot_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Update bot status
            try:
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    bot.status = "error"
                    bot.error = f"CEX bot error: {str(e)[:200]}"
                    db.commit()
            except:
                pass
        finally:
            if should_close_db:
                db.close()
    
    async def _run_volume_bot(self, bot_id: str):
        """Route volume bot to correct runner based on exchange type (CEX vs DEX)"""
        logger.info(f"📊 Volume bot {bot_id} starting...")
        
        # CRITICAL: Check if this is a CEX bot BEFORE initializing Jupiter
        # Route CEX bots to CEXVolumeBot, DEX bots to Jupiter
        db = get_db_session()
        exchange = None
        chain = None
        bot = None
        
        try:
            from sqlalchemy import text
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                logger.error(f"Bot {bot_id} not found")
                return
            
            exchange_column_exists = True
            try:
                bot_check = db.execute(text("""
                    SELECT connector, chain FROM bots WHERE id = :bot_id
                """), {"bot_id": bot_id}).first()
                
                if bot_check:
                    exchange = bot_check[0] if len(bot_check) > 0 else None
                    chain = bot_check[1] if len(bot_check) > 1 else None
            except Exception as sql_error:
                # Columns don't exist - use bot name fallback
                exchange_column_exists = False
                logger.warning(f"⚠️  exchange/chain columns don't exist (will use bot name fallback): {sql_error}")
                db.rollback()
            
            # CEX exchanges list (expanded per dev request)
            CEX_EXCHANGES = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'gate', 'mexc', 'bybit', 'okx', 'htx', 'kraken']
            
            # Primary detection: Check if this is a CEX bot from exchange column
            is_cex_bot = (
                exchange and 
                exchange.lower() in CEX_EXCHANGES and
                (not chain or chain.lower() != 'solana')
            )
            
            # Fallback: If exchange column doesn't exist, detect from bot name
            if not is_cex_bot and not exchange_column_exists:
                bot_name = (bot.name or '').lower()
                cex_keywords = ['bitmart', 'binance', 'kucoin', 'coinstore', 'gateio', 'gate', 'mexc', 'bybit', 'okx', 'htx', 'kraken']
                is_cex_from_name = any(kw in bot_name for kw in cex_keywords)
                
                if is_cex_from_name:
                    is_cex_bot = True
                    logger.info(f"✅ Detected CEX bot from name fallback: bot_name='{bot.name}' contains CEX keyword")
            
            if is_cex_bot:
                logger.warning("=" * 80)
                logger.warning(f"⚠️  CEX bot {bot_id} reached _run_volume_bot (should have been caught earlier)")
                logger.warning(f"   Exchange: {exchange}, Chain: {chain}, Bot Name: {bot.name}")
                logger.warning(f"   Routing to CEXVolumeBot as safety net...")
                logger.warning("=" * 80)
                
                # Route to CEX volume bot
                await self._run_cex_volume_bot(bot_id, db)
                return  # Exit - don't initialize Jupiter
        except Exception as check_error:
            logger.error(f"Error checking exchange/chain for bot {bot_id}: {check_error}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
        
        # Create Jupiter client and signer for this bot (only for DEX bots)
        import os
        rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        logger.info(f"  Initializing Jupiter client with RPC: {rpc_url}")
        try:
            jupiter_client = JupiterClient(rpc_url=rpc_url)
            signer = SolanaTransactionSigner(rpc_url=rpc_url)
            logger.info(f"  ✅ Jupiter client and signer initialized")
        except Exception as e:
            logger.error(f"  ❌ Failed to initialize Jupiter client/signer: {e}")
            raise
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    db = get_db_session()
                    try:
                        bot = db.query(Bot).filter(Bot.id == bot_id).first()
                        if not bot or bot.status != "running":
                            logger.info(f"Bot {bot_id} stopped or not found - exiting loop")
                            break
                        
                        config = bot.config or {}
                        logger.info(f"📊 Volume bot {bot_id} - Checking daily target...")
                        
                        # Get daily volume target
                        daily_volume_usd = config.get('daily_volume_usd', 10000)
                        stats = bot.stats or {}
                        volume_today = stats.get('volume_today', 0)
                        
                        logger.info(f"  Target: ${daily_volume_usd:,.2f}, Today: ${volume_today:,.2f}")
                        
                        # Check if daily target reached
                        if volume_today >= daily_volume_usd:
                            logger.info(f"  ✅ Daily target reached - sleeping until midnight")
                            # Sleep until midnight
                            now = datetime.utcnow()
                            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                            sleep_seconds = (midnight - now).total_seconds()
                            await asyncio.sleep(min(sleep_seconds, 3600))  # Max 1 hour sleep
                            continue
                        
                        # Get bot wallets
                        bot_wallets = db.query(BotWallet).filter(BotWallet.bot_id == bot_id).all()
                        if not bot_wallets:
                            logger.error(f"  ❌ No wallets configured for bot {bot_id}")
                            await asyncio.sleep(60)  # Wait 1 minute before retrying
                            continue
                        
                        logger.info(f"  Found {len(bot_wallets)} wallet(s)")
                        
                        # Pick random wallet
                        wallet = random.choice(bot_wallets)
                        logger.info(f"  Using wallet: {wallet.wallet_address[:8]}...")
                        
                        # Decrypt private key
                        try:
                            private_key_raw = decrypt_private_key(wallet.encrypted_private_key)
                            # Log first/last few chars for debugging (don't log full key!)
                            logger.info(f"  ✅ Private key decrypted (length: {len(private_key_raw)}, starts with: {private_key_raw[:4]}..., ends with: ...{private_key_raw[-4:]})")
                            private_key = private_key_raw
                        except Exception as e:
                            logger.error(f"  ❌ Failed to decrypt private key: {e}")
                            await asyncio.sleep(60)
                            continue
                        
                        # Pick random trade size
                        min_trade_usd = config.get('min_trade_usd', 100)
                        max_trade_usd = config.get('max_trade_usd', 500)
                        trade_size_usd = random.uniform(min_trade_usd, max_trade_usd)
                        logger.info(f"  Trade size: ${trade_size_usd:,.2f}")
                        
                        # Determine side (buy or sell)
                        side = "buy" if random.random() > 0.5 else "sell"
                        logger.info(f"  Side: {side}")
                        
                        # Get token mints from config
                        base_mint = config.get('base_mint')
                        quote_mint = config.get('quote_mint', 'So11111111111111111111111111111111111111112')  # SOL
                        
                        if not base_mint:
                            logger.error(f"  ❌ base_mint not configured")
                            await asyncio.sleep(60)
                            continue
                        
                        # Validate wallet address format (must be base58 Solana address)
                        wallet_address = wallet.wallet_address.strip()
                        if not wallet_address or len(wallet_address) < 32:
                            logger.error(f"  ❌ Invalid wallet address format: {wallet_address[:20]}...")
                            await asyncio.sleep(60)
                            continue
                        
                        logger.info(f"  Wallet address: {wallet_address[:8]}...{wallet_address[-8:]}")
                        
                        # Execute swap
                        await self._execute_volume_trade(
                            bot_id=bot_id,
                            wallet_address=wallet_address,
                            private_key=private_key,
                            base_mint=base_mint,
                            quote_mint=quote_mint,
                            trade_size_usd=trade_size_usd,
                            side=side,
                            slippage_bps=config.get('slippage_bps', 50),
                            db=db,
                            jupiter_client=jupiter_client,
                            signer=signer
                        )
                        
                        # Random interval between trades
                        interval_min = config.get('interval_min_seconds', 900)  # 15 min default
                        interval_max = config.get('interval_max_seconds', 2700)  # 45 min default
                        sleep_seconds = random.uniform(interval_min, interval_max)
                        logger.info(f"  💤 Sleeping for {sleep_seconds/60:.1f} minutes...")
                        await asyncio.sleep(sleep_seconds)
                        
                    finally:
                        db.close()
                        
                except asyncio.CancelledError:
                    logger.info(f"Volume bot {bot_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in volume bot {bot_id} loop: {e}")
                    logger.exception(e)
                    await asyncio.sleep(60)  # Wait before retrying
        finally:
            await jupiter_client.close()
            await signer.close()
    
    async def _run_evm_volume_bot(self, bot_id: str):
        """Run EVM volume generation bot using Uniswap"""
        logger.info(f"📊 EVM Volume bot {bot_id} starting main loop...")
        
        db = get_db_session()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                logger.error(f"Bot {bot_id} not found")
                return
            
            config = bot.config or {}
            chain_name = config.get("chain", "polygon")
            
            # Get chain configuration
            try:
                chain_config = get_chain(chain_name)
                logger.info(f"  Initializing Uniswap client for {chain_config.name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to get chain config: {e}")
                return
            
            # Initialize Uniswap client
            try:
                uniswap_client = UniswapClient(chain_config)
                logger.info(f"  ✅ Uniswap client initialized")
            except Exception as e:
                logger.error(f"  ❌ Failed to initialize Uniswap client: {e}")
                return
            
            # Get token addresses
            base_token = config.get("base_token")
            quote_token = config.get("quote_token", chain_config.usdc)  # Default to USDC
            
            if not base_token:
                logger.error(f"  ❌ base_token not configured")
                return
            
            logger.info(f"  Base token: {base_token[:10]}...")
            logger.info(f"  Quote token: {quote_token[:10]}...")
            
        finally:
            db.close()
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    db = get_db_session()
                    try:
                        bot = db.query(Bot).filter(Bot.id == bot_id).first()
                        if not bot or bot.status != "running":
                            logger.info(f"Bot {bot_id} stopped or not found - exiting loop")
                            break
                        
                        config = bot.config or {}
                        logger.info(f"📊 EVM Volume bot {bot_id} - Checking daily target...")
                        
                        # Get daily volume target
                        daily_volume_usd = config.get('daily_volume_usd', 1000)
                        stats = bot.stats or {}
                        volume_today = stats.get('volume_today', 0)
                        
                        logger.info(f"  Target: ${daily_volume_usd:,.2f}, Today: ${volume_today:,.2f}")
                        
                        # Check if daily target reached
                        if volume_today >= daily_volume_usd:
                            logger.info(f"  ✅ Daily target reached - sleeping until midnight")
                            now = datetime.utcnow()
                            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                            sleep_seconds = (midnight - now).total_seconds()
                            await asyncio.sleep(min(sleep_seconds, 3600))
                            continue
                        
                        # Get bot wallets
                        bot_wallets = db.query(BotWallet).filter(BotWallet.bot_id == bot_id).all()
                        if not bot_wallets:
                            logger.error(f"  ❌ No wallets configured for bot {bot_id}")
                            await asyncio.sleep(60)
                            continue
                        
                        logger.info(f"  Found {len(bot_wallets)} wallet(s)")
                        
                        # Pick random wallet
                        wallet = random.choice(bot_wallets)
                        logger.info(f"  Using wallet: {wallet.wallet_address[:8]}...")
                        
                        # Decrypt private key
                        try:
                            private_key_raw = decrypt_private_key(wallet.encrypted_private_key)
                            logger.info(f"  ✅ Private key decrypted")
                            private_key = private_key_raw
                        except Exception as e:
                            logger.error(f"  ❌ Failed to decrypt private key: {e}")
                            await asyncio.sleep(60)
                            continue
                        
                        # Initialize EVM signer
                        try:
                            signer = EVMSigner(chain_config, private_key)
                            logger.info(f"  ✅ EVM signer initialized: {signer.address[:10]}...")
                        except Exception as e:
                            logger.error(f"  ❌ Failed to initialize EVM signer: {e}")
                            await asyncio.sleep(60)
                            continue
                        
                        # Pick random trade size
                        min_trade_usd = config.get('min_trade_usd', 10)
                        max_trade_usd = config.get('max_trade_usd', 50)
                        trade_size_usd = random.uniform(min_trade_usd, max_trade_usd)
                        logger.info(f"  Trade size: ${trade_size_usd:,.2f}")
                        
                        # Determine side (buy or sell)
                        side = "buy" if random.random() > 0.5 else "sell"
                        logger.info(f"  Side: {side}")
                        
                        # Execute trade
                        tx_hash = await self._execute_evm_trade(
                            uniswap_client=uniswap_client,
                            signer=signer,
                            base_token=base_token,
                            quote_token=quote_token,
                            side=side,
                            amount_usd=trade_size_usd,
                            slippage_bps=config.get('slippage_bps', 50),
                        )
                        
                        if tx_hash:
                            # Record trade
                            self._record_trade(
                                bot_id=bot_id,
                                side=side,
                                amount_usd=trade_size_usd,
                                tx_signature=tx_hash,
                                db=db
                            )
                            
                            # Update stats
                            stats = bot.stats or {}
                            stats['volume_today'] = stats.get('volume_today', 0) + trade_size_usd
                            stats['trades_today'] = stats.get('trades_today', 0) + 1
                            stats['last_trade_at'] = datetime.utcnow().isoformat()
                            bot.stats = stats
                            db.commit()
                            
                            logger.info(f"  ✅ Trade complete: {tx_hash[:20]}...")
                            logger.info(f"  📊 Updated stats: ${stats.get('volume_today', 0):,.2f} today")
                        
                        # Random interval between trades
                        interval_min = config.get('interval_min_seconds', 900)
                        interval_max = config.get('interval_max_seconds', 2700)
                        sleep_seconds = random.uniform(interval_min, interval_max)
                        logger.info(f"  💤 Sleeping for {sleep_seconds/60:.1f} minutes...")
                        await asyncio.sleep(sleep_seconds)
                        
                    finally:
                        db.close()
                        
                except asyncio.CancelledError:
                    logger.info(f"EVM volume bot {bot_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in EVM volume bot {bot_id} loop: {e}")
                    logger.exception(e)
                    await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"❌ Fatal error in EVM volume bot {bot_id}: {e}")
            logger.exception(e)
    
    async def _execute_evm_trade(
        self,
        uniswap_client: UniswapClient,
        signer: EVMSigner,
        base_token: str,
        quote_token: str,
        side: str,
        amount_usd: float,
        slippage_bps: int,
    ) -> Optional[str]:
        """Execute single EVM trade via Uniswap"""
        logger.info(f"  🔄 Executing {side} trade...")
        
        try:
            # Get token decimals
            quote_decimals = signer.get_token_decimals(quote_token)
            base_decimals = signer.get_token_decimals(base_token)
            
            if side == "buy":
                # Buy: USDC -> SHARP (or quote -> base)
                amount_in = int(amount_usd * (10 ** quote_decimals))
                token_in = quote_token
                token_out = base_token
                
                logger.info(f"  Buy: ${amount_usd:.2f} = {amount_in} smallest units")
            else:
                # Sell: SHARP -> USDC (or base -> quote)
                # Get quote to determine price
                try:
                    quote = await uniswap_client.get_quote(
                        base_token,
                        quote_token,
                        10 ** base_decimals  # 1 token
                    )
                    token_price_usd = quote.output_amount / (10 ** quote_decimals)
                    
                    # Calculate token amount needed
                    token_amount = amount_usd / token_price_usd
                    amount_in = int(token_amount * (10 ** base_decimals))
                    token_in = base_token
                    token_out = quote_token
                    
                    logger.info(f"  Sell: ${amount_usd:.2f} = {token_amount:.6f} tokens = {amount_in} smallest units")
                    logger.info(f"  Token price: ${token_price_usd:.6f}")
                except CircuitBreakerError as e:
                    logger.error(f"  ❌ Circuit breaker open - Uniswap API unavailable: {e}")
                    return None
                except Exception as e:
                    logger.error(f"  ❌ Failed to get quote: {e}")
                    return None
            
            # Execute swap
            try:
                tx_hash = await uniswap_client.execute_swap(
                    signer=signer,
                    token_in=token_in,
                    token_out=token_out,
                    amount_in=amount_in,
                    slippage_bps=slippage_bps,
                )
                
                logger.info(f"  ✅ Trade successful! TX: {tx_hash}")
                return tx_hash
                
            except CircuitBreakerError as e:
                logger.error(f"  ❌ Circuit breaker open - Uniswap API unavailable: {e}")
                return None
            except Exception as e:
                logger.error(f"  ❌ Trade failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"  ❌ Error executing EVM trade: {e}")
            logger.exception(e)
            return None
    
    async def _execute_volume_trade(
        self,
        bot_id: str,
        wallet_address: str,
        private_key: str,
        base_mint: str,
        quote_mint: str,
        trade_size_usd: float,
        side: str,
        slippage_bps: int,
        db: Session,
        jupiter_client: JupiterClient,
        signer: SolanaTransactionSigner
    ):
        """Execute single Solana volume trade via Jupiter"""
        logger.info(f"  🔄 Executing {side} trade...")
        
        try:
            # Get SOL price for USD conversion
            try:
                sol_price_data = await jupiter_client.get_price(quote_mint, jupiter_client.USDC_MINT)
                sol_price_usd = float(sol_price_data.get('price', 100.0))
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to get SOL price from Jupiter: {e}")
                # Fallback: try to estimate from quote
                try:
                    quote = await jupiter_client.get_quote(
                        input_mint=quote_mint,
                        output_mint=jupiter_client.USDC_MINT,
                        amount=int(1e9),  # 1 SOL
                        slippage_bps=slippage_bps
                    )
                    sol_price_usd = quote.out_amount / 1e6  # USDC has 6 decimals
                except Exception as quote_error:
                    logger.error(f"  ❌ Failed to estimate SOL price: {quote_error}")
                    sol_price_usd = 100.0  # Fallback to $100
            
            if side == "buy":
                # Buy: SOL → Token (quote_mint → base_mint)
                # Calculate SOL amount needed
                sol_amount = trade_size_usd / sol_price_usd
                amount_in = int(sol_amount * 1e9)  # Convert to lamports
                input_mint = quote_mint
                output_mint = base_mint
                
                logger.info(f"  Buy: ${trade_size_usd:.2f} = {sol_amount:.6f} SOL = {amount_in} lamports (SOL price: ${sol_price_usd:.2f})")
            else:
                # Sell: Token → SOL (base_mint → quote_mint)
                # Get token price and calculate amount
                try:
                    # Try to get token price directly from Jupiter price API
                    try:
                        token_price_data = await jupiter_client.get_price(base_mint, jupiter_client.USDC_MINT)
                        token_price_usd = float(token_price_data.get('price', 0))
                    except Exception as price_error:
                        logger.warning(f"  ⚠️ Failed to get token price from API: {price_error}")
                        token_price_usd = 0
                    
                    # If price API failed, estimate from quote
                    if token_price_usd <= 0:
                        # Use quote to estimate price (assume 9 decimals for most Solana tokens)
                        token_decimals = 9
                        try:
                            quote = await jupiter_client.get_quote(
                                input_mint=base_mint,
                                output_mint=jupiter_client.USDC_MINT,
                                amount=int(10 ** token_decimals),  # 1 token
                                slippage_bps=slippage_bps
                            )
                            # Price per token in USDC (USDC has 6 decimals)
                            token_price_usd = quote.out_amount / 1e6
                        except Exception as quote_error:
                            logger.error(f"  ❌ Failed to estimate token price from quote: {quote_error}")
                            return
                    
                    # Calculate token amount needed for USD trade size
                    token_amount = trade_size_usd / token_price_usd
                    
                    # Use 9 decimals (most Solana tokens) - Jupiter will handle if wrong
                    token_decimals = 9
                    amount_in = int(token_amount * (10 ** token_decimals))
                    
                    input_mint = base_mint
                    output_mint = quote_mint
                    
                    logger.info(f"  Sell: ${trade_size_usd:.2f} = {token_amount:.6f} tokens = {amount_in} smallest units")
                    logger.info(f"  Token price: ${token_price_usd:.6f} per token")
                except CircuitBreakerError as e:
                    logger.error(f"  ❌ Circuit breaker open - Jupiter API unavailable: {e}")
                    return
                except Exception as e:
                    logger.error(f"  ❌ Failed to get token price: {e}")
                    logger.exception(e)
                    return
            
            # Get quote
            logger.info(f"  Getting quote: {input_mint[:8]}... → {output_mint[:8]}...")
            logger.info(f"  Amount: {amount_in}")
            
            try:
                quote = await jupiter_client.get_quote(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    amount=amount_in,
                    slippage_bps=slippage_bps
                )
                logger.info(f"  Quote: {quote.in_amount} → {quote.out_amount} (impact: {quote.price_impact_pct:.2f}%)")
            except CircuitBreakerError as e:
                logger.error(f"  ❌ Circuit breaker open - Jupiter API unavailable: {e}")
                return
            except Exception as e:
                logger.error(f"  ❌ Failed to get quote: {e}")
                logger.exception(e)
                return
            
            # Get swap transaction
            logger.info(f"  Getting swap transaction...")
            try:
                swap_tx = await jupiter_client.get_swap_transaction(
                    quote=quote,
                    user_public_key=wallet_address
                )
            except CircuitBreakerError as e:
                logger.error(f"  ❌ Circuit breaker open - Jupiter API unavailable: {e}")
                return
            except Exception as e:
                logger.error(f"  ❌ Failed to get swap transaction: {e}")
                logger.exception(e)
                return
            
            # Sign and send transaction
            logger.info(f"  Signing and sending transaction...")
            try:
                result = await signer.sign_and_send_transaction(
                    transaction_base64=swap_tx.transaction,
                    private_key=private_key
                )
                
                if not result.success:
                    logger.error(f"  ❌ Trade failed: {result.error}")
                    return
                
                signature = result.signature
                logger.info(f"  ✅ Trade successful! Signature: {signature[:20]}...")
                
                # Record trade
                self._record_trade(
                    bot_id=bot_id,
                    side=side,
                    amount_usd=trade_size_usd,
                    tx_signature=signature,
                    db=db
                )
                
                # Update stats
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    stats = bot.stats or {}
                    stats['volume_today'] = stats.get('volume_today', 0) + trade_size_usd
                    stats['trades_today'] = stats.get('trades_today', 0) + 1
                    stats['last_trade_at'] = datetime.utcnow().isoformat()
                    bot.stats = stats
                    db.commit()
                    
                    logger.info(f"  📊 Updated stats: ${stats.get('volume_today', 0):,.2f} today")
                
            except Exception as e:
                logger.error(f"  ❌ Trade execution failed: {e}")
                logger.exception(e)
                return
                
        except Exception as e:
            logger.error(f"  ❌ Error executing volume trade: {e}")
            logger.exception(e)
            return
    
    def _get_volume_today(self, bot_id: str) -> float:
        """Get today's volume for a bot"""
        db = get_db_session()
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                return 0.0
            stats = bot.stats or {}
            return stats.get('volume_today', 0.0)
        finally:
            db.close()
    
    def _record_trade(
        self,
        bot_id: str,
        side: str,
        amount_usd: float,
        tx_signature: str,
        db: Session
    ):
        """Record a trade in the database"""
        trade = BotTrade(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            side=side,
            value_usd=str(amount_usd),
            tx_signature=tx_signature,
            status="success",
            created_at=datetime.utcnow()
        )
        db.add(trade)
        db.commit()
    
    async def _run_spread_bot(self, bot_id: str):
        """Run spread/market making bot"""
        logger.info(f"📈 Spread bot {bot_id} starting main loop...")
        
        while not self.shutdown_event.is_set():
            try:
                db = get_db_session()
                try:
                    bot = db.query(Bot).filter(Bot.id == bot_id).first()
                    if not bot or bot.status != "running":
                        logger.info(f"Bot {bot_id} stopped or not found - exiting loop")
                        break
                    
                    config = bot.config or {}
                    logger.info(f"📈 Spread bot {bot_id} - Refreshing orders...")
                    
                    # TODO: Implement spread bot logic
                    logger.warning(f"  ⚠️  Spread bot logic not yet implemented")
                    
                    # Sleep for refresh interval
                    refresh_seconds = config.get('refresh_seconds', 30)
                    await asyncio.sleep(refresh_seconds)
                    
                finally:
                    db.close()
                    
            except asyncio.CancelledError:
                logger.info(f"Spread bot {bot_id} cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in spread bot {bot_id} loop: {e}")
                logger.exception(e)
                await asyncio.sleep(60)
    
    async def _run_spread_bot_with_error_handling(self, bot_id: str):
        """Wrapper to handle errors in spread bot"""
        try:
            await self._run_spread_bot(bot_id)
        except Exception as e:
            logger.error(f"❌ CRITICAL: Spread bot {bot_id} crashed: {e}")
            logger.exception(e)
            if bot_id in self.running_bots:
                del self.running_bots[bot_id]
    
    def shutdown(self):
        """Shutdown bot runner"""
        logger.info("Shutting down bot runner...")
        self.shutdown_event.set()
        for bot_id in list(self.running_bots.keys()):
            asyncio.create_task(self.stop_bot(bot_id))


# Global instance
bot_runner = BotRunner()
