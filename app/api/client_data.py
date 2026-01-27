"""
Client-facing API endpoints for balances, trades, portfolio, volume
Syncs connectors from database to exchange_manager on-demand
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
import logging

from app.database import get_db, Client, Wallet, Connector, Bot
from app.services.exchange import exchange_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["Client Data"])


async def sync_connectors_to_exchange_manager(account_identifier: str, db: Session):
    """
    Load connectors from database into exchange_manager for an account.
    This ensures exchange_manager has the API keys needed to query exchanges.
    """
    # Get client by account_identifier
    client = db.query(Client).filter(
        Client.account_identifier == account_identifier
    ).first()
    
    if not client:
        logger.warning(f"Client not found for account: {account_identifier}")
        return False
    
    # Get or create account in exchange_manager
    account = exchange_manager.get_or_create_account(account_identifier)
    
    # Load connectors from database
    connectors = db.query(Connector).filter(
        Connector.client_id == client.id
    ).all()
    
    if not connectors:
        logger.warning(f"No connectors found for account: {account_identifier}")
        return False
    
    # Add each connector to exchange_manager
    for connector in connectors:
        connector_name = connector.name.lower()
        
        # Skip if already loaded (avoid re-adding)
        if connector_name in account.connectors:
            logger.debug(f"Connector {connector_name} already loaded for {account_identifier}")
            continue
        
        try:
            await account.add_connector(
                connector_name=connector.name,
                api_key=connector.api_key,
                api_secret=connector.api_secret,
                memo=connector.memo
            )
            logger.info(f"✅ Synced connector {connector.name} to exchange_manager for {account_identifier}")
        except Exception as e:
            logger.error(f"Failed to sync connector {connector.name}: {e}")
            # Continue with other connectors
    
    return True


@router.get("/portfolio")
async def get_client_portfolio(
    wallet_address: str = Query(..., description="Client wallet address"),
    db: Session = Depends(get_db)
):
    """
    Get portfolio balances for a client by wallet address.
    Syncs connectors from DB to exchange_manager, then queries exchanges.
    """
    # Look up client by wallet
    wallet_lower = wallet_address.lower()
    wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
    
    if not wallet:
        raise HTTPException(
            status_code=404,
            detail=f"No client found for wallet address {wallet_address}"
        )
    
    client = wallet.client
    account_identifier = client.account_identifier
    
    # Sync connectors to exchange_manager
    synced = await sync_connectors_to_exchange_manager(account_identifier, db)
    if not synced:
        return {
            "account": account_identifier,
            "balances": {},
            "message": "No connectors configured. Add API keys in admin dashboard."
        }
    
    # Get account from exchange_manager
    account = exchange_manager.get_account(account_identifier)
    if not account:
        raise HTTPException(
            status_code=500,
            detail="Failed to create account in exchange_manager"
        )
    
    try:
        balances_raw = await account.get_balances()
        
        # Transform nested balances to flat array format expected by frontend
        balances_array = []
        total_usd = 0.0
        
        for exchange_name, exchange_balances in balances_raw.items():
            if isinstance(exchange_balances, dict) and "error" not in exchange_balances:
                for asset, balance_data in exchange_balances.items():
                    if isinstance(balance_data, dict):
                        balances_array.append({
                            "exchange": exchange_name,
                            "asset": asset,
                            "free": balance_data.get("free", 0),
                            "total": balance_data.get("total", 0),
                            "used": balance_data.get("used", 0),
                            "usd_value": 0  # TODO: Calculate from prices
                        })
        
        # Get bot counts for portfolio (query database directly)
        try:
            bots = db.query(Bot).filter(Bot.account == account_identifier).all()
            active_bots = sum(1 for b in bots if b.status == "running")
            total_bots = len(bots)
        except Exception as e:
            logger.warning(f"Failed to get bot counts: {e}")
            active_bots = 0
            total_bots = 0
        
        return {
            "account": account_identifier,
            "balances": balances_array,
            "total_usd": total_usd,
            "total_pnl": 0,  # TODO: Calculate from trades
            "active_bots": active_bots,
            "total_bots": total_bots
        }
    except Exception as e:
        logger.error(f"Failed to get balances: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {str(e)}")


@router.get("/balances")
async def get_client_balances(
    wallet_address: str = Query(..., description="Client wallet address"),
    db: Session = Depends(get_db)
):
    """
    Get balances for a client.
    Returns array format expected by frontend.
    """
    portfolio = await get_client_portfolio(wallet_address, db)
    return portfolio["balances"]  # Return array directly


@router.get("/trades")
async def get_client_trades(
    wallet_address: str = Query(..., description="Client wallet address"),
    trading_pair: Optional[str] = Query(None, description="Filter by trading pair (e.g., SHARP-USDT)"),
    limit: int = Query(100, description="Max trades to return"),
    days: int = Query(7, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Get trade history for a client by wallet address.
    """
    # Look up client by wallet
    wallet_lower = wallet_address.lower()
    wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
    
    if not wallet:
        raise HTTPException(
            status_code=404,
            detail=f"No client found for wallet address {wallet_address}"
        )
    
    client = wallet.client
    account_identifier = client.account_identifier
    
    # Sync connectors to exchange_manager
    synced = await sync_connectors_to_exchange_manager(account_identifier, db)
    if not synced:
        return {
            "account": account_identifier,
            "trades": [],
            "count": 0,
            "message": "No connectors configured"
        }
    
    # Get account from exchange_manager
    account = exchange_manager.get_account(account_identifier)
    if not account:
        raise HTTPException(
            status_code=500,
            detail="Failed to create account in exchange_manager"
        )
    
    try:
        # Format trading_pair if provided (SHARP-USDT -> SHARP/USDT for ccxt)
        formatted_pair = trading_pair.replace("-", "/") if trading_pair else None
        trades = await account.get_trades(trading_pair=formatted_pair, limit=limit)
        
        # Filter by days if needed (exchange_manager may not support this)
        # For now, return all trades (exchanges typically return recent trades)
        # Transform trades to frontend format
        trades_transformed = []
        for trade in trades:
            # Convert symbol format: SHARP/USDT -> SHARP-USDT
            symbol = trade.get("symbol", "")
            trading_pair = symbol.replace("/", "-") if "/" in symbol else symbol
            
            trades_transformed.append({
                "trading_pair": trading_pair,
                "side": trade.get("side", "").lower(),
                "amount": float(trade.get("amount", 0)),
                "price": float(trade.get("price", 0)),
                "timestamp": trade.get("timestamp", 0),
                "exchange": trade.get("connector", "unknown"),  # Rename connector -> exchange
                "id": trade.get("id"),
                "order_id": trade.get("order_id"),
                "cost": trade.get("cost", 0),
                "fee": trade.get("fee", {})
            })
        
        # Sort by timestamp descending (most recent first)
        trades_sorted = sorted(trades_transformed, key=lambda t: t.get("timestamp", 0), reverse=True)
        
        return trades_sorted  # Return array directly (frontend expects array, not object)
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trades: {str(e)}")


