"""
BitMart ccxt-compatible Adapter
Provides ccxt-like interface for BitMart exchange, bypassing ccxt library.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from app.bitmart_connector import BitmartConnector

logger = logging.getLogger(__name__)


class BitmartExchange:
    """ccxt-compatible wrapper for BitMart API."""

    def __init__(self, config: Dict[str, Any]):
        self.name = "bitmart"
        self.id = "bitmart"
        self.apiKey = config.get('apiKey', '')
        self.secret = config.get('secret', '')
        self.uid = config.get('uid', '')  # memo
        self.proxy_url = config.get('aiohttp_proxy') or config.get('proxy')
        self.markets: Dict[str, Any] = {}
        self.connector = BitmartConnector(
            api_key=self.apiKey,
            api_secret=self.secret,
            memo=self.uid,
            proxy_url=self.proxy_url,
        )

    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        if self.markets and not reload:
            return self.markets
        # We don't strictly need full market data; populate on demand
        self.markets = {"SHARP/USDT": {"id": "SHARP_USDT", "symbol": "SHARP/USDT",
                                        "base": "SHARP", "quote": "USDT", "active": True}}
        return self.markets

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker — returns ccxt-style dict."""
        data = await self.connector.get_ticker(symbol)
        t = data.get("data", {})
        return {
            "symbol": symbol,
            "last": float(t.get("last", 0)),
            "bid": float(t.get("bid_px", 0)),
            "ask": float(t.get("ask_px", 0)),
            "high": float(t.get("high_24h", 0)),
            "low": float(t.get("low_24h", 0)),
            "close": float(t.get("last", 0)),
            "timestamp": int(t.get("ts", time.time() * 1000)),
        }

    async def fetch_balance(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        data = await self.connector.get_spot_wallet()
        result: Dict[str, Any] = {"free": {}, "used": {}, "total": {}}
        for w in data.get("data", {}).get("wallet", []):
            cur = w.get("id") or w.get("currency", "")
            avail = float(w.get("available", 0))
            frozen = float(w.get("frozen", 0))
            if avail > 0 or frozen > 0:
                result["free"][cur] = avail
                result["used"][cur] = frozen
                result["total"][cur] = avail + frozen
        return result

    # ── Market orders ────────────────────────────────────────────

    async def create_market_buy_order(self, symbol: str, amount: float,
                                      params: Optional[Dict] = None) -> Dict[str, Any]:
        """Market buy — amount is USDT to spend (notional)."""
        ticker = await self.fetch_ticker(symbol)
        price = ticker["last"]
        usdt = amount * price
        logger.info(f"🔵 MARKET BUY: {amount} tokens @ {price} = {usdt:.2f} USDT")
        data = await self.connector.place_order(symbol, "buy", "market", size=amount, notional=usdt)
        return self._parse_order(data, symbol, "buy", amount, price)

    async def create_market_sell_order(self, symbol: str, amount: float,
                                       params: Optional[Dict] = None) -> Dict[str, Any]:
        logger.info(f"🔵 MARKET SELL: {amount} tokens")
        ticker = await self.fetch_ticker(symbol)
        price = ticker["last"]
        data = await self.connector.place_order(symbol, "sell", "market", size=amount)
        return self._parse_order(data, symbol, "sell", amount, price)

    # ── Limit orders ─────────────────────────────────────────────

    async def create_limit_buy_order(self, symbol: str, amount: float, price: float,
                                     params: Optional[Dict] = None) -> Dict[str, Any]:
        data = await self.connector.place_order(symbol, "buy", "limit", size=amount, price=price)
        return self._parse_order(data, symbol, "buy", amount, price)

    async def create_limit_sell_order(self, symbol: str, amount: float, price: float,
                                      params: Optional[Dict] = None) -> Dict[str, Any]:
        data = await self.connector.place_order(symbol, "sell", "limit", size=amount, price=price)
        return self._parse_order(data, symbol, "sell", amount, price)

    async def create_limit_order(self, symbol: str, side: str, amount: float, price: float,
                                 params: Optional[Dict] = None) -> Dict[str, Any]:
        data = await self.connector.place_order(symbol, side, "limit", size=amount, price=price)
        return self._parse_order(data, symbol, side, amount, price)

    async def create_order(self, symbol: str, type: str, side: str, amount: float,
                           price: Optional[float] = None,
                           params: Optional[Dict] = None) -> Dict[str, Any]:
        """Generic create_order — ccxt interface."""
        if type == "market":
            if side == "buy":
                return await self.create_market_buy_order(symbol, amount, params)
            else:
                return await self.create_market_sell_order(symbol, amount, params)
        else:
            if price is None:
                raise ValueError("Price required for limit orders")
            return await self.create_limit_order(symbol, side, amount, price, params)

    # ── Cancel / query ───────────────────────────────────────────

    async def cancel_order(self, order_id: str, symbol: Optional[str] = None,
                           params: Optional[Dict] = None) -> Dict[str, Any]:
        if not symbol:
            raise ValueError("Symbol required for BitMart order cancellation")
        return await self.connector.cancel_order(symbol, order_id)

    async def fetch_order(self, order_id: str, symbol: Optional[str] = None,
                          params: Optional[Dict] = None) -> Dict[str, Any]:
        if not symbol:
            raise ValueError("Symbol required")
        data = await self.connector.get_order(symbol, order_id)
        detail = data.get("data", {})
        status_map = {"1": "open", "2": "open", "4": "open",
                      "5": "closed", "6": "closed", "8": "canceled"}
        return {
            "id": str(detail.get("orderId", order_id)),
            "symbol": symbol,
            "status": status_map.get(str(detail.get("orderStatus", "")), "unknown"),
            "filled": float(detail.get("filledSize", 0)),
            "remaining": float(detail.get("unfilledSize", 0)),
            "price": float(detail.get("price", 0)),
        }

    async def fetch_open_orders(self, symbol: Optional[str] = None, **kwargs) -> List[Dict]:
        if not symbol:
            return []
        data = await self.connector.get_open_orders(symbol)
        orders = []
        for o in data.get("data", {}).get("orders", []):
            orders.append({
                "id": str(o.get("orderId", "")),
                "symbol": symbol,
                "side": o.get("side", ""),
                "type": o.get("type", ""),
                "amount": float(o.get("size", 0)),
                "price": float(o.get("price", 0)),
                "status": "open",
            })
        return orders

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_order(data: Dict, symbol: str, side: str, amount: float,
                     price: float) -> Dict[str, Any]:
        """Parse BitMart order response into ccxt-style dict."""
        order_id = data.get("data", {}).get("order_id", "")
        return {
            "id": str(order_id),
            "orderId": str(order_id),
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "filled": amount,  # Assume filled for market orders
            "price": price,
            "average": price,
            "cost": amount * price,
            "status": "closed",
            "timestamp": int(time.time() * 1000),
        }

    async def close(self):
        await self.connector.close()


async def create_bitmart_exchange(
    api_key: str, api_secret: str, memo: str = "",
    proxy_url: Optional[str] = None
) -> BitmartExchange:
    """Create a BitMart exchange instance."""
    config = {
        "apiKey": api_key,
        "secret": api_secret,
        "uid": memo,
    }
    if proxy_url:
        config["aiohttp_proxy"] = proxy_url
    exchange = BitmartExchange(config)
    await exchange.load_markets()
    return exchange
