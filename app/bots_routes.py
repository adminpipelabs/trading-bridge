from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .bots import get_all_bots, get_bot, create_bot, update_bot_status, delete_bot

router = APIRouter(prefix="/bots", tags=["bots"])

class BotCreate(BaseModel):
    name: str
    client: str
    exchange: str
    pair: str
    type: str  # spread, volume, grid
    config: Optional[dict] = {}

@router.get("")
async def list_bots():
    return {"bots": get_all_bots()}

@router.get("/{bot_id}")
async def get_bot_status(bot_id: str):
    bot = get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@router.post("/create")
async def create_new_bot(bot: BotCreate):
    bot_id = f"{bot.client}_{bot.type}_{bot.pair.replace('/', '_')}".lower()
    return create_bot(bot_id, bot.dict())

@router.post("/{bot_id}/start")
async def start_bot(bot_id: str):
    bot = update_bot_status(bot_id, "running")
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"message": f"Bot {bot_id} started", "bot": bot}

@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str):
    bot = update_bot_status(bot_id, "stopped")
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"message": f"Bot {bot_id} stopped", "bot": bot}

@router.delete("/{bot_id}")
async def remove_bot(bot_id: str):
    if delete_bot(bot_id):
        return {"message": f"Bot {bot_id} deleted"}
    raise HTTPException(status_code=404, detail="Bot not found")
