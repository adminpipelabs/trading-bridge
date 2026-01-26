"""
Bot management routes with PostgreSQL persistence.
Synchronous routes for SQLAlchemy compatibility.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import logging

from app.database import get_db, Bot, Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["bots"])


# ============================================================
# Request/Response Models
# ============================================================

class BotConfig(BaseModel):
    bid_spread: Optional[float] = 0.003
    ask_spread: Optional[float] = 0.003
    order_amount: Optional[float] = 1000
    order_interval: Optional[int] = 60


class CreateBotRequest(BaseModel):
    name: str = Field(..., description="Bot display name")
    account: str = Field(..., description="Account identifier (must match client account_identifier)")
    connector: str = Field(..., description="Exchange connector: 'bitmart', 'jupiter'")
    pair: str = Field(..., description="Trading pair: 'SHARP/USDT', 'SOL/USDC'")
    strategy: str = Field(..., description="Strategy: 'spread', 'volume', 'grid'")
    config: Optional[BotConfig] = Field(default_factory=BotConfig)


# ============================================================
# Database Dependency
# ============================================================
# Using get_db from app.database (imported above)


# ============================================================
# Helper Functions
# ============================================================

def generate_instance_name(bot_id: str, account: str) -> str:
    """Generate Hummingbot instance name."""
    return f"{account}_{bot_id[:8]}"


# ============================================================
# Routes (Synchronous)
# ============================================================

@router.post("/create")
def create_bot(request: CreateBotRequest, db: Session = Depends(get_db)):
    """Create a new bot and persist to database."""
    bot_id = str(uuid.uuid4())
    instance_name = generate_instance_name(bot_id, request.account)

    # Verify client exists
    client = db.query(Client).filter(
        Client.account_identifier == request.account
    ).first()

    if not client:
        raise HTTPException(
            status_code=400,
            detail=f"No client found with account_identifier '{request.account}'"
        )

    # Create bot record
    bot = Bot(
        id=bot_id,
        client_id=client.id,
        account=request.account,
        instance_name=instance_name,
        name=request.name,
        connector=request.connector,
        pair=request.pair,
        strategy=request.strategy,
        status="created",
        config=request.config.dict() if request.config else {},
    )

    db.add(bot)

    # Deploy to Hummingbot
    try:
        # TODO: Integrate with hummingbot_client when ready
        # from app.hummingbot_client import hummingbot
        # hummingbot.deploy_script(
        #     instance_name=instance_name,
        #     credentials_profile=request.account,
        #     script_name=f"{request.strategy}_strategy",
        #     config={
        #         "connector": request.connector,
        #         "trading_pair": request.pair,
        #         **bot.config
        #     }
        # )
        bot.status = "running"
        logger.info(f"Bot {bot_id} created successfully")
    except Exception as e:
        logger.error(f"Failed to deploy bot {bot_id}: {e}")
        bot.status = "deploy_failed"
        bot.error = str(e)

    db.commit()
    db.refresh(bot)

    return bot.to_dict()


@router.get("")
def list_bots(
    account: Optional[str] = Query(None, description="Filter by account identifier"),
    db: Session = Depends(get_db)
):
    """List all bots, optionally filtered by account."""
    query = db.query(Bot)

    if account:
        query = query.filter(Bot.account == account)

    bots = query.all()

    return {"bots": [bot.to_dict() for bot in bots]}


@router.get("/{bot_id}")
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get a specific bot by ID."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return bot.to_dict()


@router.post("/{bot_id}/start")
def start_bot(bot_id: str, db: Session = Depends(get_db)):
    """Start a stopped bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if bot.status == "running":
        return {"status": "already_running", "bot_id": bot_id}

    try:
        # TODO: Integrate with hummingbot_client when ready
        # from app.hummingbot_client import hummingbot
        # hummingbot.start_bot(bot.instance_name)
        bot.status = "running"
        bot.error = None
        db.commit()
        logger.info(f"Bot {bot_id} started")
        return {"status": "started", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Failed to start bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{bot_id}/stop")
def stop_bot(bot_id: str, db: Session = Depends(get_db)):
    """Stop a running bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if bot.status == "stopped":
        return {"status": "already_stopped", "bot_id": bot_id}

    try:
        # TODO: Integrate with hummingbot_client when ready
        # from app.hummingbot_client import hummingbot
        # hummingbot.stop_bot(bot.instance_name)
        bot.status = "stopped"
        db.commit()
        logger.info(f"Bot {bot_id} stopped")
        return {"status": "stopped", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Failed to stop bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{bot_id}")
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    """Delete a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Stop bot first if running
    if bot.status == "running":
        try:
            # hummingbot.stop_bot(bot.instance_name)
            pass
        except Exception as e:
            logger.warning(f"Failed to stop bot before deletion: {e}")

    db.delete(bot)
    db.commit()

    return {"status": "deleted", "bot_id": bot_id}
