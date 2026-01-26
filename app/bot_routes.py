"""
Bot & Strategy API Routes with PostgreSQL persistence.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import uuid
import logging

from app.hummingbot_client import HummingbotClient
from app.database import get_db, Bot, Client

logger = logging.getLogger(__name__)

router = APIRouter()

# Hummingbot client - initialized on first use
_hummingbot_client: Optional[HummingbotClient] = None


def get_hummingbot_client() -> HummingbotClient:
    """Get or create Hummingbot client"""
    global _hummingbot_client
    if _hummingbot_client is None:
        _hummingbot_client = HummingbotClient()
    return _hummingbot_client


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


def _extract_running_instances(hb_status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract running bot instances from Hummingbot status response.
    Handle various response formats.
    """
    running = {}
    
    # Try different possible structures
    data = hb_status.get("data", hb_status)
    
    # Format 1: data.bots
    if "bots" in data:
        for name, info in data["bots"].items():
            running[name] = info
    
    # Format 2: data.running_bots (list)
    if "running_bots" in data:
        for bot in data["running_bots"]:
            name = bot.get("instance_name", bot.get("name"))
            if name:
                running[name] = bot
    
    # Format 3: direct list
    if isinstance(data, list):
        for bot in data:
            name = bot.get("instance_name", bot.get("name"))
            if name:
                running[name] = bot
    
    return running


def get_strategies():
    """Return available trading strategies"""
    return [
        {"id": "market_making", "name": "Market Making", "description": "Place buy/sell orders around mid price"},
        {"id": "grid", "name": "Grid Trading", "description": "Place orders in a grid pattern"},
        {"id": "dca", "name": "Dollar Cost Averaging", "description": "Buy at regular intervals"},
        {"id": "twap", "name": "TWAP", "description": "Time-weighted average price execution"},
        {"id": "volume", "name": "Volume Trading", "description": "Create volume by trading between accounts"},
        {"id": "spread", "name": "Spread Trading", "description": "Market making with spread"}
    ]


class CreateBotRequest(BaseModel):
    name: str
    account: str
    strategy: str  # market_making, grid, dca, twap, volume, spread
    connector: str
    pair: str
    config: Optional[Dict[str, Any]] = {}


# =============================================================================
# Bot Endpoints
# =============================================================================

@router.get("/bots")
async def list_bots(
    account: Optional[str] = Query(None, description="Filter by account identifier"),
    db: Session = Depends(get_db)
):
    """
    List all trading bots, optionally filtered by account.
    Combines database definitions (source of truth) with Hummingbot runtime status.
    """
    try:
        # 1. Get bot definitions from database
        query = db.query(Bot)
        if account:
            query = query.filter(Bot.account == account)
        
        db_bots = query.all()
        
        # 2. Transform to response format
        bots = []
        for db_bot in db_bots:
            chain = "solana" if "jupiter" in db_bot.connector.lower() else "evm"
            bot = {
                "id": db_bot.id,
                "name": db_bot.name,
                "account": db_bot.account,
                "connector": db_bot.connector,
                "pair": db_bot.pair,
                "strategy": db_bot.strategy,
                "config": db_bot.config or {},
                "status": db_bot.status or "stopped",
                "chain": chain,
                "instance_name": db_bot.instance_name,
                "created_at": db_bot.created_at.isoformat() if db_bot.created_at else None,
            }
            bots.append(bot)
        
        # 3. Get runtime status from Hummingbot to update "running" status
        try:
            hummingbot_client = get_hummingbot_client()
            hb_status = await hummingbot_client.get_status()
            running_instances = _extract_running_instances(hb_status)
            
            # 4. Update status for running bots
            for bot in bots:
                instance_name = bot.get("instance_name") or bot["name"]
                if instance_name in running_instances:
                    bot["status"] = "running"
                    bot["runtime_info"] = running_instances[instance_name]
                    # Update database status
                    db_bot = db.query(Bot).filter(Bot.id == bot["id"]).first()
                    if db_bot:
                        db_bot.status = "running"
                        db_bot.updated_at = datetime.utcnow()
                        db.commit()
        except Exception as e:
            logger.warning(f"Could not fetch Hummingbot status: {e}")
            # Continue with database data, status remains as stored
        
        return {"bots": bots}
    except Exception as e:
        logger.error(f"Failed to list bots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list bots: {str(e)}")


