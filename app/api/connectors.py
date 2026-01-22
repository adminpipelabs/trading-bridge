"""
Connectors API endpoints
Add exchange connections to accounts
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.exchange import exchange_manager

router = APIRouter()


class AddConnectorRequest(BaseModel):
    account_name: str
    connector_name: str
    api_key: str
    api_secret: str
    password: Optional[str] = None  # For exchanges that need passphrase
    memo: Optional[str] = None      # For BitMart


class AddConnectorResponse(BaseModel):
    success: bool
    connector: str
    message: str
    markets_loaded: Optional[int] = None


@router.post("/connectors/add", response_model=AddConnectorResponse)
async def add_connector(request: AddConnectorRequest):
    """Add an exchange connector to an account"""
    try:
        # Get or create account
        account = exchange_manager.get_or_create_account(request.account_name)
        
        # Add connector
        result = await account.add_connector(
            connector_name=request.connector_name,
            api_key=request.api_key,
            api_secret=request.api_secret,
            password=request.password,
            memo=request.memo
        )
        
        return AddConnectorResponse(
            success=True,
            connector=request.connector_name,
            message=f"Connector '{request.connector_name}' added to account '{request.account_name}'",
            markets_loaded=result.get("markets_loaded")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add connector: {str(e)}")


@router.get("/connectors/supported")
async def list_supported_connectors():
    """List all supported exchanges"""
    from app.services.exchange import EXCHANGE_MAP
    return {
        "supported_exchanges": list(EXCHANGE_MAP.keys())
    }
