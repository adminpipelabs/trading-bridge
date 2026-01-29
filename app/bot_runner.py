"""
Bot Runner Service
Background service that executes Solana trading bots (volume and spread bots).
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

logger = logging.getLogger(__name__)

# Initialize Jupiter client and signer (will be created per bot)
# Note: These should be created with proper RPC URL from environment


class BotRunner:
    """Manages running Solana trading bots"""
    
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
            
            if bot.bot_type == 'volume':
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
    
    async def _run_volume_bot(self, bot_id: str):
        """Run volume generation bot"""
        logger.info(f"📊 Volume bot {bot_id} starting main loop...")
        
        # Create Jupiter client and signer for this bot
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
        """Execute a volume trade (swap)"""
        logger.info(f"  🔄 Executing {side} trade...")
        
        try:
            # Determine input/output based on side
            if side == "buy":
                input_mint = quote_mint  # SOL
                output_mint = base_mint  # Token
            else:
                input_mint = base_mint  # Token
                output_mint = quote_mint  # SOL
            
            # Convert USD to token amount
            if input_mint == quote_mint:  # Buying with SOL
                # Get SOL price in USD
                try:
                    sol_price_data = await jupiter_client.get_price(quote_mint)
                    sol_price_usd = sol_price_data.get("price", 100)  # Fallback to $100
                except Exception as e:
                    logger.error(f"  ❌ Failed to get SOL price: {e}")
                    sol_price_usd = 100  # Use fallback
                
                amount_sol = trade_size_usd / sol_price_usd
                amount = int(amount_sol * 1e9)  # Convert to lamports
                logger.info(f"  Buy: ${trade_size_usd:.2f} = {amount_sol:.6f} SOL = {amount} lamports (SOL price: ${sol_price_usd:.2f})")
            else:
                # Selling token - calculate amount from USD value
                # Get token price (Token/SOL) and SOL price (SOL/USD)
                try:
                    token_price_data = await jupiter_client.get_price(base_mint, quote_mint)
                    token_price = token_price_data.get("price", 0)
                except Exception as e:
                    logger.error(f"  ❌ Failed to get token price for {base_mint}: {e}")
                    return
                
                if token_price == 0:
                    logger.error(f"  ❌ Could not get price for {base_mint} (price is 0)")
                    return
                
                try:
                    sol_price_data = await jupiter_client.get_price(quote_mint)
                    sol_price_usd = sol_price_data.get("price", 100)  # Fallback to $100
                except Exception as e:
                    logger.error(f"  ❌ Failed to get SOL price: {e}")
                    sol_price_usd = 100  # Use fallback
                
                # Calculate token price in USD: (Token/SOL) * (SOL/USD) = Token/USD
                token_price_usd = token_price * sol_price_usd
                
                if token_price_usd == 0:
                    logger.error(f"  ❌ Token price USD is 0 (token_price={token_price}, sol_price_usd={sol_price_usd})")
                    return
                
                # Calculate token amount needed for trade_size_usd
                token_amount = trade_size_usd / token_price_usd
                
                # Convert to smallest units (assume 9 decimals like most Solana tokens)
                token_decimals = 9  # TODO: Fetch from token metadata
                amount = int(token_amount * (10 ** token_decimals))
                
                logger.info(f"  Sell: ${trade_size_usd:.2f} = {token_amount:.6f} tokens = {amount} smallest units")
                logger.info(f"  Token price: {token_price:.8f} {quote_mint[:8]}.../token")
                logger.info(f"  Token price USD: ${token_price_usd:.6f}/token")
            
            logger.info(f"  Getting quote: {input_mint[:8]}... → {output_mint[:8]}...")
            logger.info(f"  Amount: {amount}")
            
            # Get quote from Jupiter
            quote = await jupiter_client.get_quote(
                input_mint=input_mint,
                output_mint=output_mint,
                amount=amount,
                slippage_bps=slippage_bps
            )
            
            if not quote:
                logger.error(f"  ❌ Failed to get quote")
                return
            
            logger.info(f"  Quote: {quote.in_amount} → {quote.out_amount} (impact: {quote.price_impact_pct:.2f}%)")
            
            # Get swap transaction from Jupiter
            logger.info(f"  Getting swap transaction...")
            swap_tx = await jupiter_client.get_swap_transaction(
                quote=quote,
                user_public_key=wallet_address,
                wrap_unwrap_sol=True
            )
            
            if not swap_tx:
                logger.error(f"  ❌ Failed to get swap transaction")
                return
            
            # Sign and send transaction
            logger.info(f"  Signing and sending transaction...")
            result = await signer.sign_and_send_transaction(
                transaction_base64=swap_tx.transaction,
                private_key=private_key,
                skip_preflight=False,
                max_retries=3
            )
            
            if result.success:
                logger.info(f"  ✅ Trade successful! Signature: {result.signature[:16]}...")
                
                # Calculate actual trade value
                actual_value_usd = (quote.out_amount / 1e9) * sol_price_usd if output_mint == quote_mint else trade_size_usd
                
                # Record trade
                trade = BotTrade(
                    id=str(uuid.uuid4()),
                    bot_id=bot_id,
                    wallet_address=wallet_address,
                    side=side,
                    amount=quote.in_amount,
                    price=quote.out_amount / quote.in_amount if quote.in_amount > 0 else 0,
                    value_usd=actual_value_usd,
                    gas_cost=0.000005,  # Approximate SOL gas cost
                    tx_signature=result.signature,
                    status="success",
                    created_at=datetime.utcnow()
                )
                db.add(trade)
                
                # Update bot stats
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    stats = bot.stats or {}
                    stats['volume_today'] = stats.get('volume_today', 0) + actual_value_usd
                    stats['trades_today'] = stats.get('trades_today', 0) + 1
                    stats['last_trade_at'] = datetime.utcnow().isoformat()
                    bot.stats = stats
                    db.commit()
                    logger.info(f"  📊 Updated stats: ${stats['volume_today']:,.2f} today")
            else:
                logger.error(f"  ❌ Trade failed: {result.error}")
                
        except Exception as e:
            logger.error(f"  ❌ Error executing trade: {e}")
            logger.exception(e)
    
    async def _run_spread_bot_with_error_handling(self, bot_id: str):
        """Wrapper to catch and log any exceptions in spread bot loop"""
        try:
            await self._run_spread_bot(bot_id)
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ CRITICAL: Spread bot {bot_id} crashed with unhandled exception")
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
    
    def shutdown(self):
        """Shutdown bot runner"""
        logger.info("Shutting down bot runner...")
        self.shutdown_event.set()
        for bot_id in list(self.running_bots.keys()):
            asyncio.create_task(self.stop_bot(bot_id))


# Global instance
bot_runner = BotRunner()
