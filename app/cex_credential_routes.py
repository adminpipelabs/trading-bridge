"""
API routes for managing CEX exchange credentials.
"""

import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional

from app.cex_volume_bot import encrypt_credential
from app.database import get_db, Session
from app.auth_routes import get_current_user

logger = logging.getLogger("cex_credentials")

router = APIRouter(prefix="/exchanges", tags=["exchanges"])


class AddCredentialsRequest(BaseModel):
    exchange: str           # bitmart, coinstore, binance
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None


class CredentialStatus(BaseModel):
    exchange: str
    connected: bool
    created_at: Optional[str] = None


@router.post("/credentials")
async def add_exchange_credentials(
    payload: AddCredentialsRequest, 
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Add or update exchange API credentials for a client.
    Credentials are encrypted before storage.
    """
    # Validate exchange
    supported = ["bitmart", "coinstore", "binance", "kucoin"]
    if payload.exchange.lower() not in supported:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported exchange. Supported: {supported}"
        )
    
    try:
        # Encrypt credentials
        api_key_enc = encrypt_credential(payload.api_key.strip())
        api_secret_enc = encrypt_credential(payload.api_secret.strip())
        passphrase_enc = None
        if payload.passphrase:
            passphrase_enc = encrypt_credential(payload.passphrase.strip())
        
        # Use raw SQL since exchange_credentials table may not be in SQLAlchemy model yet
        from sqlalchemy import text
        
        await db.execute(text("""
            INSERT INTO exchange_credentials 
                (client_id, exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, updated_at)
            VALUES (:client_id, :exchange, :api_key, :api_secret, :passphrase, :updated_at)
            ON CONFLICT (client_id, exchange)
            DO UPDATE SET 
                api_key_encrypted = :api_key,
                api_secret_encrypted = :api_secret,
                passphrase_encrypted = :passphrase,
                updated_at = :updated_at
        """), {
            "client_id": user.client_id,
            "exchange": payload.exchange.lower(),
            "api_key": api_key_enc,
            "api_secret": api_secret_enc,
            "passphrase": passphrase_enc,
            "updated_at": datetime.now(timezone.utc)
        })
        db.commit()
        
        logger.info(f"Client {user.client_id} added credentials for {payload.exchange}")
        return {"success": True, "message": f"{payload.exchange} credentials saved"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save credentials")


@router.get("/credentials")
async def list_exchange_credentials(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    List connected exchanges for the client (without revealing keys).
    """
    from sqlalchemy import text
    
    rows = db.execute(text("""
        SELECT exchange, created_at FROM exchange_credentials
        WHERE client_id = :client_id
    """), {"client_id": user.client_id}).fetchall()
    
    return {
        "exchanges": [
            {
                "exchange": row[0],
                "connected": True,
                "created_at": row[1].isoformat() if row[1] else None
            }
            for row in rows
        ]
    }


@router.delete("/credentials/{exchange}")
async def remove_exchange_credentials(
    exchange: str, 
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Remove exchange credentials. Will stop any bots using this exchange.
    """
    from sqlalchemy import text
    
    # Check if any bots are using this exchange
    bots = db.execute(text("""
        SELECT id, name FROM bots 
        WHERE account = (SELECT account_identifier FROM clients WHERE id = :client_id)
          AND exchange = :exchange
          AND status = 'running'
    """), {
        "client_id": user.client_id,
        "exchange": exchange.lower()
    }).fetchall()
    
    if bots:
        # Stop the bots first
        db.execute(text("""
            UPDATE bots SET status = 'stopped', health_status = 'stopped',
                health_message = 'Exchange credentials removed'
            WHERE account = (SELECT account_identifier FROM clients WHERE id = :client_id)
              AND exchange = :exchange
        """), {
            "client_id": user.client_id,
            "exchange": exchange.lower()
        })
    
    # Remove credentials
    db.execute(text("""
        DELETE FROM exchange_credentials
        WHERE client_id = :client_id AND exchange = :exchange
    """), {
        "client_id": user.client_id,
        "exchange": exchange.lower()
    })
    db.commit()
    
    return {
        "success": True,
        "message": f"{exchange} credentials removed",
        "bots_stopped": len(bots)
    }


# ──────────────────────────────────────────────────────────────
# Admin endpoint to add credentials on behalf of client
# ──────────────────────────────────────────────────────────────

@router.post("/admin/{client_id}/credentials")
async def admin_add_credentials(
    client_id: str, 
    payload: AddCredentialsRequest, 
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Admin: Add exchange credentials on behalf of a client.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        api_key_enc = encrypt_credential(payload.api_key.strip())
        api_secret_enc = encrypt_credential(payload.api_secret.strip())
        passphrase_enc = None
        if payload.passphrase:
            passphrase_enc = encrypt_credential(payload.passphrase.strip())
        
        from sqlalchemy import text
        
        db.execute(text("""
            INSERT INTO exchange_credentials 
                (client_id, exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, updated_at)
            VALUES (:client_id, :exchange, :api_key, :api_secret, :passphrase, :updated_at)
            ON CONFLICT (client_id, exchange)
            DO UPDATE SET 
                api_key_encrypted = :api_key,
                api_secret_encrypted = :api_secret,
                passphrase_encrypted = :passphrase,
                updated_at = :updated_at
        """), {
            "client_id": client_id,
            "exchange": payload.exchange.lower(),
            "api_key": api_key_enc,
            "api_secret": api_secret_enc,
            "passphrase": passphrase_enc,
            "updated_at": datetime.now(timezone.utc)
        })
        db.commit()
        
        logger.info(f"Admin added {payload.exchange} credentials for client {client_id}")
        return {"success": True, "message": f"{payload.exchange} credentials saved for client"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save credentials")
