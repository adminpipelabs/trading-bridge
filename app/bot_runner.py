"""
Bot Runner Service - Executes Solana bots continuously.
Runs VolumeBot and SpreadBot logic in background tasks.
"""

import asyncio
import logging
import random
import time
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.database import Bot, BotWallet, BotTrade, get_db_session
from app.wallet_encryption import decrypt_private_key
import httpx

logger = logging.getLogger(__name__)

# Trading Bridge URL (for calling our own endpoints)
TRADING_BRIDGE_URL = os.getenv("TRADING_BRIDGE_URL", "https://trading-bridge-production.up.railway.app")


class BotRunner:
    """Manages running Solana bots"""
    
    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the bot runner - loads all running bots"""
        logger.info("Starting bot runner service...")
        
        # Load all bots with status='running'
        db = get_db_session()
        try:
            running_bots = db.query(Bot).filter(
                Bot.status == "running",
                Bot.bot_type.in_(["volume", "spread"])
            ).all()
            
            for bot in running_bots:
                await self.start_bot(bot.id, db)
            
            logger.info(f"Bot runner started - monitoring {len(running_bots)} bots")
        except Exception as e:
            logger.error(f"Failed to start bot runner: {e}")
        finally:
            db.close()
    
    async def start_bot(self, bot_id: str, db: Optional[Session] = None):
        """Start a specific bot"""
        if bot_id in self.running_tasks:
            logger.warning(f"Bot {bot_id} is already running")
            return
        
        if not db:
            db = get_db_session()
        
        try:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                logger.error(f"Bot {bot_id} not found")
                return
            
            if bot.bot_type == "volume":
                task = asyncio.create_task(self.run_volume_bot(bot_id))
            elif bot.bot_type == "spread":
                task = asyncio.create_task(self.run_spread_bot(bot_id))
            else:
                logger.error(f"Unknown bot type: {bot.bot_type}")
                return
            
            self.running_tasks[bot_id] = task
            logger.info(f"Started bot {bot_id} ({bot.bot_type})")
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
        finally:
            if not db:
                db.close()
    
    async def stop_bot(self, bot_id: str):
        """Stop a specific bot"""
        if bot_id in self.running_tasks:
            self.running_tasks[bot_id].cancel()
            try:
                await self.running_tasks[bot_id]
            except asyncio.CancelledError:
                pass
            del self.running_tasks[bot_id]
            logger.info(f"Stopped bot {bot_id}")
    
    async def run_volume_bot(self, bot_id: str):
        """Run VolumeBot - executes swaps at intervals"""
        logger.info(f"VolumeBot {bot_id} started")
        
        while not self.shutdown_event.is_set():
            try:
                db = get_db_session()
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                
                if not bot or bot.status != "running":
                    logger.info(f"VolumeBot {bot_id} stopped (status changed)")
                    break
                
                # Check if daily target reached
                stats = bot.stats or {}
                volume_today = stats.get("volume_today", 0)
                daily_target = bot.config.get("daily_volume_usd", 0)
                
                if volume_today >= daily_target:
                    # Wait until midnight
                    await self.sleep_until_midnight()
                    # Reset stats
                    stats["volume_today"] = 0
                    stats["trades_today"] = 0
                    bot.stats = stats
                    db.commit()
                    continue
                
                # Get wallets
                wallets = db.query(BotWallet).filter(BotWallet.bot_id == bot_id).all()
                if not wallets:
                    logger.error(f"No wallets configured for bot {bot_id}")
                    await asyncio.sleep(60)  # Wait 1 minute before retry
                    db.close()
                    continue
                
                # Pick random wallet
                wallet = random.choice(wallets)
                private_key = decrypt_private_key(wallet.encrypted_private_key)
                
                # Pick random trade size
                min_trade = bot.config.get("min_trade_usd", 100)
                max_trade = bot.config.get("max_trade_usd", 500)
                size_usd = random.uniform(min_trade, max_trade)
                
                # Alternate buy/sell
                side = "buy" if random.random() > 0.5 else "sell"
                
                # Execute swap
                result = await self.execute_swap(
                    bot=bot,
                    wallet=wallet,
                    private_key=private_key,
                    size_usd=size_usd,
                    side=side
                )
                
                # Update stats
                if result.get("success"):
                    stats["volume_today"] = stats.get("volume_today", 0) + size_usd
                    stats["trades_today"] = stats.get("trades_today", 0) + 1
                    stats["last_trade_at"] = datetime.utcnow().isoformat()
                    bot.stats = stats
                    db.commit()
                
                # Random interval
                min_interval = bot.config.get("interval_min_seconds", 900)
                max_interval = bot.config.get("interval_max_seconds", 2700)
                interval = random.uniform(min_interval, max_interval)
                
                db.close()
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info(f"VolumeBot {bot_id} cancelled")
                break
            except Exception as e:
                logger.error(f"VolumeBot {bot_id} error: {e}")
                await asyncio.sleep(60)  # Wait before retry
                if db:
                    db.close()
    
    async def run_spread_bot(self, bot_id: str):
        """Run SpreadBot - places bid/ask orders around current price"""
        logger.info(f"SpreadBot {bot_id} started")
        
        while not self.shutdown_event.is_set():
            try:
                db = get_db_session()
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                
                if not bot or bot.status != "running":
                    logger.info(f"SpreadBot {bot_id} stopped (status changed)")
                    break
                
                # Get wallet (spread bot uses single wallet)
                wallets = db.query(BotWallet).filter(BotWallet.bot_id == bot_id).all()
                if not wallets:
                    logger.error(f"No wallet configured for bot {bot_id}")
                    await asyncio.sleep(60)
                    db.close()
                    continue
                
                wallet = wallets[0]
                private_key = decrypt_private_key(wallet.encrypted_private_key)
                
                # Cancel existing orders first
                await self.cancel_all_orders(wallet.wallet_address, private_key, bot.config)
                
                # Get current price
                price = await self.get_current_price(bot.config)
                
                if not price:
                    logger.warning(f"Could not get price for bot {bot_id}")
                    await asyncio.sleep(30)
                    db.close()
                    continue
                
                # Calculate bid/ask
                spread_bps = bot.config.get("spread_bps", 50)
                bid_price = price * (1 - spread_bps / 20000)
                ask_price = price * (1 + spread_bps / 20000)
                
                # Convert USD to token amount
                order_size_usd = bot.config.get("order_size_usd", 500)
                base_amount = await self.usd_to_token_amount(order_size_usd, bot.config.get("base_mint"), price)
                
                # Place spread orders
                result = await self.place_spread_orders(
                    bot=bot,
                    wallet=wallet,
                    private_key=private_key,
                    base_amount=base_amount,
                    spread_bps=spread_bps,
                    expire_seconds=bot.config.get("expire_seconds", 3600)
                )
                
                # Update stats
                if result.get("success"):
                    stats = bot.stats or {}
                    stats["orders_placed"] = stats.get("orders_placed", 0) + 2
                    stats["last_refresh_at"] = datetime.utcnow().isoformat()
                    bot.stats = stats
                    db.commit()
                
                # Wait for refresh interval
                refresh_seconds = bot.config.get("refresh_seconds", 30)
                db.close()
                await asyncio.sleep(refresh_seconds)
                
            except asyncio.CancelledError:
                logger.info(f"SpreadBot {bot_id} cancelled")
                break
            except Exception as e:
                logger.error(f"SpreadBot {bot_id} error: {e}")
                await asyncio.sleep(30)
                if db:
                    db.close()
    
    async def execute_swap(self, bot: Bot, wallet: BotWallet, private_key: str, size_usd: float, side: str) -> dict:
        """Execute a swap via trading-bridge /solana/swap endpoint"""
        try:
            config = bot.config
            base_mint = config.get("base_mint")
            quote_mint = config.get("quote_mint")
            slippage_bps = config.get("slippage_bps", 50)
            
            # Get current price to convert USD to token amount
            price = await self.get_current_price(config)
            if not price:
                return {"success": False, "error": "Could not get price"}
            
            # Determine input/output based on side
            if side == "buy":
                input_mint = quote_mint  # SOL
                output_mint = base_mint  # TOKEN
                amount = int(size_usd / price * 1e9)  # Convert SOL USD to lamports
            else:
                input_mint = base_mint  # TOKEN
                output_mint = quote_mint  # SOL
                # Need token decimals - assume 9 for now
                amount = int(size_usd / price * 1e9)  # Convert token USD to smallest units
            
            # Call trading-bridge swap endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TRADING_BRIDGE_URL}/solana/swap",
                    json={
                        "wallet_address": wallet.wallet_address,
                        "private_key": private_key,
                        "input_mint": input_mint,
                        "output_mint": output_mint,
                        "amount": amount,
                        "slippage_bps": slippage_bps
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Record trade
                    await self.record_trade(bot.id, wallet.wallet_address, side, size_usd, price, result.get("signature"))
                    return {"success": True, **result}
                else:
                    error = response.json().get("detail", "Swap failed")
                    logger.error(f"Swap failed: {error}")
                    return {"success": False, "error": error}
                    
        except Exception as e:
            logger.error(f"Execute swap error: {e}")
            return {"success": False, "error": str(e)}
    
    async def place_spread_orders(self, bot: Bot, wallet: BotWallet, private_key: str, base_amount: int, spread_bps: int, expire_seconds: int) -> dict:
        """Place spread orders via trading-bridge /solana/spread-orders endpoint"""
        try:
            config = bot.config
            base_mint = config.get("base_mint")
            quote_mint = config.get("quote_mint")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TRADING_BRIDGE_URL}/solana/spread-orders",
                    json={
                        "wallet_address": wallet.wallet_address,
                        "private_key": private_key,
                        "base_mint": base_mint,
                        "quote_mint": quote_mint,
                        "base_amount": base_amount,
                        "spread_bps": spread_bps,
                        "expire_in_seconds": expire_seconds
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"success": True, **response.json()}
                else:
                    error = response.json().get("detail", "Spread orders failed")
                    logger.error(f"Spread orders failed: {error}")
                    return {"success": False, "error": error}
                    
        except Exception as e:
            logger.error(f"Place spread orders error: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_all_orders(self, wallet_address: str, private_key: str, config: dict):
        """Cancel all open orders"""
        try:
            base_mint = config.get("base_mint")
            quote_mint = config.get("quote_mint")
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{TRADING_BRIDGE_URL}/solana/cancel-all-orders",
                    json={
                        "wallet_address": wallet_address,
                        "private_key": private_key,
                        "input_mint": base_mint,
                        "output_mint": quote_mint
                    },
                    timeout=10.0
                )
        except Exception as e:
            logger.warning(f"Failed to cancel orders: {e}")
    
    async def get_current_price(self, config: dict) -> Optional[float]:
        """Get current price from Jupiter"""
        try:
            base_mint = config.get("base_mint")
            quote_mint = config.get("quote_mint")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{TRADING_BRIDGE_URL}/solana/price",
                    params={
                        "token_mint": base_mint,
                        "vs_token": quote_mint
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("price")
                return None
        except Exception as e:
            logger.error(f"Get price error: {e}")
            return None
    
    async def usd_to_token_amount(self, usd_amount: float, token_mint: str, price: float) -> int:
        """Convert USD amount to token amount (in smallest units)"""
        # Assume 9 decimals for now (can be improved with token metadata)
        token_amount = usd_amount / price
        return int(token_amount * 1e9)
    
    async def record_trade(self, bot_id: str, wallet_address: str, side: str, value_usd: float, price: float, tx_signature: Optional[str]):
        """Record a trade in bot_trades table"""
        try:
            db = get_db_session()
            trade = BotTrade(
                id=str(uuid.uuid4()),
                bot_id=bot_id,
                wallet_address=wallet_address,
                side=side,
                amount=None,  # Could calculate from value_usd / price
                price=price,
                value_usd=value_usd,
                tx_signature=tx_signature,
                status="success" if tx_signature else "pending"
            )
            db.add(trade)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
            if db:
                db.close()
    
    async def sleep_until_midnight(self):
        """Sleep until next midnight UTC"""
        now = datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seconds_until_midnight = (tomorrow - now).total_seconds()
        await asyncio.sleep(seconds_until_midnight)


# Global bot runner instance
bot_runner = BotRunner()
