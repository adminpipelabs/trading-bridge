"""
Coinstore API Connector
Direct API client for Coinstore exchange.
"""
import aiohttp
import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

BASE_URL = "https://api.coinstore.com"


class CoinstoreConnector:
    """Direct API connector for Coinstore exchange."""
    
    def __init__(self, api_key: str, api_secret: str, proxy_url: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy_url = proxy_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            # Proxy is passed per-request, not at session level
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for authenticated requests."""
        # Sort parameters
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        
        # Create signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, authenticated: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Coinstore API."""
        session = await self._get_session()
        url = f"{BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        
        # Add timestamp for authenticated requests
        if authenticated:
            params['timestamp'] = int(time.time() * 1000)
            params['apiKey'] = self.api_key
            signature = self._generate_signature(params)
            params['signature'] = signature
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        if authenticated:
            headers['X-API-KEY'] = self.api_key
        
        try:
            # Pass proxy per-request if configured
            request_kwargs = {'headers': headers}
            if self.proxy_url:
                request_kwargs['proxy'] = self.proxy_url
            
            if method.upper() == 'GET':
                async with session.get(url, params=params, **request_kwargs) as response:
                    response_text = await response.text()
                    logger.debug(f"Coinstore API GET {endpoint} response status={response.status}, body={response_text[:200]}")
                    
                    if response.status != 200:
                        error_text = response_text[:500]
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    try:
                        return await response.json()
                    except Exception as json_err:
                        logger.error(f"Failed to parse JSON response: {json_err}, response text: {response_text[:500]}")
                        raise Exception(f"Invalid JSON response: {response_text[:200]}")
            elif method.upper() == 'POST':
                async with session.post(url, json=params, **request_kwargs) as response:
                    response_text = await response.text()
                    logger.debug(f"Coinstore API POST {endpoint} response status={response.status}, body={response_text[:200]}")
                    
                    if response.status != 200:
                        error_text = response_text[:500]
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    try:
                        return await response.json()
                    except Exception as json_err:
                        logger.error(f"Failed to parse JSON response: {json_err}, response text: {response_text[:500]}")
                        raise Exception(f"Invalid JSON response: {response_text[:200]}")
            else:
                raise ValueError(f"Unsupported method: {method}")
        except Exception as e:
            logger.error(f"Coinstore API request failed for {endpoint}: {e}", exc_info=True)
            raise
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol."""
        # Format: BTCUSDT -> BTC/USDT
        if '/' not in symbol:
            # Assume USDT pair if no separator
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}/USDT"
        
        endpoint = "/api/v1/market/ticker"
        params = {"symbol": symbol.replace('/', '')}
        return await self._request('GET', endpoint, params, authenticated=False)
    
    async def get_balances(self) -> Dict[str, Any]:
        """Get account balances."""
        endpoint = "/api/v1/account/balance"
        return await self._request('GET', endpoint, authenticated=True)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get open orders."""
        endpoint = "/api/v1/order/openOrders"
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        return await self._request('GET', endpoint, params, authenticated=True)
    
    async def get_symbols(self) -> Dict[str, Any]:
        """Get all trading symbols."""
        endpoint = "/api/v1/market/symbols"
        return await self._request('GET', endpoint, authenticated=False)
    
    async def place_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        order_type: str,  # 'market' or 'limit'
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place an order."""
        endpoint = "/api/v1/order/place"
        params = {
            'symbol': symbol.replace('/', ''),
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(amount),
        }
        if order_type.lower() == 'limit' and price:
            params['price'] = str(price)
        
        return await self._request('POST', endpoint, params, authenticated=True)
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order."""
        endpoint = "/api/v1/order/cancel"
        params = {
            'orderId': order_id,
            'symbol': symbol.replace('/', ''),
        }
        return await self._request('POST', endpoint, params, authenticated=True)
