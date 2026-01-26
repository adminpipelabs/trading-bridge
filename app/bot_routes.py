"""
Bot & Strategy API Routes
==========================

File: app/bot_routes.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.hummingbot_client import HummingbotClient

logger = logging.getLogger(__name__)

# Bot functionality - integrated with Hummingbot API

def generate_hummingbot_script(
    strategy: str,
    connector: str,
    pair: str,
    config: Dict[str, Any]
) -> str:
    """
    Generate Hummingbot v2 strategy script
    
    Args:
        strategy: Strategy type (market_making, volume, etc.)
        connector: Exchange connector (bitmart, jupiter, etc.)
        pair: Trading pair (e.g., "SHARP/USDT")
        config: Strategy configuration
        
    Returns:
        Python script as string
    """
    # Extract config values with defaults
    bid_spread = config.get("bid_spread", 0.001)  # 0.1%
    ask_spread = config.get("ask_spread", 0.001)   # 0.1%
    order_amount = config.get("order_amount", 100)
    order_refresh_time = config.get("order_refresh_time", 60)
    
    if strategy == "market_making" or strategy == "spread":
        # Pure Market Making Strategy V2
        script = f'''from hummingbot.strategy.pure_market_making.pure_market_making_v2 import PureMarketMakingStrategyV2

strategy = PureMarketMakingStrategyV2(
    exchange="{connector}",
    trading_pair="{pair}",
    bid_spread={bid_spread},
    ask_spread={ask_spread},
    order_amount={order_amount},
    order_refresh_time={order_refresh_time}
)
'''
    elif strategy == "volume":
        # Volume trading strategy (custom implementation)
        script = f'''# Volume Trading Strategy
# Custom implementation for volume generation

from hummingbot.strategy.volume_trading import VolumeTradingStrategy

strategy = VolumeTradingStrategy(
    exchange="{connector}",
    trading_pair="{pair}",
    order_amount={order_amount}
)
'''
    else:
        # Default: Market Making
        script = f'''from hummingbot.strategy.pure_market_making.pure_market_making_v2 import PureMarketMakingStrategyV2

strategy = PureMarketMakingStrategyV2(
    exchange="{connector}",
    trading_pair="{pair}",
    bid_spread={bid_spread},
    ask_spread={ask_spread},
    order_amount={order_amount},
    order_refresh_time={order_refresh_time}
)
'''
    
    return script


def transform_hummingbot_bot(bot_name: str, bot_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Hummingbot bot format to our format
    
    Args:
        bot_name: Bot name from Hummingbot
        bot_info: Bot info dict from Hummingbot
        
    Returns:
        Transformed bot dict
    """
    # Determine chain from connector
    connector = bot_info.get("connector", "").lower()
    chain = "solana" if "jupiter" in connector else "evm"
    
    # Map strategy names
    strategy_map = {
        "pure_market_making": "spread",
        "market_making": "spread",
        "volume_trading": "volume",
    }
    strategy = bot_info.get("strategy", "unknown")
    our_strategy = strategy_map.get(strategy.lower(), strategy)
    
    return {
        "id": bot_name,
        "name": bot_name,
        "status": "running" if bot_info.get("is_running", False) else "stopped",
        "strategy": our_strategy,
        "connector": connector,
        "pair": bot_info.get("trading_pair", "unknown"),
        "chain": chain,
        "account": bot_info.get("account", "unknown"),
        "config": bot_info.get("config", {})
    }


