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
    logger.info(f"🔄 Syncing connectors for account: {account_identifier}")
    
    # Get client by account_identifier
    client = db.query(Client).filter(
        Client.account_identifier == account_identifier
    ).first()
    
    if not client:
        logger.error(f"❌ Client not found for account: {account_identifier}")
        return False
    
    logger.info(f"✅ Found client: {client.name} (ID: {client.id})")
    
    # Get or create account in exchange_manager
    account = exchange_manager.get_or_create_account(account_identifier)
    
    # Load connectors from database
    connectors = db.query(Connector).filter(
        Connector.client_id == client.id
    ).all()
    
    if not connectors:
        logger.error(f"❌ No connectors found for account: {account_identifier} (client_id: {client.id})")
        logger.error(f"   Client needs to add API keys via admin dashboard")
        return False
    
    logger.info(f"✅ Found {len(connectors)} connector(s) for {account_identifier}")
    
    # Add each connector to exchange_manager
    synced_count = 0
    for connector in connectors:
        connector_name = connector.name.lower()
        
        # Skip if already loaded (avoid re-adding)
        if connector_name in account.connectors:
            logger.debug(f"⏭️  Connector {connector_name} already loaded for {account_identifier}")
            synced_count += 1
            continue
        
        # Validate connector has required fields
        if not connector.api_key or not connector.api_secret:
            logger.warning(f"⚠️  Connector {connector.name} missing API key or secret - skipping")
            continue
        
        try:
            await account.add_connector(
                connector_name=connector.name,
                api_key=connector.api_key,
                api_secret=connector.api_secret,
                memo=connector.memo
            )
            logger.info(f"✅ Synced connector {connector.name} to exchange_manager for {account_identifier}")
            synced_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to sync connector {connector.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Continue with other connectors
    
    if synced_count == 0:
        logger.error(f"❌ No connectors successfully synced for {account_identifier}")
        return False
    
    logger.info(f"✅ Successfully synced {synced_count}/{len(connectors)} connector(s) for {account_identifier}")
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
    logger.info(f"📊 Portfolio request for wallet: {wallet_address}")
    
    # Look up client by wallet
    wallet_lower = wallet_address.lower()
    wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
    
    if not wallet:
        logger.error(f"❌ No wallet found for address: {wallet_address}")
        raise HTTPException(
            status_code=404,
            detail=f"No client found for wallet address {wallet_address}"
        )
    
    client = wallet.client
    account_identifier = client.account_identifier
    logger.info(f"✅ Found client: {client.name} (account: {account_identifier})")
    
    # Sync connectors to exchange_manager
    synced = await sync_connectors_to_exchange_manager(account_identifier, db)
    if not synced:
        logger.error(f"❌ Failed to sync connectors for {account_identifier}")
        # Check if connectors exist in DB
        connectors_check = db.query(Connector).filter(
            Connector.client_id == client.id
        ).all()
        
        if not connectors_check:
            return {
                "account": account_identifier,
                "balances": [],
                "total_usd": 0,
                "error": "NO_CONNECTORS",
                "message": "No API keys configured. Please add BitMart API keys via admin dashboard."
            }
        else:
            return {
                "account": account_identifier,
                "balances": [],
                "total_usd": 0,
                "error": "SYNC_FAILED",
                "message": f"Found {len(connectors_check)} connector(s) but failed to sync. Check API keys are valid."
            }
    
    # Get account from exchange_manager
    account = exchange_manager.get_account(account_identifier)
    if not account:
        logger.error(f"❌ Failed to get account from exchange_manager for {account_identifier}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create account in exchange_manager"
        )
    
    try:
        logger.info(f"🔍 Fetching balances for {account_identifier}...")
        balances_raw = await account.get_balances()
        logger.info(f"✅ Received balance data: {balances_raw}")
        
        # Transform nested balances to flat array format expected by frontend
        balances_array = []
        total_usd = 0.0
        
        for exchange_name, exchange_balances in balances_raw.items():
            if isinstance(exchange_balances, dict):
                if "error" in exchange_balances:
                    logger.error(f"❌ Exchange {exchange_name} returned error: {exchange_balances['error']}")
                    continue
                
                for asset, balance_data in exchange_balances.items():
                    if isinstance(balance_data, dict):
                        total = balance_data.get("total", 0)
                        free = balance_data.get("free", 0)
                        # Calculate USD value (USDT = 1:1, others = 0 for now)
                        usd_value = total if asset == "USDT" else 0
                        total_usd += usd_value
                        
                        balances_array.append({
                            "exchange": exchange_name,
                            "asset": asset,
                            "free": free,
                            "total": total,
                            "used": balance_data.get("used", 0),
                            "usd_value": usd_value
                        })
                        logger.info(f"  💰 {exchange_name} {asset}: {total} (free: {free})")
        
        if not balances_array:
            logger.warning(f"⚠️  No balances found for {account_identifier}")
        
        # Get bot counts for portfolio (query database directly)
        try:
            bots = db.query(Bot).filter(Bot.account == account_identifier).all()
            active_bots = sum(1 for b in bots if b.status == "running")
            total_bots = len(bots)
            logger.info(f"📊 Bot counts: {active_bots}/{total_bots} active")
        except Exception as e:
            logger.warning(f"Failed to get bot counts: {e}")
            active_bots = 0
            total_bots = 0
        
        logger.info(f"✅ Returning portfolio data: {len(balances_array)} balances, ${total_usd:.2f} total USD")
        
        return {
            "account": account_identifier,
            "balances": balances_array,
            "total_usd": total_usd,
            "total_pnl": 0,  # TODO: Calculate from trades
            "active_bots": active_bots,
            "total_bots": total_bots
        }
    except Exception as e:
        logger.error(f"❌ Failed to get balances for {account_identifier}: {e}")
        import traceback
        logger.error(traceback.format_exc())
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


@router.get("/debug")
async def debug_client_setup(
    wallet_address: str = Query(..., description="Client wallet address"),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to check client setup status.
    Returns detailed information about connectors, sync status, etc.
    """
    wallet_lower = wallet_address.lower()
    wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
    
    if not wallet:
        return {
            "error": "WALLET_NOT_FOUND",
            "message": f"No client found for wallet address {wallet_address}"
        }
    
    client = wallet.client
    connectors = db.query(Connector).filter(
        Connector.client_id == client.id
    ).all()
    
    connector_info = []
    for conn in connectors:
        connector_info.append({
            "name": conn.name,
            "has_api_key": bool(conn.api_key),
            "has_api_secret": bool(conn.api_secret),
            "has_memo": bool(conn.memo),
            "created_at": conn.created_at.isoformat() if conn.created_at else None
        })
    
    # Check if synced to exchange_manager
    account = exchange_manager.get_account(client.account_identifier)
    synced_connectors = list(account.connectors.keys()) if account else []
    
    return {
        "client": {
            "id": client.id,
            "name": client.name,
            "account_identifier": client.account_identifier
        },
        "connectors_in_db": len(connectors),
        "connectors_detail": connector_info,
        "synced_to_exchange_manager": len(synced_connectors),
        "synced_connectors": synced_connectors,
        "wallet_address": wallet_address
    }


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
        formatted_pair = None
        if trading_pair:
            formatted_pair = trading_pair.replace("-", "/").replace("_", "/")
        
        trades = await account.get_trades(trading_pair=formatted_pair, limit=limit)
        return {
            "account": account_identifier,
            "trades": trades,
            "count": len(trades)
        }
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volume")
async def get_client_volume(
    wallet_address: str = Query(..., description="Client wallet address"),
    days: int = Query(7, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Get trading volume for a client.
    Calculated from trade history.
    """
    # Get trades first
    trades_data = await get_client_trades(wallet_address, limit=1000, days=days, db=db)
    trades = trades_data.get("trades", [])
    
    total_volume = sum(float(t.get("cost", 0)) for t in trades)
    
    return {
        "account": trades_data.get("account"),
        "total_volume": total_volume,
        "trade_count": len(trades),
        "days": days
    }


@router.get("/pnl")
async def get_client_pnl(
    wallet_address: str = Query(..., description="Client wallet address"),
    days: int = Query(7, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Get profit & loss for a client.
    Calculated from trade history.
    """
    # Get trades
    trades_data = await get_client_trades(wallet_address, limit=1000, days=days, db=db)
    trades = trades_data.get("trades", [])
    
    # TODO: Calculate P&L from trades
    # For now, return 0
    return {
        "account": trades_data.get("account"),
        "total_pnl": 0,
        "trade_count": len(trades),
        "days": days
    }
