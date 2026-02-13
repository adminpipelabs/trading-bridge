"""
BitMart API Connector
Direct API client for BitMart exchange — bypasses ccxt to avoid library bugs.
"""
import aiohttp
import hmac
import hashlib
import time
import json
import logging
import socket
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api-cloud.bitmart.com"


class BitmartConnector:
    """Direct API connector for BitMart exchange."""

    def __init__(self, api_key: str, api_secret: str, memo: str = "", proxy_url: Optional[str] = None):
        self.api_key = api_key.strip() if api_key else ''
        self.api_secret = api_secret.strip() if api_secret else ''
        self.memo = memo.strip() if memo else ''
        if proxy_url and proxy_url.startswith('https://'):
            proxy_url = 'http://' + proxy_url[8:]
        self.proxy_url = proxy_url
        self.session: Optional[aiohttp.ClientSession] = None
        logger.debug(f"BitmartConnector initialized: key_len={len(self.api_key)}, memo={self.memo}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session. Forces IPv4 to match IP whitelist."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(family=socket.AF_INET)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _sign(self, timestamp: str, body: str = "") -> str:
        """Generate HMAC-SHA256 signature: timestamp + '#' + memo + '#' + body."""
        message = f"{timestamp}#{self.memo}#{body}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _auth_headers(self, body: str = "") -> Dict[str, str]:
        """Build authenticated request headers."""
        ts = str(int(time.time() * 1000))
        return {
            "X-BM-KEY": self.api_key,
            "X-BM-SIGN": self._sign(ts, body),
            "X-BM-TIMESTAMP": ts,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, body: Optional[Dict] = None,
                       authenticated: bool = False) -> Dict[str, Any]:
        """Make HTTP request to BitMart API."""
        session = await self._get_session()
        url = f"{BASE_URL}{path}"
        body_str = json.dumps(body) if body else ""
        if authenticated:
            logger.debug(f"🔑 Signing: key_len={len(self.api_key)}, memo='{self.memo}', body_len={len(body_str)}, body={body_str[:100]}")
        headers = self._auth_headers(body_str) if authenticated else {"Content-Type": "application/json"}

        kwargs: Dict[str, Any] = {"headers": headers}
        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url

        try:
            if method == "GET":
                async with session.get(url, **kwargs) as resp:
                    text = await resp.text()
                    data = json.loads(text)
                    self._check_error(data, path)
                    return data
            else:
                async with session.post(url, data=body_str, **kwargs) as resp:
                    text = await resp.text()
                    data = json.loads(text)
                    self._check_error(data, path)
                    return data
        except BitmartApiError:
            raise
        except Exception as e:
            logger.error(f"BitMart request {method} {path} failed: {e}")
            raise

    @staticmethod
    def _check_error(data: Dict, path: str):
        code = data.get("code")
        if code is not None and code != 1000:
            msg = data.get("message") or data.get("msg") or f"code {code}"
            raise BitmartApiError(code, msg, path)

    # ── Public endpoints ─────────────────────────────────────────

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker. symbol format: SHARP_USDT"""
        sym = symbol.replace("/", "_")
        return await self._request("GET", f"/spot/quotation/v3/ticker?symbol={sym}")

    # ── Account endpoints ────────────────────────────────────────

    async def get_wallet(self) -> Dict[str, Any]:
        return await self._request("GET", "/account/v1/wallet", authenticated=True)

    async def get_spot_wallet(self) -> Dict[str, Any]:
        return await self._request("GET", "/spot/v1/wallet", authenticated=True)

    # ── Trading endpoints ────────────────────────────────────────

    async def place_order(self, symbol: str, side: str, order_type: str,
                          size: float, price: Optional[float] = None,
                          notional: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a spot order.

        BitMart V2 submit_order params:
          symbol:   "SHARP_USDT"
          side:     "sell" / "buy"
          type:     "limit" / "market"
          size:     quantity of base token (for limit + market-sell)
          price:    required for limit orders
          notional: USDT amount for market-buy
        """
        sym = symbol.replace("/", "_")
        body: Dict[str, Any] = {
            "symbol": sym,
            "side": side.lower(),
            "type": order_type.lower(),
        }

        if order_type.lower() == "market":
            if side.lower() == "buy":
                # Market buy: spend X USDT
                body["notional"] = str(notional or size)
            else:
                # Market sell: sell X tokens
                body["size"] = str(int(size))
        else:
            # Limit order
            body["size"] = str(int(size))
            if price is not None:
                body["price"] = str(price)

        logger.info(f"🔵 PLACING BITMART ORDER: {body}")
        result = await self._request("POST", "/spot/v2/submit_order", body=body, authenticated=True)
        logger.info(f"🔵 BITMART ORDER RESPONSE: {result}")
        return result

    async def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        sym = symbol.replace("/", "_")
        body = {"symbol": sym, "order_id": order_id}
        return await self._request("POST", "/spot/v3/cancel_order", body=body, authenticated=True)

    async def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        sym = symbol.replace("/", "_")
        return await self._request("POST", "/spot/v2/order_detail",
                                   body={"orderId": order_id}, authenticated=True)

    async def get_open_orders(self, symbol: str) -> Dict[str, Any]:
        sym = symbol.replace("/", "_")
        return await self._request("POST", "/spot/v4/query/open-orders",
                                   body={"symbol": sym}, authenticated=True)


class BitmartApiError(Exception):
    def __init__(self, code, message, path=""):
        self.code = code
        self.message = message
        self.path = path
        super().__init__(f"BitMart API error on {path}: code={code}, msg={message}")
