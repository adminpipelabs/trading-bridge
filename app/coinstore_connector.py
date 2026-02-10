"""
Coinstore API Connector
Direct API client for Coinstore exchange.
"""
import aiohttp
import hmac
import hashlib
import time
import math
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

BASE_URL = "https://api.coinstore.com/api"


class CoinstoreConnector:
    """Direct API connector for Coinstore exchange."""
    
    def __init__(self, api_key: str, api_secret: str, proxy_url: Optional[str] = None):
        # Strip whitespace (common issue with copy-paste)
        self.api_key = api_key.strip() if api_key else ''
        self.api_secret = api_secret.strip() if api_secret else ''
        # Normalize proxy URL: HTTP proxies should use http:// even for HTTPS targets
        if proxy_url and proxy_url.startswith('https://'):
            proxy_url = 'http://' + proxy_url[8:]  # Replace https:// with http://
            logger.debug("Normalized proxy URL: changed https:// to http://")
        self.proxy_url = proxy_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Log key lengths for debugging (don't log full keys)
        logger.debug(f"CoinstoreConnector initialized: api_key length={len(self.api_key)}, api_secret length={len(self.api_secret)}")
    
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
    
    def _generate_signature(self, expires: int, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature for authenticated requests.
        Coinstore uses a two-step signature:
        1. HMAC-SHA256(secret_key, expires_key) where expires_key = floor(expires/30000)
        2. HMAC-SHA256(key_from_step1, payload)
        
        Per Coinstore API docs:
        - GET with no params: payload = '' (empty string)
        - POST with empty params: payload = json.dumps({}) = '{}'
        """
        # Step 1: Calculate expires_key
        expires_key = str(math.floor(expires / 30000))
        
        # Step 2: First HMAC to get derived key
        # Use api_secret as key, expires_key as message
        secret_bytes = self.api_secret.encode('utf-8')
        expires_key_bytes = expires_key.encode('utf-8')
        key = hmac.new(
            secret_bytes,
            expires_key_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Step 3: Second HMAC to get signature
        # Use derived key as key, payload as message
        key_bytes = key.encode('utf-8')
        payload_bytes = payload.encode('utf-8')
        signature = hmac.new(
            key_bytes,
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Coinstore signature generated for endpoint")
        
        return signature
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, authenticated: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Coinstore API."""
        import json
        
        session = await self._get_session()
        url = f"{BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        
        # Prepare payload for signature
        # Per Coinstore docs: POST with empty params uses json.dumps({}) = '{}'
        if method.upper() == 'GET':
            # GET: payload is query string (empty string if no params)
            payload = urlencode(params) if params else ''
        else:
            # POST: payload is JSON body
            # Coinstore docs show: payload = json.dumps({}) for empty params
            payload = json.dumps(params, separators=(',', ':')) if params else json.dumps({})
        
        # Headers matching official Coinstore API docs exactly
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
        
        # Add authentication headers
        if authenticated:
            expires = int(time.time() * 1000)
            signature = self._generate_signature(expires, payload)
            
            headers['X-CS-APIKEY'] = self.api_key
            headers['X-CS-SIGN'] = signature
            headers['X-CS-EXPIRES'] = str(expires)
            headers['exch-language'] = 'en_US'
            
            logger.debug(f"Coinstore authenticated request: {method} {endpoint}")
        
        try:
            # Pass proxy per-request if configured
            # On Hetzner (static IP 5.161.64.209), proxy is NOT needed
            # On Railway, proxy was needed for IP 54.205.35.75
            request_kwargs = {'headers': headers}
            if self.proxy_url:
                logger.debug(f"Using proxy for Coinstore request: {self.proxy_url.split('@')[0] if '@' in self.proxy_url else self.proxy_url[:30]}...")
                request_kwargs['proxy'] = self.proxy_url
            else:
                logger.debug("No proxy configured - using direct connection (Hetzner static IP)")
            
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
                # CRITICAL: Send exact payload bytes that signature was calculated on
                # Don't let aiohttp re-serialize - use raw bytes to ensure exact match
                body_bytes = payload.encode('utf-8') if payload else b'{}'
                
                async with session.post(url, data=body_bytes, **request_kwargs) as response:
                    response_text = await response.text()
                    logger.debug(f"Coinstore API POST {endpoint} response status={response.status}")
                    
                    if response.status != 200:
                        error_text = response_text[:500]
                        # Try to parse error response
                        try:
                            error_json = await response.json()
                            error_code = error_json.get('code', response.status)
                            error_msg = error_json.get('msg') or error_json.get('message') or error_text
                            
                            # Detailed error logging for 1401
                            if error_code == 1401:
                                logger.error("=" * 80)
                                logger.error("❌ COINSTORE 1401 UNAUTHORIZED")
                                logger.error("=" * 80)
                                logger.error(f"   Error: {error_msg}")
                                logger.error(f"   API Key: {self.api_key[:10]}...{self.api_key[-5:]}")
                                logger.error(f"   Using proxy: {bool(self.proxy_url)}")
                                if self.proxy_url:
                                    logger.error(f"   Proxy URL: {self.proxy_url.split('@')[0] if '@' in self.proxy_url else self.proxy_url[:50]}")
                                logger.error("")
                                logger.error("   CHECK THESE:")
                                logger.error("   1. IP Whitelist: Is server IP whitelisted on Coinstore dashboard?")
                                logger.error("   2. API Secret: Does secret in database match Coinstore dashboard?")
                                logger.error("   3. API Permissions: Does API key have 'Read' and 'Spot Trading' enabled?")
                                logger.error("=" * 80)
                            else:
                                logger.error(f"❌ Coinstore API error (code {error_code}): {error_msg}")
                                logger.error(f"   Full error response: {error_json}")
                            
                            raise Exception(f"HTTP {response.status}: Coinstore API error (code {error_code}): {error_msg}")
                        except:
                            logger.error(f"❌ Coinstore API HTTP {response.status}: {error_text}")
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
        endpoint = "/spot/accountList"
        return await self._request('POST', endpoint, params={}, authenticated=True)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get open orders."""
        endpoint = "/api/v1/order/openOrders"
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        return await self._request('GET', endpoint, params, authenticated=True)
    
    async def get_symbols(self) -> Dict[str, Any]:
        """Get all trading symbols."""
        endpoint = "/v2/public/config/spot/symbols"
        return await self._request('POST', endpoint, params={}, authenticated=False)
    
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
