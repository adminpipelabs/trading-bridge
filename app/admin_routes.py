"""
Admin-only routes for client management and overview.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime, timezone
import logging

from app.database import get_db, Client, Wallet
from app.security import get_current_client
from app.api.client_data import sync_connectors_to_exchange_manager
from app.services.exchange import exchange_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/clients/overview")
async def admin_clients_overview(
    request: Request,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client)
):
    """
    Returns all clients with their key status, bot status, and plan.
    Admin only.
    """
    # Check admin access
    if current_client.role != "admin" and current_client.account_identifier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Use raw SQL for complex joins
        result = db.execute(text("""
            SELECT 
                c.id, c.name, c.account_identifier, c.chain, c.role,
                c.management_mode,
                tk.wallet_address, tk.added_by, tk.created_at as key_connected_at,
                CASE WHEN tk.id IS NOT NULL THEN true ELSE false END as has_key,
                (SELECT COUNT(*) FROM bots WHERE account = c.account_identifier) as bot_count,
                (SELECT health_status FROM bots WHERE account = c.account_identifier ORDER BY created_at DESC LIMIT 1) as bot_health,
                (SELECT status FROM bots WHERE account = c.account_identifier ORDER BY created_at DESC LIMIT 1) as bot_status
            FROM clients c
            LEFT JOIN trading_keys tk ON tk.client_id = c.id
            WHERE c.role = 'client' OR c.account_identifier != 'admin'
            ORDER BY c.created_at DESC
        """))
        
        rows = result.fetchall()
        
        clients = []
        for row in rows:
            client_dict = {
                "id": row.id,
                "name": row.name,
                "account_identifier": row.account_identifier,
                "chain": row.chain or "solana",
                "management_mode": row.management_mode or "unset",
                "has_key": row.has_key,
                "key_added_by": row.added_by if row.has_key else None,
                "key_connected_at": row.key_connected_at.isoformat() if row.key_connected_at else None,
                "wallet_address": row.wallet_address if row.has_key else None,
                "bot_count": row.bot_count or 0,
                "bot_health": row.bot_health,
                "bot_status": row.bot_status,
            }
            clients.append(client_dict)
        
        return {"clients": clients}
    
    except Exception as e:
        logger.error(f"Error fetching admin clients overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching client overview: {str(e)}")


@router.get("/clients/{client_id}/balances")
async def get_client_balances_admin(
    client_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client)
):
    """
    Admin: Get detailed balances for a client from all exchanges.
    Shows individual token balances (USDT, SHARP, etc.)
    """
    # Check admin access
    if current_client.role != "admin" and current_client.account_identifier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    account_identifier = client.account_identifier
    
    # Sync connectors to exchange_manager
    synced = await sync_connectors_to_exchange_manager(account_identifier, db)
    if not synced:
        return {
            "account": account_identifier,
            "balances": [],
            "total_usdt": 0.0,
            "message": "No connectors configured. Add BitMart API keys via admin UI."
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
        
        # Transform to array format with all tokens
        balances_array = []
        total_usdt = 0.0
        
        for exchange_name, exchange_balances in balances_raw.items():
            if isinstance(exchange_balances, dict) and "error" not in exchange_balances:
                for asset, balance_data in exchange_balances.items():
                    if isinstance(balance_data, dict):
                        total = float(balance_data.get("total", 0))
                        free = float(balance_data.get("free", 0))
                        used = float(balance_data.get("used", 0))
                        
                        # Calculate USD value: USDT/USDC = 1:1, others = 0
                        usd_value = total if asset in ["USDT", "USDC"] else 0
                        
                        balances_array.append({
                            "exchange": exchange_name,
                            "asset": asset,
                            "total": total,
                            "free": free,
                            "used": used,
                            "usd_value": usd_value
                        })
                        
                        # Sum USDT
                        if asset == "USDT":
                            total_usdt += total
        
        return {
            "account": account_identifier,
            "client_name": client.name,
            "balances": balances_array,
            "total_usdt": total_usdt,
            "token_count": len(balances_array)
        }
    except Exception as e:
        logger.error(f"Failed to get balances for client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {str(e)}")


@router.get("/notifications")
async def get_admin_notifications(
    request: Request,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client)
):
    """
    Get admin notifications.
    Admin only.
    """
    if current_client.role != "admin" and current_client.account_identifier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        query = "SELECT * FROM admin_notifications"
        if unread_only:
            query += " WHERE read = false"
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        result = db.execute(text(query), {"limit": limit})
        rows = result.fetchall()
        
        notifications = []
        for row in rows:
            notifications.append({
                "id": row.id,
                "type": row.type,
                "client_id": row.client_id,
                "message": row.message,
                "read": row.read,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })
        
        return {"notifications": notifications}
    
    except Exception as e:
        # Table might not exist yet
        if "does not exist" in str(e).lower() or "relation" in str(e).lower():
            return {"notifications": []}
        logger.error(f"Error fetching notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")


@router.get("/check-sharp-connectors")
async def check_sharp_connectors(db: Session = Depends(get_db)):
    """Check Sharp's BitMart connectors - diagnostic endpoint"""
    try:
        result = db.execute(text("""
            SELECT 
                c.id,
                c.name as connector_name,
                c.memo,
                c.api_key IS NOT NULL as has_api_key,
                c.api_secret IS NOT NULL as has_api_secret,
                cl.account_identifier,
                cl.name as client_name
            FROM connectors c
            LEFT JOIN clients cl ON cl.id = c.client_id
            WHERE cl.account_identifier LIKE '%sharp%'
               OR c.name ILIKE '%bitmart%'
            ORDER BY c.created_at DESC
        """))
        rows = result.fetchall()
        
        connectors = []
        for row in rows:
            connectors.append({
                "id": str(row[0]),
                "name": row[1],
                "memo": row[2],
                "has_api_key": row[3],
                "has_api_secret": row[4],
                "account_identifier": row[5],
                "client_name": row[6]
            })
        
        return {
            "found": len(connectors),
            "connectors": connectors
        }
    except Exception as e:
        logger.error(f"Error checking connectors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
