"""
Client management routes with PostgreSQL persistence.
Wallet-to-account mapping for bot filtering.
"""
from fastapi import APIRouter, HTTPException, Depends
from starlette.requests import Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import re
import logging

from app.database import get_db, Client, Wallet, Connector, init_db
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])


class WalletInfo(BaseModel):
    chain: str = Field(..., description="Chain type: 'evm' or 'solana'")
    address: str = Field(..., description="Wallet address")


class ConnectorInfo(BaseModel):
    name: str = Field(..., description="Connector name: 'bitmart', 'jupiter', etc.")
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    memo: Optional[str] = None


class CreateClientRequest(BaseModel):
    name: str = Field(..., description="Client display name")
    account_identifier: Optional[str] = Field(None, description="Unique account ID for bot association")
    wallets: List[WalletInfo] = Field(default_factory=list)
    connectors: List[ConnectorInfo] = Field(default_factory=list)


class ClientResponse(BaseModel):
    id: str
    name: str
    account_identifier: str
    wallets: List[dict]
    connectors: List[dict]
    created_at: str


def generate_account_identifier(name: str) -> str:
    """Generate a valid account identifier from client name."""
    sanitized = re.sub(r'[^a-z0-9]+', '_', name.lower())
    sanitized = sanitized.strip('_')
    return f"client_{sanitized}"


