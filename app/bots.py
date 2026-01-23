"""
Bot Management for Trading Bridge
===================================

Adds automated trading bots to your existing trading-bridge.
Works with your ExchangeManager.

File: app/bots.py
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class StrategyType(str, Enum):
    MARKET_MAKING = "market_making"
    GRID = "grid"
    DCA = "dca"
    TWAP = "twap"
    VOLUME = "volume"


@dataclass
class Bot:
    """Trading bot instance"""
    id: str
    name: str
    account: str
    strategy: StrategyType
    connector: str
    pair: str
    config: Dict[str, Any]
    status: BotStatus = BotStatus.STOPPED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    error_message: Optional[str] = None
    total_trades: int = 0
    total_volume: float = 0.0
    realized_pnl: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "account": self.account,
            "strategy": self.strategy.value,
            "connector": self.connector,
            "pair": self.pair,
            "config": self.config,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "error_message": self.error_message,
            "metrics": {
                "total_trades": self.total_trades,
                "total_volume": self.total_volume,
                "realized_pnl": self.realized_pnl
            }
        }


class BotManager:
    """Manages trading bots - runs within existing trading-bridge process"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.bots: Dict[str, Bot] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
    
    def list_bots(self) -> List[dict]:
        return [bot.to_dict() for bot in self.bots.values()]
    
    def get_bot(self, bot_id: str) -> Optional[dict]:
        bot = self.bots.get(bot_id)
        return bot.to_dict() if bot else None
    
    def create_bot(
        self,
        name: str,
        account: str,
        strategy: str,
        connector: str,
        pair: str,
        config: Dict[str, Any] = None
    ) -> dict:
        """Create a new bot"""
        
        # Validate account exists
        acc = self.exchange_manager.get_account(account)
        if not acc:
            raise ValueError(f"Account not found: {account}")
        
        # Validate connector is in account
        if connector.lower() not in acc.connectors:
            raise ValueError(f"Connector {connector} not found in account {account}")
        
        bot_id = str(uuid.uuid4())[:8]
        
        bot = Bot(
            id=bot_id,
            name=name,
            account=account,
            strategy=StrategyType(strategy),
            connector=connector.lower(),
            pair=pair,
            config=config or {}
        )
        
        self.bots[bot_id] = bot
        logger.info(f"Created bot {bot_id}: {name}")
        
        return bot.to_dict()
    
    async def start_bot(self, bot_id: str) -> dict:
        bot = self.bots.get(bot_id)
        if not bot:
            raise ValueError(f"Bot not found: {bot_id}")
        
        if bot.status == BotStatus.RUNNING:
            return {"message": "Bot is already running", "bot": bot.to_dict()}
        
        task = asyncio.create_task(self._run_bot(bot))
        self._tasks[bot_id] = task
        
        bot.status = BotStatus.RUNNING
        bot.started_at = datetime.utcnow()
        bot.error_message = None
        
        logger.info(f"Started bot {bot_id}")
        return {"message": "Bot started", "bot": bot.to_dict()}
    
    async def stop_bot(self, bot_id: str) -> dict:
        bot = self.bots.get(bot_id)
        if not bot:
            raise ValueError(f"Bot not found: {bot_id}")
        
        task = self._tasks.get(bot_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        bot.status = BotStatus.STOPPED
        logger.info(f"Stopped bot {bot_id}")
        
        return {"message": "Bot stopped", "bot": bot.to_dict()}
    
    def delete_bot(self, bot_id: str) -> dict:
        bot = self.bots.get(bot_id)
        if not bot:
            raise ValueError(f"Bot not found: {bot_id}")
        
        if bot.status == BotStatus.RUNNING:
            raise ValueError("Stop bot before deleting")
        
        del self.bots[bot_id]
        return {"message": "Bot deleted"}
    
    def get_bot_status(self, bot_id: str) -> dict:
        bot = self.bots.get(bot_id)
        if not bot:
            raise ValueError(f"Bot not found: {bot_id}")
        
        uptime = 0
        if bot.started_at and bot.status == BotStatus.RUNNING:
            uptime = (datetime.utcnow() - bot.started_at).total_seconds()
        
        return {"bot": bot.to_dict(), "uptime_seconds": uptime}
    
    async def _run_bot(self, bot: Bot):
        """Main bot loop"""
        try:
            strategy = self._get_strategy(bot)
            
            while True:
                try:
                    await strategy.execute_cycle()
                    await asyncio.sleep(strategy.cycle_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Bot {bot.id} error: {e}")
                    bot.error_message = str(e)
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info(f"Bot {bot.id} stopped")
        except Exception as e:
            logger.error(f"Bot {bot.id} fatal: {e}")
            bot.status = BotStatus.ERROR
            bot.error_message = str(e)
    
    def _get_strategy(self, bot: Bot):
        strategies = {
            StrategyType.MARKET_MAKING: MarketMakingStrategy,
            StrategyType.GRID: GridStrategy,
            StrategyType.DCA: DCAStrategy,
            StrategyType.TWAP: TWAPStrategy,
            StrategyType.VOLUME: VolumeStrategy,
        }
        return strategies[bot.strategy](self.exchange_manager, bot)


# =============================================================================
# Strategies
# =============================================================================

class BaseStrategy:
    cycle_interval: float = 10.0
    
    def __init__(self, exchange_manager, bot: Bot):
        self.exchange_manager = exchange_manager
        self.bot = bot
        self.config = bot.config
        self.account = exchange_manager.get_account(bot.account)
    
    async def execute_cycle(self):
        raise NotImplementedError
    
    async def get_price(self) -> float:
        price = await self.exchange_manager.get_price(self.bot.connector, self.bot.pair)
        if price is None:
            raise ValueError(f"Could not get price for {self.bot.pair}")
        return float(price)
    
    async def place_order(self, side: str, amount: float, price: float = None, order_type: str = "limit"):
        result = await self.account.place_order(
            connector_name=self.bot.connector,
            trading_pair=self.bot.pair,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price
        )
        self.bot.total_trades += 1
        self.bot.total_volume += amount * (price or await self.get_price())
        return result
    
    async def cancel_all_orders(self):
        orders = await self.account.get_orders(self.bot.pair)
        for order in orders:
            if order["connector"] == self.bot.connector:
                try:
                    await self.account.cancel_order(
                        self.bot.connector,
                        order["id"],
                        self.bot.pair
                    )
                except:
                    pass


class MarketMakingStrategy(BaseStrategy):
    """Places buy/sell orders around mid price"""
    cycle_interval = 30.0
    
    async def execute_cycle(self):
        spread = self.config.get("spread", 0.002)
        order_amount = self.config.get("order_amount", 0.01)
        levels = self.config.get("levels", 1)
        
        await self.cancel_all_orders()
        price = await self.get_price()
        
        for level in range(levels):
            level_spread = spread * (level + 1)
            buy_price = round(price * (1 - level_spread), 8)
            sell_price = round(price * (1 + level_spread), 8)
            
            await self.place_order("buy", order_amount, buy_price)
            await self.place_order("sell", order_amount, sell_price)
        
        logger.info(f"Bot {self.bot.id}: {levels * 2} orders around {price}")


class GridStrategy(BaseStrategy):
    """Grid trading within price range"""
    cycle_interval = 60.0
    
    async def execute_cycle(self):
        lower = self.config.get("lower_price")
        upper = self.config.get("upper_price")
        grid_levels = self.config.get("grid_levels", 10)
        total_amount = self.config.get("total_amount", 1.0)
        
        if not lower or not upper:
            raise ValueError("Grid needs lower_price and upper_price")
        
        await self.cancel_all_orders()
        
        step = (upper - lower) / grid_levels
        amount = total_amount / grid_levels
        current = await self.get_price()
        
        for i in range(grid_levels):
            grid_price = round(lower + (i * step), 8)
            side = "buy" if grid_price < current else "sell"
            await self.place_order(side, amount, grid_price)
        
        logger.info(f"Bot {self.bot.id}: {grid_levels} grid orders")


class DCAStrategy(BaseStrategy):
    """Dollar cost averaging - regular buys"""
    cycle_interval = 3600.0
    
    async def execute_cycle(self):
        buy_amount_usd = self.config.get("buy_amount", 10.0)
        price = await self.get_price()
        amount = buy_amount_usd / price
        
        await self.place_order("buy", amount, order_type="market")
        logger.info(f"Bot {self.bot.id}: DCA bought {amount:.6f} at {price}")


class TWAPStrategy(BaseStrategy):
    """Time-weighted execution"""
    cycle_interval = 60.0
    executed: float = 0.0
    
    async def execute_cycle(self):
        total = self.config.get("total_amount", 1.0)
        side = self.config.get("side", "buy")
        duration = self.config.get("duration_minutes", 60)
        
        per_cycle = total / duration
        
        if self.executed >= total:
            self.bot.status = BotStatus.STOPPED
            return
        
        await self.place_order(side, per_cycle, order_type="market")
        self.executed += per_cycle
        logger.info(f"Bot {self.bot.id}: TWAP {self.executed:.4f}/{total}")


class VolumeStrategy(BaseStrategy):
    """Volume generation with tight spread"""
    cycle_interval = 30.0
    
    async def execute_cycle(self):
        volume_usd = self.config.get("volume_per_cycle", 100.0)
        spread = self.config.get("spread", 0.001)
        
        price = await self.get_price()
        amount = volume_usd / price / 2
        
        buy_price = round(price * (1 - spread), 8)
        sell_price = round(price * (1 + spread), 8)
        
        await self.place_order("buy", amount, buy_price)
        await self.place_order("sell", amount, sell_price)
        logger.info(f"Bot {self.bot.id}: Volume orders ${volume_usd}")


# =============================================================================
# Strategy Info
# =============================================================================

STRATEGIES = {
    "market_making": {
        "name": "Market Making",
        "description": "Places buy/sell orders around current price",
        "config_schema": {
            "spread": {"type": "float", "default": 0.002, "description": "Spread (0.002 = 0.2%)"},
            "order_amount": {"type": "float", "default": 0.01, "description": "Amount per order"},
            "levels": {"type": "int", "default": 1, "description": "Order levels each side"}
        }
    },
    "grid": {
        "name": "Grid Trading",
        "description": "Orders at fixed price intervals",
        "config_schema": {
            "lower_price": {"type": "float", "required": True},
            "upper_price": {"type": "float", "required": True},
            "grid_levels": {"type": "int", "default": 10},
            "total_amount": {"type": "float", "default": 1.0}
        }
    },
    "dca": {
        "name": "Dollar Cost Averaging",
        "description": "Regular buys at intervals",
        "config_schema": {
            "buy_amount": {"type": "float", "default": 10.0, "description": "USD per buy"}
        }
    },
    "twap": {
        "name": "TWAP",
        "description": "Execute large order over time",
        "config_schema": {
            "total_amount": {"type": "float", "required": True},
            "side": {"type": "string", "default": "buy"},
            "duration_minutes": {"type": "int", "default": 60}
        }
    },
    "volume": {
        "name": "Volume Generation",
        "description": "Generate trading volume",
        "config_schema": {
            "volume_per_cycle": {"type": "float", "default": 100.0},
            "spread": {"type": "float", "default": 0.001}
        }
    }
}

def get_strategies() -> List[dict]:
    return [{"id": k, **v} for k, v in STRATEGIES.items()]
