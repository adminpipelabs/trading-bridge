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

from app.database import get_db_session, Bot, BotWallet, BotTrade
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
                        await self.start_bot(bot.id, db)
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
                    SELECT exchange, chain FROM bots WHERE id = :bot_id
                """), {"bot_id": bot_id}).first()
                
                if bot_check:
                    exchange = bot_check[0] if len(bot_check) > 0 else None
                    chain = bot_check[1] if len(bot_check) > 1 else None
            except Exception as sql_error:
                logger.warning(f"Could not check exchange/chain columns: {sql_error}")
            
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
    
    async def _run_volume_bot(self, bot_id: str):
        """Run Solana volume generation bot - ONLY for DEX bots, NOT CEX"""
        logger.info(f"📊 Volume bot {bot_id} starting main loop...")
        
        # CRITICAL: Check if this is a CEX bot BEFORE initializing Jupiter
        # CEX bots should NEVER reach this function - they're handled by CEXBotRunner
        db = get_db_session()
        try:
            from sqlalchemy import text
            bot_check = db.execute(text("""
                SELECT exchange, chain FROM bots WHERE id = :bot_id
            """), {"bot_id": bot_id}).first()
            
            if bot_check:
                exchange = bot_check[0] if len(bot_check) > 0 else None
                chain = bot_check[1] if len(bot_check) > 1 else None
                
                # CEX exchanges list
                CEX_EXCHANGES = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
                
                # Check if this is a CEX bot
                is_cex_bot = (
                    exchange and 
                    exchange.lower() in CEX_EXCHANGES and
                    (not chain or chain.lower() != 'solana')
                )
                
                if is_cex_bot:
                    logger.error("=" * 80)
                    logger.error(f"❌ CRITICAL ERROR: CEX bot {bot_id} reached _run_volume_bot!")
                    logger.error(f"   Exchange: {exchange}, Chain: {chain}")
                    logger.error(f"   CEX bots should be handled by CEXBotRunner, NOT bot_runner")
                    logger.error(f"   This bot should have been detected in bot_routes.py or start_bot()")
                    logger.error("=" * 80)
                    # Stop the bot - don't try to use Jupiter
                    bot = db.query(Bot).filter(Bot.id == bot_id).first()
                    if bot:
                        bot.status = "error"
                        bot.error = f"Routing error: CEX bot incorrectly routed to Jupiter runner"
                        db.commit()
                    return  # Exit - don't initialize Jupiter
        except Exception as check_error:
            logger.warning(f"Could not check exchange/chain for bot {bot_id}: {check_error}")
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
