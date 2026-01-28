"""
Solana Market Maker Bot
Automated market making using Jupiter limit orders

This bot:
1. Monitors current price
2. Cancels stale orders
3. Places new spread orders at configured intervals
4. Tracks P&L and filled orders
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from .jupiter_client import JupiterClient
from .transaction_signer import SolanaTransactionSigner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MarketMakerConfig:
    """Configuration for market maker bot"""
    # Token pair
    base_mint: str  # Token to market make
    quote_mint: str  # Usually SOL
    
    # Wallet
    wallet_address: str
    private_key: str  # Should come from secure storage
    
    # Strategy parameters
    spread_bps: int = 50  # 0.5% spread
    order_size: int = 1000000  # Amount per side (in base token smallest units)
    refresh_interval_seconds: int = 60  # How often to refresh orders
    order_expiry_seconds: int = 300  # 5 minute expiry
    
    # Risk limits
    max_position: Optional[int] = None  # Max position in base token
    min_quote_balance: int = 100000000  # Min SOL balance (0.1 SOL in lamports)
    
    # Behavior
    cancel_on_refresh: bool = True  # Cancel existing orders before placing new ones
    enabled: bool = True


@dataclass
class MarketMakerStats:
    """Statistics for market maker bot"""
    start_time: datetime = field(default_factory=datetime.now)
    orders_placed: int = 0
    orders_filled: int = 0
    orders_cancelled: int = 0
    total_buy_volume: int = 0
    total_sell_volume: int = 0
    errors: int = 0
    last_price: float = 0.0
    last_refresh: Optional[datetime] = None


class SolanaMarketMaker:
    """
    Market maker bot for Solana tokens via Jupiter
    
    Usage:
        config = MarketMakerConfig(
            base_mint="HZG1RVn4zcRM7zEFEVGYPGoPzPAWAj2AAdvQivfmLYNK",
            quote_mint="So11111111111111111111111111111111111111112",
            wallet_address="YOUR_WALLET",
            private_key="YOUR_PRIVATE_KEY",
            spread_bps=50,
            order_size=1000000000  # 1000 tokens if 6 decimals
        )
        
        bot = SolanaMarketMaker(config)
        await bot.start()
    """
    
    def __init__(
        self,
        config: MarketMakerConfig,
        rpc_url: str = "https://api.mainnet-beta.solana.com"
    ):
        self.config = config
        self.rpc_url = rpc_url
        self.jupiter: Optional[JupiterClient] = None
        self.signer: Optional[SolanaTransactionSigner] = None
        self.stats = MarketMakerStats()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def _init_clients(self):
        """Initialize API clients"""
        if not self.jupiter:
            self.jupiter = JupiterClient(rpc_url=self.rpc_url)
        if not self.signer:
            self.signer = SolanaTransactionSigner(rpc_url=self.rpc_url)
    
    async def _close_clients(self):
        """Close API clients"""
        if self.jupiter:
            await self.jupiter.close()
            self.jupiter = None
        if self.signer:
            await self.signer.close()
            self.signer = None
    
    async def start(self):
        """Start the market maker bot"""
        if self._running:
            logger.warning("Bot is already running")
            return
        
        logger.info(f"Starting market maker for {self.config.base_mint}")
        logger.info(f"Spread: {self.config.spread_bps} bps, Order size: {self.config.order_size}")
        
        self._running = True
        self.stats = MarketMakerStats()
        
        await self._init_clients()
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Stop the market maker bot"""
        logger.info("Stopping market maker...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Cancel all open orders
        await self._cancel_all_orders()
        await self._close_clients()
        
        logger.info("Market maker stopped")
    
    async def _run_loop(self):
        """Main bot loop"""
        while self._running and self.config.enabled:
            try:
                await self._refresh_orders()
                self.stats.last_refresh = datetime.now()
                
            except Exception as e:
                logger.error(f"Error in market maker loop: {e}")
                self.stats.errors += 1
            
            # Wait for next refresh
            await asyncio.sleep(self.config.refresh_interval_seconds)
    
    async def _refresh_orders(self):
        """Refresh spread orders"""
        logger.info("Refreshing orders...")
        
        # Check balances
        if not await self._check_balances():
            logger.warning("Insufficient balance, skipping refresh")
            return
        
        # Cancel existing orders if configured
        if self.config.cancel_on_refresh:
            await self._cancel_all_orders()
        
        # Get current price
        try:
            price_data = await self.jupiter.get_price(
                self.config.base_mint,
                self.config.quote_mint
            )
            self.stats.last_price = price_data["price"]
            logger.info(f"Current price: {self.stats.last_price}")
        except Exception as e:
            logger.error(f"Failed to get price: {e}")
            return
        
        # Place spread orders
        await self._place_spread_orders()
    
    async def _check_balances(self) -> bool:
        """Check if we have sufficient balances"""
        try:
            # Check SOL balance
            sol_balance = await self.signer.get_balance(self.config.wallet_address)
            if sol_balance < self.config.min_quote_balance:
                logger.warning(f"Low SOL balance: {sol_balance / 1e9} SOL")
                return False
            
            # Check token balance
            token_accounts = await self.signer.get_token_accounts(
                self.config.wallet_address,
                self.config.base_mint
            )
            
            if token_accounts:
                token_balance = token_accounts[0]["amount"]
                if token_balance < self.config.order_size:
                    logger.warning(f"Low token balance: {token_balance}")
                    # Still allow if we at least have SOL for buying
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check balances: {e}")
            return False
    
    async def _place_spread_orders(self):
        """Place buy and sell orders at spread from current price"""
        try:
            expired_at = int(time.time()) + self.config.order_expiry_seconds
            
            # Create spread orders
            spread_data = await self.jupiter.create_spread_orders(
                maker=self.config.wallet_address,
                base_mint=self.config.base_mint,
                quote_mint=self.config.quote_mint,
                base_amount=self.config.order_size,
                spread_bps=self.config.spread_bps,
                expired_at=expired_at
            )
            
            logger.info(f"Creating spread orders: Buy @ {spread_data['buy_price']}, Sell @ {spread_data['sell_price']}")
            
            # Sign and send buy order
            buy_tx = spread_data["buy_order"].get("tx") or spread_data["buy_order"].get("transaction")
            if buy_tx:
                buy_result = await self.signer.sign_and_send_transaction(
                    transaction_base64=buy_tx,
                    private_key=self.config.private_key
                )
                if buy_result.success:
                    logger.info(f"Buy order placed: {buy_result.signature}")
                    self.stats.orders_placed += 1
                else:
                    logger.error(f"Buy order failed: {buy_result.error}")
                    self.stats.errors += 1
            
            # Sign and send sell order
            sell_tx = spread_data["sell_order"].get("tx") or spread_data["sell_order"].get("transaction")
            if sell_tx:
                sell_result = await self.signer.sign_and_send_transaction(
                    transaction_base64=sell_tx,
                    private_key=self.config.private_key
                )
                if sell_result.success:
                    logger.info(f"Sell order placed: {sell_result.signature}")
                    self.stats.orders_placed += 1
                else:
                    logger.error(f"Sell order failed: {sell_result.error}")
                    self.stats.errors += 1
                    
        except Exception as e:
            logger.error(f"Failed to place spread orders: {e}")
            self.stats.errors += 1
    
    async def _cancel_all_orders(self):
        """Cancel all open orders for this token pair"""
        try:
            # Get open orders
            orders = await self.jupiter.get_open_orders(
                wallet=self.config.wallet_address,
                input_mint=self.config.base_mint
            )
            
            # Also get orders where we're buying (input is quote)
            buy_orders = await self.jupiter.get_open_orders(
                wallet=self.config.wallet_address,
                input_mint=self.config.quote_mint,
                output_mint=self.config.base_mint
            )
            
            all_orders = orders + buy_orders
            
            if not all_orders:
                logger.info("No open orders to cancel")
                return
            
            logger.info(f"Cancelling {len(all_orders)} orders...")
            
            # Cancel all
            cancel_data = await self.jupiter.cancel_all_orders(
                maker=self.config.wallet_address
            )
            
            tx_base64 = cancel_data.get("tx") or cancel_data.get("transaction")
            if tx_base64:
                result = await self.signer.sign_and_send_transaction(
                    transaction_base64=tx_base64,
                    private_key=self.config.private_key
                )
                if result.success:
                    logger.info(f"Cancelled orders: {result.signature}")
                    self.stats.orders_cancelled += len(all_orders)
                else:
                    logger.error(f"Failed to cancel orders: {result.error}")
                    
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current bot statistics"""
        return {
            "running": self._running,
            "enabled": self.config.enabled,
            "start_time": self.stats.start_time.isoformat(),
            "last_refresh": self.stats.last_refresh.isoformat() if self.stats.last_refresh else None,
            "last_price": self.stats.last_price,
            "orders_placed": self.stats.orders_placed,
            "orders_filled": self.stats.orders_filled,
            "orders_cancelled": self.stats.orders_cancelled,
            "errors": self.stats.errors,
            "config": {
                "base_mint": self.config.base_mint,
                "quote_mint": self.config.quote_mint,
                "spread_bps": self.config.spread_bps,
                "order_size": self.config.order_size,
                "refresh_interval": self.config.refresh_interval_seconds
            }
        }


# ============ BOT MANAGER ============

class MarketMakerManager:
    """
    Manages multiple market maker bots
    
    Usage:
        manager = MarketMakerManager()
        
        await manager.start_bot("client_1", config1)
        await manager.start_bot("client_2", config2)
        
        stats = manager.get_all_stats()
        
        await manager.stop_bot("client_1")
        await manager.stop_all()
    """
    
    def __init__(self):
        self.bots: Dict[str, SolanaMarketMaker] = {}
    
    async def start_bot(self, bot_id: str, config: MarketMakerConfig) -> bool:
        """Start a new market maker bot"""
        if bot_id in self.bots:
            logger.warning(f"Bot {bot_id} already exists")
            return False
        
        bot = SolanaMarketMaker(config)
        self.bots[bot_id] = bot
        await bot.start()
        return True
    
    async def stop_bot(self, bot_id: str) -> bool:
        """Stop a market maker bot"""
        if bot_id not in self.bots:
            logger.warning(f"Bot {bot_id} not found")
            return False
        
        await self.bots[bot_id].stop()
        del self.bots[bot_id]
        return True
    
    async def stop_all(self):
        """Stop all bots"""
        for bot_id in list(self.bots.keys()):
            await self.stop_bot(bot_id)
    
    def get_bot_stats(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific bot"""
        if bot_id not in self.bots:
            return None
        return self.bots[bot_id].get_stats()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all bots"""
        return {
            bot_id: bot.get_stats()
            for bot_id, bot in self.bots.items()
        }
    
    def list_bots(self) -> List[str]:
        """List all bot IDs"""
        return list(self.bots.keys())
