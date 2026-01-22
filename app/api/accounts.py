"""
Accounts API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.exchange import exchange_manager

router = APIRouter()


class CreateAccountRequest(BaseModel):
    account_name: str


class CreateAccountResponse(BaseModel):
    success: bool
    account_name: str
    message: str


@router.post("/accounts/create", response_model=CreateAccountResponse)
async def create_account(request: CreateAccountRequest):
    """Create a new trading account"""
    try:
        account = exchange_manager.create_account(request.account_name)
        return CreateAccountResponse(
            success=True,
            account_name=account.name,
            message=f"Account '{account.name}' created successfully"
        )
    except ValueError as e:
        # Account already exists - return success anyway
        return CreateAccountResponse(
            success=True,
            account_name=request.account_name,
            message=f"Account '{request.account_name}' already exists"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts")
async def list_accounts():
    """List all trading accounts"""
    accounts = []
    for name, account in exchange_manager.accounts.items():
        accounts.append({
            "name": name,
            "connectors": list(account.connectors.keys()),
            "created_at": account.created_at.isoformat()
        })
    return {"accounts": accounts}


@router.get("/accounts/{account_name}")
async def get_account(account_name: str):
    """Get account details"""
    account = exchange_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    
    return {
        "name": account.name,
        "connectors": list(account.connectors.keys()),
        "created_at": account.created_at.isoformat()
    }
