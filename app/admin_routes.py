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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


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


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client)
):
    """
    Mark a notification as read.
    Admin only.
    """
    if current_client.role != "admin" and current_client.account_identifier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        db.execute(text("""
            UPDATE admin_notifications 
            SET read = true 
            WHERE id = :id
        """), {"id": notification_id})
        db.commit()
        
        return {"success": True}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating notification: {str(e)}")
