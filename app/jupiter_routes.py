from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .jupiter import get_quote, execute_swap, get_token_balance, TOKENS

router = APIRouter(prefix="/jupiter", tags=["jupiter"])

class QuoteRequest(BaseModel):
    input_token: str
    output_token: str
    amount: float
    slippage_bps: Optional[int] = 50

class SwapRequest(BaseModel):
    input_token: str
    output_token: str
    amount: float
    account_name: str

@router.get("/tokens")
async def list_tokens():
    return TOKENS

@router.post("/quote")
async def jupiter_quote(req: QuoteRequest):
    input_mint = TOKENS.get(req.input_token.upper(), req.input_token)
    output_mint = TOKENS.get(req.output_token.upper(), req.output_token)
    
    # Convert to smallest unit (lamports for SOL, etc)
    decimals = 9 if req.input_token.upper() == "SOL" else 6
    amount = int(req.amount * (10 ** decimals))
    
    quote = await get_quote(input_mint, output_mint, amount, req.slippage_bps)
    
    out_decimals = 9 if req.output_token.upper() == "SOL" else 6
    
    return {
        "input_token": req.input_token,
        "output_token": req.output_token,
        "input_amount": req.amount,
        "output_amount": int(quote.get("outAmount", 0)) / (10 ** out_decimals),
        "price_impact": quote.get("priceImpactPct"),
        "route_info": quote.get("routePlan")
    }

@router.post("/swap")
async def jupiter_swap(req: SwapRequest):
    from .main import accounts_db
    
    account = accounts_db.get(req.account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {req.account_name} not found")
    
    solana_key = account.get("connectors", {}).get("solana", {}).get("private_key")
    if not solana_key:
        raise HTTPException(status_code=400, detail="Solana wallet not configured for this account")
    
    input_mint = TOKENS.get(req.input_token.upper(), req.input_token)
    output_mint = TOKENS.get(req.output_token.upper(), req.output_token)
    
    decimals = 9 if req.input_token.upper() == "SOL" else 6
    amount = int(req.amount * (10 ** decimals))
    
    result = await execute_swap(input_mint, output_mint, amount, solana_key)
    return result

@router.get("/balance/{account_name}")
async def solana_balance(account_name: str, token: str = "SOL"):
    from .main import accounts_db
    
    account = accounts_db.get(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_name} not found")
    
    wallet = account.get("connectors", {}).get("solana", {}).get("wallet")
    if not wallet:
        raise HTTPException(status_code=400, detail="Solana wallet not configured")
    
    token_mint = TOKENS.get(token.upper(), token)
    return await get_token_balance(wallet, token_mint)
