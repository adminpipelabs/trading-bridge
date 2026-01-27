"""
Exchange Data Routes
Production endpoints to query BitMart and other exchanges for dashboard data.
Keys are stored in PostgreSQL connectors table.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.database import get_db, Client, Connector, Bot
from app.services.exchange import exchange_manager
from app.api.client_data import sync_connectors_to_exchange_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exchange", tags=["Exchange Data"])


@router.get("/balance/{account}")
async def get_balance(account: str, db: Session = Depends(get_db)):
    """
    Get USDT and token balances for an account.
    Returns balances from all connectors (exchanges) configured for this account.
    """
    # Sync connectors from DB to exchange_manager
    synced = await sync_connectors_to_exchange_manager(account, db)
    if not synced:
        return {
            "account": account,
            "balances": {},
            "total_usdt": 0.0,
            "message": "No connectors configured"
        }
    
    # Get account from exchange_manager
    acc = exchange_manager.get_account(account)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{account}' not found")
    
    try:
        balances_raw = await acc.get_balances()
        
        # Transform to frontend format
        balances = {}
        total_usdt = 0.0
        
        for exchange_name, exchange_balances in balances_raw.items():
            if isinstance(exchange_balances, dict) and "error" not in exchange_balances:
                balances[exchange_name] = {}
                for asset, balance_data in exchange_balances.items():
                    if isinstance(balance_data, dict):
                        total = float(balance_data.get("total", 0))
                        balances[exchange_name][asset] = {
                            "total": total,
                            "free": float(balance_data.get("free", 0)),
                            "used": float(balance_data.get("used", 0))
                        }
                        # Sum USDT
                        if asset == "USDT":
                            total_usdt += total
        
        return {
            "account": account,
            "balances": balances,
            "total_usdt": total_usdt
        }
    except Exception as e:
        logger.error(f"Failed to get balance for {account}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/{account}")
async def get_trades(
    account: str,
    pair: Optional[str] = Query(None, description="Trading pair filter (e.g., SHARP-USDT)"),
    limit: int = Query(100, description="Max trades to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent trades for an account.
    """
    # Sync connectors from DB to exchange_manager
    synced = await sync_connectors_to_exchange_manager(account, db)
    if not synced:
        return {
            "account": account,
            "trades": [],
            "count": 0
        }
    
    # Get account from exchange_manager
    acc = exchange_manager.get_account(account)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{account}' not found")
    
    try:
        # Format pair if provided (SHARP-USDT -> SHARP/USDT for ccxt)
        formatted_pair = None
        if pair:
            formatted_pair = str(pair).replace("-", "/")
        trades_raw = await acc.get_trades(trading_pair=formatted_pair, limit=limit)
        
        # Transform to frontend format
        trades = []
        for trade in trades_raw:
            symbol = trade.get("symbol", "")
            trading_pair = symbol.replace("/", "-") if "/" in symbol else symbol
            
            trades.append({
                "trading_pair": trading_pair,
                "exchange": trade.get("connector", "unknown"),
                "side": trade.get("side", "").lower(),
                "amount": float(trade.get("amount", 0)),
                "price": float(trade.get("price", 0)),
                "cost": float(trade.get("cost", 0)),
                "timestamp": trade.get("timestamp", 0),
                "id": trade.get("id"),
                "order_id": trade.get("order_id")
            })
        
        # Sort by timestamp descending
        trades.sort(key=lambda t: t.get("timestamp", 0), reverse=True)
        
        return {
            "account": account,
            "trades": trades,
            "count": len(trades)
        }
    except Exception as e:
        logger.error(f"Failed to get trades for {account}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pnl/{account}")
