"""
Portfolio API endpoints
Get balances and trade history
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.exchange import exchange_manager

router = APIRouter()


@router.get("/portfolio")
async def get_portfolio(account: str = Query(..., description="Account name")):
    """Get portfolio balances for an account"""
    acc = exchange_manager.get_account(account)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{account}' not found")
    
    try:
        balances = await acc.get_balances()
        return {
            "account": account,
            "balances": balances
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/state")
async def get_portfolio_state(data: dict):
    """Get portfolio state for multiple accounts (for Hummingbot compatibility)"""
    account_names = data.get("account_names", [])
    
    result = {}
    for account_name in account_names:
        acc = exchange_manager.get_account(account_name)
        if acc:
            try:
                balances = await acc.get_balances()
                result[account_name] = balances
            except Exception as e:
                result[account_name] = {"error": str(e)}
        else:
            result[account_name] = {"error": "Account not found"}
    
    return result


@router.get("/history")
async def get_trade_history(
    account: str = Query(..., description="Account name"),
    pair: Optional[str] = Query(None, description="Trading pair (e.g., SHARP-USDT)"),
    limit: int = Query(100, description="Max trades to return")
):
    """Get trade history for an account"""
    acc = exchange_manager.get_account(account)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{account}' not found")
    
    try:
        trades = await acc.get_trades(trading_pair=pair, limit=limit)
        return {
            "account": account,
            "trades": trades,
            "count": len(trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
