"""
Bot & Strategy API Routes
==========================

File: app/bot_routes.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.bots import BotManager, get_strategies

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
