from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from .jupiter import get_quote, TOKENS

router = APIRouter(prefix="/jupiter", tags=["jupiter"])

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
    return await get_quote(req.input_token, req.output_token, req.amount, req.slippage_bps)
