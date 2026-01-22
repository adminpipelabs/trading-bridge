"""
Orders API endpoints
Place and manage orders
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.exchange import exchange_manager

router = APIRouter()


class PlaceOrderRequest(BaseModel):
    account_name: str
    connector_name: str
    trading_pair: str
    side: str  # "buy" or "sell" or "BUY" or "SELL"
    order_type: str = "limit"  # "market" or "limit"
    amount: float
    price: Optional[float] = None


class CancelOrderRequest(BaseModel):
    account_name: str
    order_id: str
    connector_name: Optional[str] = None
    symbol: Optional[str] = None


@router.get("/orders")
async def get_orders(
    account: str = Query(..., description="Account name"),
    pair: Optional[str] = Query(None, description="Trading pair filter")
):
    """Get open orders for an account"""
    acc = exchange_manager.get_account(account)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{account}' not found")
    
    try:
        orders = await acc.get_orders(trading_pair=pair)
        return {
            "account": account,
            "orders": orders,
            "count": len(orders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/place")
async def place_order(request: PlaceOrderRequest):
    """Place a new order"""
    acc = exchange_manager.get_account(request.account_name)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{request.account_name}' not found")
    
    try:
        result = await acc.place_order(
            connector_name=request.connector_name,
            trading_pair=request.trading_pair,
            side=request.side.lower(),
            order_type=request.order_type.lower(),
            amount=request.amount,
            price=request.price
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel")
async def cancel_order(request: CancelOrderRequest):
    """Cancel an existing order"""
    acc = exchange_manager.get_account(request.account_name)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account '{request.account_name}' not found")
    
    try:
        # Find the connector if not specified
        connector_name = request.connector_name
        if not connector_name and acc.connectors:
            connector_name = list(acc.connectors.keys())[0]
        
        if not connector_name:
            raise ValueError("No connector specified and account has no connectors")
        
        result = await acc.cancel_order(
            connector_name=connector_name,
            order_id=request.order_id,
            symbol=request.symbol
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Hummingbot-compatible endpoint
@router.post("/trading/orders")
async def trading_orders(data: dict):
    """Hummingbot-compatible order endpoint"""
    try:
        request = PlaceOrderRequest(
            account_name=data.get("account_name", "master_account"),
            connector_name=data.get("connector_name"),
            trading_pair=data.get("trading_pair"),
            side=data.get("trade_type", data.get("side", "buy")),
            order_type=data.get("order_type", "limit"),
            amount=float(data.get("amount", 0)),
            price=float(data.get("price")) if data.get("price") else None
        )
        return await place_order(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