class BotManager:
    """BotManager integrated with Hummingbot API"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.hummingbot_client = HummingbotClient()
        # Keep local cache for bot metadata
        self.bot_metadata = {}
    
    async def list_bots(self):
        """List all bots from Hummingbot"""
        try:
            # Get status from Hummingbot
            status = await self.hummingbot_client.get_status()
            bots_data = status.get("bots", {})
            
            # Transform to our format
            bots = []
            for bot_name, bot_info in bots_data.items():
                transformed_bot = transform_hummingbot_bot(bot_name, bot_info)
                # Merge with local metadata if exists
                if bot_name in self.bot_metadata:
                    transformed_bot.update(self.bot_metadata[bot_name])
                bots.append(transformed_bot)
            
            return {"bots": bots}
        except Exception as e:
            logger.error(f"Failed to list bots from Hummingbot: {str(e)}")
            # Fallback to local cache if Hummingbot unavailable
            return {"bots": list(self.bot_metadata.values())}
    
    def get_bot(self, bot_id):
        """Get bot details"""
        # Try to get from Hummingbot first
        # For now, return from local cache
        return self.bot_metadata.get(bot_id)
    
    async def create_bot(self, name, account, strategy, connector, pair, config):
        """Create and start a bot via Hummingbot"""
        try:
            # Generate script
            script_content = generate_hummingbot_script(strategy, connector, pair, config)
            script_name = f"{name}_strategy.py"
            
            # Deploy script to Hummingbot
            await self.hummingbot_client.deploy_script(script_content, script_name)
            logger.info(f"Deployed script: {script_name}")
            
            # Start bot
            await self.hummingbot_client.start_bot(name, script_name, config)
            logger.info(f"Started bot: {name}")
            
            # Store metadata locally
            bot_id = name
            bot = {
                "id": bot_id,
                "name": name,
                "account": account,
                "strategy": strategy,
                "connector": connector,
                "pair": pair,
                "config": config,
                "status": "running",
                "chain": "solana" if "jupiter" in connector.lower() else "evm"
            }
            self.bot_metadata[bot_id] = bot
            
            return bot
        except Exception as e:
            logger.error(f"Failed to create bot: {str(e)}")
            raise ValueError(f"Failed to create bot: {str(e)}")
    
    async def start_bot(self, bot_id):
        """Start a bot via Hummingbot"""
        try:
            # Get bot metadata
            bot = self.bot_metadata.get(bot_id)
            if not bot:
                raise ValueError(f"Bot not found: {bot_id}")
            
            # Start via Hummingbot
            script_name = f"{bot_id}_strategy.py"
            await self.hummingbot_client.start_bot(bot_id, script_name, bot.get("config", {}))
            
            # Update status
            bot["status"] = "running"
            self.bot_metadata[bot_id] = bot
            
            return bot
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {str(e)}")
            raise ValueError(f"Failed to start bot: {str(e)}")
    
    async def stop_bot(self, bot_id):
        """Stop a bot via Hummingbot"""
        try:
            # Stop via Hummingbot
            await self.hummingbot_client.stop_bot(bot_id)
            
            # Update status
            bot = self.bot_metadata.get(bot_id)
            if bot:
                bot["status"] = "stopped"
                self.bot_metadata[bot_id] = bot
                return bot
            else:
                return {"id": bot_id, "status": "stopped"}
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            raise ValueError(f"Failed to stop bot: {str(e)}")
    
    def delete_bot(self, bot_id):
        """Delete bot metadata (bot deletion in Hummingbot handled separately)"""
        if bot_id in self.bot_metadata:
            del self.bot_metadata[bot_id]
        return {"message": f"Bot {bot_id} deleted"}
    
    async def get_bot_status(self, bot_id):
        """Get bot status from Hummingbot"""
        try:
            # Get status from Hummingbot
            status = await self.hummingbot_client.get_status()
            bots_data = status.get("bots", {})
            
            if bot_id in bots_data:
                bot_info = bots_data[bot_id]
                return transform_hummingbot_bot(bot_id, bot_info)
            else:
                # Fallback to local cache
                return self.bot_metadata.get(bot_id)
        except Exception as e:
            logger.error(f"Failed to get bot status: {str(e)}")
            # Fallback to local cache
            return self.bot_metadata.get(bot_id)


def get_strategies():
    """Return available trading strategies"""
    return [
        {"id": "market_making", "name": "Market Making", "description": "Place buy/sell orders around mid price"},
        {"id": "grid", "name": "Grid Trading", "description": "Place orders in a grid pattern"},
        {"id": "dca", "name": "Dollar Cost Averaging", "description": "Buy at regular intervals"},
        {"id": "twap", "name": "TWAP", "description": "Time-weighted average price execution"},
        {"id": "volume", "name": "Volume Trading", "description": "Create volume by trading between accounts"}
    ]


router = APIRouter()

# Will be initialized by main.py
bot_manager: BotManager = None


def init_bot_manager(exchange_manager):
    """Called from main.py at startup"""
    global bot_manager
    bot_manager = BotManager(exchange_manager)


class CreateBotRequest(BaseModel):
    name: str
    account: str
    strategy: str  # market_making, grid, dca, twap, volume
    connector: str
    pair: str
    config: Optional[Dict[str, Any]] = {}


# =============================================================================
# Bot Endpoints
# =============================================================================

@router.get("/bots")
async def list_bots():
    """List all trading bots"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    return bot_manager.list_bots()


@router.get("/bots/{bot_id}")
async def get_bot(bot_id: str):
    """Get bot details"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    bot = bot_manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, f"Bot not found: {bot_id}")
    return bot


@router.post("/bots/create")
async def create_bot(request: CreateBotRequest):
    """Create a new trading bot"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    try:
        return bot_manager.create_bot(
            name=request.name,
            account=request.account,
            strategy=request.strategy,
            connector=request.connector,
            pair=request.pair,
            config=request.config
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/bots/{bot_id}/start")
async def start_bot(bot_id: str):
    """Start a trading bot"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    try:
        return await bot_manager.start_bot(bot_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: str):
    """Stop a trading bot"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    try:
        return await bot_manager.stop_bot(bot_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    """Delete a trading bot"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    try:
        return bot_manager.delete_bot(bot_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/bots/{bot_id}/status")
async def get_bot_status(bot_id: str):
    """Get bot status and metrics"""
    if not bot_manager:
        raise HTTPException(500, "Bot manager not initialized")
    try:
        return bot_manager.get_bot_status(bot_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# =============================================================================
# Strategy Endpoints
# =============================================================================

@router.get("/strategies")
async def list_strategies():
    """List available trading strategies"""
    return get_strategies()


@router.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get strategy details"""
    strategies = {s["id"]: s for s in get_strategies()}
    if strategy_id not in strategies:
        raise HTTPException(404, f"Strategy not found: {strategy_id}")
    return strategies[strategy_id]
