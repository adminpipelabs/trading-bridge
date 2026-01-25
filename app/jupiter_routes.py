from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from .jupiter import get_quote, TOKENS

router = APIRouter(prefix="/jupiter", tags=["jupiter"])
logger = logging.getLogger(__name__)

class QuoteRequest(BaseModel):
    input_token: str
    output_token: str
    amount: float
    slippage_bps: Optional[int] = 50

@router.get("/tokens")
async def list_tokens():
    return TOKENS

@router.post("/quote")
async def jupiter_quote(req: QuoteRequest):
    try:
        logger.info(f"Getting Jupiter quote: {req.input_token} -> {req.output_token}, amount: {req.amount}")
        result = await get_quote(req.input_token, req.output_token, req.amount, req.slippage_bps)
        logger.info(f"Quote successful: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting Jupiter quote: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
