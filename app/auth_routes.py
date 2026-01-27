"""
Authentication routes for Trading Bridge
Provides wallet-based authentication endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from eth_account.messages import encode_defunct
from web3 import Web3
import os
import httpx
import logging

from app.database import get_db, Client, Wallet
from fastapi import Depends
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

w3 = Web3()

# Request/Response Models
class VerifyRequest(BaseModel):
    wallet_address: str
    signature: str
    message: str

class VerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """Verify Ethereum wallet signature"""
    try:
        wallet_address = Web3.to_checksum_address(wallet_address)
        message_hash = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == wallet_address.lower()
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


@router.get("/message/{wallet_address}")
def get_auth_message(wallet_address: str):
    """
    Get authentication message for wallet signature
    Returns a message that the client must sign to prove wallet ownership
    """
    timestamp = int(datetime.utcnow().timestamp())
    message = f"Sign this message to login to Pipe Labs Dashboard.\n\nWallet: {wallet_address}\nTimestamp: {timestamp}"
    
    return {
        "message": message,
        "timestamp": timestamp
    }


@router.post("/verify", response_model=VerifyResponse)
def verify_signature(request: VerifyRequest, db: Session = Depends(get_db)):
    """
    Verify wallet signature and authenticate user
    Auto-creates Client if wallet exists in trading-bridge but not in local DB
    """
    # Verify signature
    if not verify_wallet_signature(request.wallet_address, request.message, request.signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Normalize wallet address
    wallet_address = Web3.to_checksum_address(request.wallet_address)
    wallet_lower = wallet_address.lower()
    
    # Check if Wallet exists (links to Client)
    wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
    
    if not wallet:
        # Wallet not found - reject login
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Wallet address {wallet_address} is not registered. Please contact your admin to create your account."
        )
    
    # Get the Client associated with this wallet
    client = db.query(Client).filter(Client.id == wallet.client_id).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Client record not found for registered wallet"
        )
    
    # Create a simple access token (in production, use JWT)
    # For now, return a token based on wallet address
    import hashlib
    token_data = f"{wallet_address}:{datetime.utcnow().timestamp()}"
    access_token = hashlib.sha256(token_data.encode()).hexdigest()
    
    return VerifyResponse(
        access_token=access_token,
        user={
            "id": str(client.id),
            "wallet_address": client.wallet_address,
            "name": client.name,
            "role": "client",
            "is_active": True
        }
    )
