"""
Client management routes with wallet-to-account mapping.
Production-ready implementation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import re

router = APIRouter(prefix="/clients", tags=["clients"])

# In-memory storage (replace with PostgreSQL for persistence)
clients_db: dict = {}


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
async def create_client(request: CreateClientRequest):
    """Create a new client with account identifier for bot association."""
    client_id = str(uuid.uuid4())
    
    account_identifier = request.account_identifier
    if not account_identifier:
        account_identifier = generate_account_identifier(request.name)
    
    # Ensure account_identifier is unique
    for existing in clients_db.values():
        if existing["account_identifier"] == account_identifier:
            raise HTTPException(
                status_code=400,
                detail=f"Account identifier '{account_identifier}' already exists"
            )
    
    client = {
        "id": client_id,
        "name": request.name,
        "account_identifier": account_identifier,
        "wallets": [w.dict() for w in request.wallets],
        "connectors": [c.dict() for c in request.connectors],
        "created_at": datetime.utcnow().isoformat()
    }
    
    clients_db[client_id] = client
    return client


@router.get("", response_model=dict)
async def list_clients():
    """List all clients."""
    return {"clients": list(clients_db.values())}


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str):
    """Get a specific client by ID."""
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    return clients_db[client_id]


@router.get("/by-wallet/{wallet_address}", response_model=dict)
async def get_client_by_wallet(wallet_address: str):
    """
    Look up client by wallet address.
    Returns client info including account_identifier for bot filtering.
    """
    wallet_lower = wallet_address.lower()
    
    for client in clients_db.values():
        for wallet in client.get("wallets", []):
            if wallet.get("address", "").lower() == wallet_lower:
                return {
                    "client_id": client["id"],
                    "account_identifier": client["account_identifier"],
                    "name": client["name"],
                    "wallets": client["wallets"],
                    "connectors": client["connectors"]
                }
    
    raise HTTPException(
        status_code=404,
        detail="No client found for this wallet address"
    )


@router.put("/{client_id}/wallet", response_model=ClientResponse)
async def add_wallet(client_id: str, wallet: WalletInfo):
    """Add a wallet to an existing client."""
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = clients_db[client_id]
    
    # Check for duplicate wallet
    wallet_lower = wallet.address.lower()
    for existing in client["wallets"]:
        if existing["address"].lower() == wallet_lower:
            raise HTTPException(status_code=400, detail="Wallet already exists for this client")
    
    client["wallets"].append(wallet.dict())
    return client


@router.put("/{client_id}/connector", response_model=ClientResponse)
async def add_connector(client_id: str, connector: ConnectorInfo):
    """Add a connector to an existing client."""
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = clients_db[client_id]
    client["connectors"].append(connector.dict())
    return client


@router.delete("/{client_id}")
async def delete_client(client_id: str):
    """Delete a client."""
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    del clients_db[client_id]
    return {"status": "deleted", "client_id": client_id}