@router.post("/create", response_model=ClientResponse)
def create_client(request: CreateClientRequest, db: Session = Depends(get_db)):
    """Create a new client with account identifier for bot association."""
    client_id = str(uuid.uuid4())
    
    account_identifier = request.account_identifier
    if not account_identifier:
        account_identifier = generate_account_identifier(request.name)
    
    # Check if account_identifier already exists
    existing = db.query(Client).filter(Client.account_identifier == account_identifier).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Account identifier '{account_identifier}' already exists"
        )
    
    # Create client
    client = Client(
        id=client_id,
        name=request.name,
        account_identifier=account_identifier,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(client)
    
    # Add wallets
    wallet_objs = []
    for wallet_info in request.wallets:
        # Store addresses in original case (both EVM and Solana)
        # Solana addresses are case-sensitive, EVM addresses can be stored in original case too
        wallet = Wallet(
            id=str(uuid.uuid4()),
            client_id=client_id,
            chain=wallet_info.chain,
            address=wallet_info.address,  # Store in original case
            created_at=datetime.utcnow()
        )
        db.add(wallet)
        wallet_objs.append({
            "id": wallet.id,
            "chain": wallet.chain,
            "address": wallet.address,
            "created_at": wallet.created_at.isoformat()
        })
    
    # Add connectors
    connector_objs = []
    for connector_info in request.connectors:
        connector = Connector(
            id=str(uuid.uuid4()),
            client_id=client_id,
            name=connector_info.name,
            api_key=connector_info.api_key,
            api_secret=connector_info.api_secret,
            memo=connector_info.memo,
            created_at=datetime.utcnow()
        )
        db.add(connector)
        connector_objs.append({
            "id": connector.id,
            "name": connector.name,
            "api_key": connector.api_key,
            "api_secret": connector.api_secret,
            "memo": connector.memo,
            "created_at": connector.created_at.isoformat()
        })
    
    try:
        db.commit()
        logger.info(f"Created client: {client_id} with account_identifier: {account_identifier}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create client: {str(e)}")
    
    return {
        "id": client_id,
        "name": client.name,
        "account_identifier": client.account_identifier,
        "wallets": wallet_objs,
        "connectors": connector_objs,
        "created_at": client.created_at.isoformat()
    }


@router.get("", response_model=dict)
def list_clients(db: Session = Depends(get_db)):
    """List all clients - returns frontend-compatible format."""
    # Eagerly load relationships to avoid lazy loading issues
    clients = db.query(Client).options(
        joinedload(Client.wallets),
        joinedload(Client.connectors)
    ).all()
    
    result = []
    for client in clients:
        # Get primary wallet address (from wallets relationship or legacy field)
        primary_wallet = client.wallet_address
        primary_wallet_type = client.wallet_type
        if not primary_wallet and client.wallets:
            primary_wallet = client.wallets[0].address
            primary_wallet_type = client.wallets[0].chain.upper()
        
        wallets = [{"id": w.id, "chain": w.chain, "address": w.address} for w in client.wallets]
        connectors = [{"id": c.id, "name": c.name, "api_key": c.api_key, "api_secret": c.api_secret, "memo": c.memo} for c in client.connectors]
        
        # Frontend-compatible response
        result.append({
            "id": client.id,
            "name": client.name,
            "account_identifier": client.account_identifier,
            # Frontend-expected fields
            "wallet_address": primary_wallet,
            "wallet_type": primary_wallet_type or "EVM",
            "email": client.email,
            "password_hash": client.password_hash,  # Usually not returned, but field exists
            "status": client.status or "active",
            "tier": client.tier,
            "role": client.role or "client",
            "settings": client.settings or {},
            # New schema fields
            "wallets": wallets,
            "connectors": connectors,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None
        })
    
    # Return format compatible with both frontend (array) and Pipe Labs backend (object)
    # Frontend code does: (data || []) which works with both formats
    return {"clients": result}


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get a specific client by ID."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    wallets = [{"id": w.id, "chain": w.chain, "address": w.address} for w in client.wallets]
    connectors = [{"id": c.id, "name": c.name, "api_key": c.api_key, "api_secret": c.api_secret, "memo": c.memo} for c in client.connectors]
    
    return {
        "id": client.id,
        "name": client.name,
        "account_identifier": client.account_identifier,
        "wallets": wallets,
        "connectors": connectors,
        "created_at": client.created_at.isoformat()
    }


@router.get("/by-wallet/{wallet_address}", response_model=dict)
def get_client_by_wallet(
    wallet_address: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Look up client by wallet address.
    Returns client info including account_identifier for bot filtering.
    
    Authorization: Clients can only look up their own wallet. Admins can look up any wallet.
    """
    
    # Get requesting wallet from header
    requesting_wallet = request.headers.get("X-Wallet-Address") if request else None
    
    # Try both original case and lowercase for backward compatibility with existing data
    # New entries are stored in original case, but old entries might be lowercase
    wallet = db.query(Wallet).filter(
        (Wallet.address == wallet_address) | (Wallet.address == wallet_address.lower())
    ).first()
    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="No client found for this wallet address"
        )
    
    client = wallet.client
    
    # Authorization check: Client can only look up their own wallet
    # Admins can look up any wallet
    if requesting_wallet:
        requesting_wallet_lower = requesting_wallet.lower()
        wallet_address_lower = wallet_address.lower()
        
        # Check if requesting wallet matches the wallet being looked up
        wallet_matches = (
            requesting_wallet_lower == wallet_address_lower or
            requesting_wallet_lower == wallet_address
        )
        
        # Check if requesting wallet belongs to the same client
        requesting_wallet_obj = db.query(Wallet).filter(
            (Wallet.address == requesting_wallet) | 
            (Wallet.address == requesting_wallet_lower)
        ).first()
        
        if requesting_wallet_obj:
            requesting_client = requesting_wallet_obj.client
            # Allow if same client OR admin
            is_admin = (
                requesting_client.account_identifier == "admin" or
                (requesting_client.role and requesting_client.role.lower() == "admin")
            )
            same_client = requesting_client.id == client.id
            
            if not (is_admin or same_client or wallet_matches):
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this wallet's data"
                )
        elif not wallet_matches:
            # Requesting wallet not found, but wallet being looked up doesn't match
            # Check if admin account exists and allow admin access
            admin_client = db.query(Client).filter(Client.account_identifier == "admin").first()
            if not admin_client:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this wallet's data"
                )
    
    wallets = [{"id": w.id, "chain": w.chain, "address": w.address} for w in client.wallets]
    connectors = [{"id": c.id, "name": c.name} for c in client.connectors]
    
    return {
        "client_id": client.id,
        "account_identifier": client.account_identifier,
        "name": client.name,
        "role": "admin" if client.account_identifier == "admin" else (client.role or "client"),
        "management_mode": getattr(client, 'management_mode', None) or 'unset',
        "wallets": wallets,
        "connectors": connectors
    }


@router.put("/{client_id}/wallet", response_model=ClientResponse)
def add_wallet(client_id: str, wallet: WalletInfo, db: Session = Depends(get_db)):
    """Add a wallet to an existing client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check for duplicate wallet (try both original case and lowercase for backward compatibility)
    existing = db.query(Wallet).filter(
        Wallet.client_id == client_id,
        ((Wallet.address == wallet.address) | (Wallet.address == wallet.address.lower()))
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Wallet already exists for this client")
    
    # Store address in original case
    new_wallet = Wallet(
        id=str(uuid.uuid4()),
        client_id=client_id,
        chain=wallet.chain,
        address=wallet.address,  # Store in original case
        created_at=datetime.utcnow()
    )
    db.add(new_wallet)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add wallet: {str(e)}")
    
    wallets = [{"id": w.id, "chain": w.chain, "address": w.address} for w in client.wallets]
    connectors = [{"id": c.id, "name": c.name} for c in client.connectors]
    
    return {
        "id": client.id,
        "name": client.name,
        "account_identifier": client.account_identifier,
        "wallets": wallets,
        "connectors": connectors,
        "created_at": client.created_at.isoformat()
    }


@router.put("/{client_id}/connector", response_model=ClientResponse)
def add_connector(client_id: str, connector: ConnectorInfo, db: Session = Depends(get_db)):
    """Add a connector to an existing client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    new_connector = Connector(
        id=str(uuid.uuid4()),
        client_id=client_id,
        name=connector.name,
        api_key=connector.api_key,
        api_secret=connector.api_secret,
        memo=connector.memo,
        created_at=datetime.utcnow()
    )
    db.add(new_connector)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add connector: {str(e)}")
    
    wallets = [{"id": w.id, "chain": w.chain, "address": w.address} for w in client.wallets]
    connectors = [{"id": c.id, "name": c.name} for c in client.connectors]
    
    return {
        "id": client.id,
        "name": client.name,
        "account_identifier": client.account_identifier,
        "wallets": wallets,
        "connectors": connectors,
        "created_at": client.created_at.isoformat()
    }


@router.delete("/{client_id}/connector/{connector_id}")
def delete_connector(client_id: str, connector_id: str, db: Session = Depends(get_db)):
    """Delete a specific connector from a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    connector = db.query(Connector).filter(
        Connector.id == connector_id,
        Connector.client_id == client_id
    ).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    try:
        db.delete(connector)
        db.commit()
        logger.info(f"Deleted connector {connector_id} from client {client_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete connector: {str(e)}")
    
    return {"status": "deleted", "connector_id": connector_id, "client_id": client_id}


@router.delete("/{client_id}")
def delete_client(client_id: str, db: Session = Depends(get_db)):
    """Delete a client and all associated data (cascade delete)."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        db.delete(client)  # Cascade delete will remove wallets, connectors, bots
        db.commit()
        logger.info(f"Deleted client: {client_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete client: {str(e)}")
    
    return {"status": "deleted", "client_id": client_id}
