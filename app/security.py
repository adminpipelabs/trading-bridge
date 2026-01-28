"""
Security utilities for authentication and authorization
"""
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db, Client, Wallet

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user from token.
    For now, we'll use wallet_address from token or header.
    In production, decode JWT token.
    """
    # Try to get token from Bearer token or Authorization header
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid token."
        )
    
    # For now, token is wallet_address hash
    # In production, decode JWT and extract wallet_address
    # For this implementation, we'll require wallet_address to be passed
    # or extract from token if it's a JWT
    
    # Temporary: Since we don't have JWT yet, we'll require wallet_address header
    # This is a security improvement but not perfect - proper JWT is needed
    return None  # Will be handled by get_current_client


def get_current_client(
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current client from wallet address.
    This is a temporary solution - proper JWT authentication should be implemented.
    """
    # Try to get wallet from header
    if not wallet_address:
        # Try to extract from Authorization token (if it contains wallet info)
        # For now, require wallet_address header
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide X-Wallet-Address header."
        )
    
    wallet_lower = wallet_address.lower()
    wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
    
    if not wallet:
        raise HTTPException(
            status_code=403,
            detail="Wallet address not registered"
        )
    
    client = wallet.client
    return client


def require_account_access(
    requested_account: Optional[str],
    current_client: Client = Depends(get_current_client)
):
    """
    Verify that the current user can access the requested account.
    - Admin users can access any account
    - Client users can only access their own account
    """
    # Admin can access all accounts
    if current_client.account_identifier == "admin" or current_client.role == "admin":
        return current_client
    
    # Client can only access their own account
    if requested_account and requested_account != current_client.account_identifier:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. You can only access your own account ({current_client.account_identifier})"
        )
    
    # If no account specified, return client's own account
    if not requested_account:
        return current_client
    
    return current_client