@router.get("/volume")
async def get_client_volume(
    wallet_address: str = Query(..., description="Client wallet address"),
    days: int = Query(7, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Get trading volume for a client.
    """
    # Get trades first
    trades = await get_client_trades(wallet_address, limit=1000, days=days, db=db)
    
    # Calculate volume
    total_volume = 0.0
    volume_by_pair = {}
    
    for trade in trades:
        pair = trade.get("trading_pair", "unknown")
        amount = float(trade.get("amount", 0))
        price = float(trade.get("price", 0))
        volume = amount * price
        
        total_volume += volume
        volume_by_pair[pair] = volume_by_pair.get(pair, 0) + volume
    
    return {
        "total_volume": total_volume,  # Rename total_volume_usd -> total_volume
        "trade_count": len(trades),    # Add trade_count
        "volume_by_pair": volume_by_pair,
        "days": days
    }


@router.get("/pnl")
async def get_client_pnl(
    wallet_address: str = Query(..., description="Client wallet address"),
    days: int = Query(7, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Get P&L (profit and loss) for a client.
    Calculated from trade history.
    """
    # Get trades
    trades_data = await get_client_trades(wallet_address, limit=1000, days=days, db=db)
    trades = trades_data.get("trades", [])
    
    # Calculate P&L
    # Simple calculation: sum of (sell_price - buy_price) * amount
    # This is simplified - real P&L needs to track positions
    
    total_pnl = 0.0
    pnl_by_pair = {}
    
    # Group trades by pair and calculate P&L
    positions = {}  # {pair: {amount, avg_price}}
    
    for trade in sorted(trades, key=lambda t: t.get("timestamp", 0)):
        pair = trade.get("symbol", trade.get("pair", "unknown"))
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
        "account": trades_data.get("account"),
        "total_pnl_usd": total_pnl,
        "pnl_by_pair": pnl_by_pair,
        "days": days
    }