@router.get("/bots/{bot_id}")
async def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get bot details"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot not found: {bot_id}")
    
    chain = "solana" if "jupiter" in bot.connector.lower() else "evm"
    return {
        "id": bot.id,
        "name": bot.name,
        "account": bot.account,
        "connector": bot.connector,
        "pair": bot.pair,
        "strategy": bot.strategy,
        "config": bot.config or {},
        "status": bot.status or "stopped",
        "chain": chain,
        "instance_name": bot.instance_name,
        "error": bot.error,
        "created_at": bot.created_at.isoformat() if bot.created_at else None,
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


@router.post("/bots/create")
async def create_bot(request: CreateBotRequest, db: Session = Depends(get_db)):
    """Create a new trading bot"""
    try:
        # 1. Validate client exists with matching account_identifier
        client = db.query(Client).filter(Client.account_identifier == request.account).first()
        if not client:
            raise HTTPException(
                status_code=400,
                detail=f"Client with account_identifier '{request.account}' not found. Create client first."
            )
        
        # 2. Check if bot with same name already exists
        existing_bot = db.query(Bot).filter(Bot.name == request.name).first()
        if existing_bot:
            raise HTTPException(
                status_code=400,
                detail=f"Bot with name '{request.name}' already exists"
            )
        
        # 3. Generate unique instance name for Hummingbot
        instance_name = f"{request.account}_{uuid.uuid4().hex[:8]}"
        
        # 4. Generate Hummingbot script
        script_content = generate_hummingbot_script(
            request.strategy,
            request.connector,
            request.pair,
            request.config
        )
        script_name = f"{request.name}_strategy.py"
        
        # 5. Deploy script to Hummingbot
        hummingbot_client = get_hummingbot_client()
        try:
            await hummingbot_client.deploy_script(
                script_content,
                script_name,
                instance_name=instance_name,
                credentials_profile=request.account
            )
            logger.info(f"Deployed script: {script_name} for instance: {instance_name}")
            bot_status = "running"  # deploy-v2-script auto-starts the bot
        except Exception as e:
            logger.error(f"Failed to deploy script to Hummingbot: {e}")
            bot_status = "error"
            error_message = str(e)
        
        # 6. Store bot in database
        bot_id = str(uuid.uuid4())
        bot = Bot(
            id=bot_id,
            client_id=client.id,
            account=request.account,
            instance_name=instance_name,
            name=request.name,
            connector=request.connector,
            pair=request.pair,
            strategy=request.strategy,
            status=bot_status,
            config=request.config or {},
            error=error_message if bot_status == "error" else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(bot)
        
        try:
            db.commit()
            logger.info(f"Created bot: {bot_id} ({request.name}) for account: {request.account}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save bot to database: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save bot: {str(e)}")
        
        chain = "solana" if "jupiter" in request.connector.lower() else "evm"
        return {
            "id": bot_id,
            "name": bot.name,
            "account": bot.account,
            "connector": bot.connector,
            "pair": bot.pair,
            "strategy": bot.strategy,
            "config": bot.config or {},
            "status": bot.status,
            "chain": chain,
            "instance_name": bot.instance_name,
            "created_at": bot.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create bot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {str(e)}")


@router.post("/bots/{bot_id}/start")
async def start_bot(bot_id: str, db: Session = Depends(get_db)):
    """Start a trading bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot not found: {bot_id}")
    
    try:
        # Start via Hummingbot
        hummingbot_client = get_hummingbot_client()
        script_name = f"{bot.name}_strategy.py"
        await hummingbot_client.start_bot(bot.instance_name, script_name, bot.config or {})
        
        # Update status in database
        bot.status = "running"
        bot.error = None
        bot.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Started bot: {bot_id}")
        
        chain = "solana" if "jupiter" in bot.connector.lower() else "evm"
        return {
            "id": bot.id,
            "name": bot.name,
            "status": bot.status,
            "chain": chain,
        }
    except Exception as e:
        logger.error(f"Failed to start bot {bot_id}: {str(e)}")
        bot.status = "error"
        bot.error = str(e)
        bot.updated_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")


@router.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: str, db: Session = Depends(get_db)):
    """Stop a trading bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot not found: {bot_id}")
    
    try:
        # Stop via Hummingbot
        hummingbot_client = get_hummingbot_client()
        await hummingbot_client.stop_bot(bot.instance_name)
        
        # Update status in database
        bot.status = "stopped"
        bot.error = None
        bot.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Stopped bot: {bot_id}")
        
        chain = "solana" if "jupiter" in bot.connector.lower() else "evm"
        return {
            "id": bot.id,
            "name": bot.name,
            "status": bot.status,
            "chain": chain,
        }
    except Exception as e:
        logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
        bot.status = "error"
        bot.error = str(e)
        bot.updated_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")


@router.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    """Delete a trading bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot not found: {bot_id}")
    
    try:
        db.delete(bot)
        db.commit()
        logger.info(f"Deleted bot: {bot_id}")
        return {"status": "deleted", "bot_id": bot_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete bot: {str(e)}")


@router.get("/bots/{bot_id}/status")
async def get_bot_status(bot_id: str, db: Session = Depends(get_db)):
    """Get bot status and metrics"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot not found: {bot_id}")
    
    # Try to get runtime status from Hummingbot
    try:
        hummingbot_client = get_hummingbot_client()
        hb_status = await hummingbot_client.get_status()
        running_instances = _extract_running_instances(hb_status)
        
        instance_name = bot.instance_name or bot.name
        if instance_name in running_instances:
            runtime_info = running_instances[instance_name]
            # Update database status
            bot.status = "running"
            bot.updated_at = datetime.utcnow()
            db.commit()
        else:
            # Bot not running in Hummingbot
            if bot.status == "running":
                bot.status = "stopped"
                bot.updated_at = datetime.utcnow()
                db.commit()
    except Exception as e:
        logger.warning(f"Could not fetch Hummingbot status: {e}")
    
    chain = "solana" if "jupiter" in bot.connector.lower() else "evm"
    return {
        "id": bot.id,
        "name": bot.name,
        "status": bot.status or "stopped",
        "chain": chain,
        "error": bot.error,
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


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
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    return strategies[strategy_id]


# Legacy compatibility - keep init_bot_manager for main.py
def init_bot_manager(exchange_manager):
    """Legacy function - kept for compatibility with main.py"""
    # Database-based implementation doesn't need this
    # But we keep it to avoid breaking main.py
    pass
