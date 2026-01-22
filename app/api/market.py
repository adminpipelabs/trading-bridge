"""
Market Data API endpoints
Get prices and market info
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List

from app.services.exchange import exchange_manager

router = APIRouter()


@router.get("/market/price")
async def get_price(
    connector: str = Query(..., description="Exchange name"),
    pair: str = Query(..., description="Trading pair (e.g., SHARP-USDT)")
):
    """Get current price for a trading pair"""
    try:
        price = await exchange_manager.get_price(connector, pair)
        if price is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not get price for {pair} on {connector}"
            )
        return {
            "connector": connector,
            "pair": pair,
            "price": price
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Hummingbot-compatible endpoint
@router.post("/market-data/prices")
async def get_prices(data: dict):
    """Get prices for multiple trading pairs (Hummingbot compatible)"""
    connector_name = data.get("connector_name")
    trading_pairs = data.get("trading_pairs", [])
    
    if not connector_name:
        raise HTTPException(status_code=400, detail="connector_name required")
    
    results = {}
    for pair in trading_pairs:
        try:
            price = await exchange_manager.get_price(connector_name, pair)
            results[pair] = {
                "price": price,
                "success": price is not None
            }
        except Exception as e:
            results[pair] = {
                "price": None,
                "success": False,
                "error": str(e)
            }
    
    return {
        "connector": connector_name,
        "prices": results
    }


@router.get("/market/orderbook")
async def get_orderbook(
    connector: str = Query(..., description="Exchange name"),
    pair: str = Query(..., description="Trading pair"),
    limit: int = Query(20, description="Depth limit")
):
    """Get order book for a trading pair"""
    from app.services.exchange import EXCHANGE_MAP
    
    connector_lower = connector.lower()
    symbol = pair.replace("-", "/")
    
    # Try to use existing connection first
    for account in exchange_manager.accounts.values():
        if connector_lower in account.connectors:
            try:
                exchange = account.connectors[connector_lower]
                orderbook = await exchange.fetch_order_book(symbol, limit)
                return {
                    "connector": connector,
                    "pair": pair,
                    "bids": orderbook.get("bids", [])[:limit],
                    "asks": orderbook.get("asks", [])[:limit],
                    "timestamp": orderbook.get("timestamp")
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    # Create temporary public connection
    if connector_lower in EXCHANGE_MAP:
        try:
            exchange = EXCHANGE_MAP[connector_lower]({"enableRateLimit": True})
            orderbook = await exchange.fetch_order_book(symbol, limit)
            await exchange.close()
            return {
                "connector": connector,
                "pair": pair,
                "bids": orderbook.get("bids", [])[:limit],
                "asks": orderbook.get("asks", [])[:limit],
                "timestamp": orderbook.get("timestamp")
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=400, detail=f"Unsupported exchange: {connector}")