async def get_pnl(
    account: str,
    days: int = Query(7, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Calculate P&L (profit and loss) for an account.
    """
    # Get trades first
    trades_data = await get_trades(account, pair=None, limit=1000, db=db)
    trades = trades_data.get("trades", [])
    
    # Filter by days if needed
    if days > 0:
        cutoff_time = (datetime.utcnow() - timedelta(days=days)).timestamp() * 1000
        trades = [t for t in trades if t.get("timestamp", 0) >= cutoff_time]
    
    # Calculate P&L
    # Simple calculation: track positions and realized P&L
    positions = {}  # {pair: {amount, avg_price, cost}}
    total_pnl = 0.0
    pnl_by_pair = {}
    
    for trade in sorted(trades, key=lambda t: t.get("timestamp", 0)):
        pair = trade.get("trading_pair", "unknown")
        side = trade.get("side", "").lower()
        amount = float(trade.get("amount", 0))
        price = float(trade.get("price", 0))
        
        if pair not in positions:
            positions[pair] = {"amount": 0, "avg_price": 0, "cost": 0}
        
        pos = positions[pair]
        
        if side == "buy":
            # Add to position
            total_cost = pos["cost"] + (amount * price)
            pos["amount"] += amount
            pos["cost"] = total_cost
            pos["avg_price"] = total_cost / pos["amount"] if pos["amount"] > 0 else 0
        elif side == "sell":
            # Realize P&L
            if pos["amount"] > 0:
                realized_pnl = (price - pos["avg_price"]) * min(amount, pos["amount"])
                total_pnl += realized_pnl
                pnl_by_pair[pair] = pnl_by_pair.get(pair, 0) + realized_pnl
                pos["amount"] -= min(amount, pos["amount"])
                if pos["amount"] == 0:
                    pos["cost"] = 0
                    pos["avg_price"] = 0
    
    return {
        "account": account,
        "total": total_pnl,
        "pnl_by_pair": pnl_by_pair,
        "days": days,
        "trade_count": len(trades)
    }


@router.get("/volume/{pair}")
async def get_volume(
    pair: str,
    exchange: str = Query("bitmart", description="Exchange name")
):
    """
    Get 24h volume for a trading pair (public endpoint, free).
    """
    try:
        # Format pair (SHARP-USDT -> SHARP/USDT)
        formatted_pair = pair.replace("-", "/")
        
        # Get price/volume from exchange (public, no auth needed)
        price = await exchange_manager.get_price(exchange, formatted_pair)
        
        # For now, return basic data
        # In production, you might want to fetch 24h ticker data
        return {
            "pair": pair,
            "exchange": exchange,
            "price": price,
            "volume_24h": 0,  # TODO: Fetch from exchange ticker
            "message": "Volume data requires exchange ticker API"
        }
    except Exception as e:
        logger.error(f"Failed to get volume for {pair}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{account}")
async def get_dashboard(account: str, db: Session = Depends(get_db)):
    """
    Get all dashboard data in one call (cost-optimized).
    Returns balance, trades, P&L, and volume in a single response.
    """
    try:
        # Get all data in parallel
        balance_data = await get_balance(account, db)
        trades_data = await get_trades(account, pair=None, limit=100, db=db)
        pnl_data = await get_pnl(account, days=7, db=db)
        
        # Get bot counts
        try:
            bots = db.query(Bot).filter(Bot.account == account).all()
            active_bots = sum(1 for b in bots if b.status == "running")
            total_bots = len(bots)
        except:
            active_bots = 0
            total_bots = 0
        
        # Calculate volume from trades
        trades = trades_data.get("trades", [])
        total_volume = sum(float(t.get("cost", 0)) for t in trades)
        
        # Transform balances to array format for frontend
        balances_array = []
        balances_dict = balance_data.get("balances", {})
        for exchange_name, exchange_balances in balances_dict.items():
            if isinstance(exchange_balances, dict):
                for asset, balance_info in exchange_balances.items():
                    balances_array.append({
                        "exchange": exchange_name,
                        "asset": asset,
                        "free": balance_info.get("free", 0),
                        "total": balance_info.get("total", 0),
                        "used": balance_info.get("used", 0),
                        "usd_value": balance_info.get("total", 0) if asset == "USDT" else 0
                    })
        
        return {
            "account": account,
            "balance": {
                "total_usdt": balance_data.get("total_usdt", 0),
                "balances": balances_array
            },
            "pnl": {
                "total": pnl_data.get("total", 0),
                "by_pair": pnl_data.get("pnl_by_pair", {})
            },
            "volume": {
                "traded": total_volume,
                "trade_count": len(trades)
            },
            "recent_trades": trades[:10],  # Last 10 trades
            "bots": {
                "active": active_bots,
                "total": total_bots
            }
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard data for {account}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
