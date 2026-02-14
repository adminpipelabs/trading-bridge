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
import socket
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
        """Get or create aiohttp session. Forces IPv4 to match IP whitelist."""
        if self.session is None or self.session.closed:
            # Force IPv4 — exchanges whitelist our IPv4 (5.161.64.209),
            # but aiohttp defaults to IPv6 on dual-stack servers
            connector = aiohttp.TCPConnector(family=socket.AF_INET)
            self.session = aiohttp.ClientSession(connector=connector)
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
        
        Per Coinstore API docs (https://coinstore-openapi.github.io/en/#signature-authentication):
        - GET with no params: payload = '' (empty string)
        - POST with empty params: payload = json.dumps({}) = '{}'
        - Payload must be the exact string that will be sent in the request body
        
        Python example from docs:
        expires = int(time.time() * 1000)
        expires_key = str(math.floor(expires / 30000))
        expires_key = expires_key.encode("utf-8")
        key = hmac.new(secret_key, expires_key, hashlib.sha256).hexdigest()
        key = key.encode("utf-8")
        payload = json.dumps({})
        payload = payload.encode("utf-8")
        signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
        """
        # Step 1: Calculate expires_key (must be string representation of floor(expires/30000))
        expires_key = str(math.floor(expires / 30000))
        
        # Step 2: First HMAC to get derived key
        # Use api_secret as key, expires_key as message (both must be bytes)
        secret_bytes = self.api_secret.encode('utf-8')
        expires_key_bytes = expires_key.encode('utf-8')
        key_hex = hmac.new(
            secret_bytes,
            expires_key_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Step 3: Second HMAC to get signature
        # Use derived key (hex string) as bytes, payload (string) as bytes
        key_bytes = key_hex.encode('utf-8')
        payload_bytes = payload.encode('utf-8')
        signature = hmac.new(
            key_bytes,
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Coinstore signature generated: expires={expires}, expires_key={expires_key}, payload_length={len(payload)}")
        
        return signature
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, authenticated: bool = False, custom_payload: Optional[str] = None) -> Dict[str, Any]:
        """Make HTTP request to Coinstore API."""
        import json
        
        session = await self._get_session()
        url = f"{BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        
        # Prepare payload for signature
        # Per Coinstore docs: POST with empty params uses json.dumps({}) = '{}'
        if custom_payload:
            # Custom payload override (e.g., for semicolon-formatted endpoints)
            payload = custom_payload
        elif method.upper() == 'GET':
            # GET: payload is query string (empty string if no params)
            payload = urlencode(params) if params else ''
        else:
            # POST: payload is JSON body
            # Coinstore docs show: payload = json.dumps({}) for empty params
            # Use default json.dumps (with spaces) - Coinstore expects default JSON format
            payload = json.dumps(params) if params else json.dumps({})
        
        # Headers matching official Coinstore API docs exactly
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
        
        # Add authentication headers
        if authenticated:
            # Use timestamp from params if present (for order placement), otherwise generate new one
            # This ensures timestamp in payload matches expires in header (critical for signature)
            if params and 'timestamp' in params:
                expires = params['timestamp']
            else:
                expires = int(time.time() * 1000)
            
            # Log payload before signature generation (for debugging)
            logger.debug(f"Coinstore signature input: expires={expires}, payload='{payload}', payload_type={type(payload)}")
            
            signature = self._generate_signature(expires, payload)
            
            headers['X-CS-APIKEY'] = self.api_key
            headers['X-CS-SIGN'] = signature
            headers['X-CS-EXPIRES'] = str(expires)
            headers['exch-language'] = 'en_US'
            
            logger.debug(f"Coinstore authenticated request: {method} {endpoint}, signature={signature[:16]}...")
        
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
                    logger.info(f"🔵 Coinstore API GET {endpoint} response status={response.status}, body={response_text[:500]}")
                    
                    if response.status != 200:
                        error_text = response_text[:500]
                        logger.error(f"❌ Coinstore API GET {endpoint} failed: HTTP {response.status}: {error_text}")
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    try:
                        json_data = await response.json()
                        logger.debug(f"✅ Coinstore API GET {endpoint} parsed JSON: keys={list(json_data.keys()) if isinstance(json_data, dict) else 'not dict'}")
                        return json_data
                    except Exception as json_err:
                        logger.error(f"Failed to parse JSON response: {json_err}, response text: {response_text[:500]}")
                        raise Exception(f"Invalid JSON response: {response_text[:200]}")
            elif method.upper() == 'POST':
                # CRITICAL: Send exact payload bytes that signature was calculated on
                # Don't let aiohttp re-serialize - use raw bytes to ensure exact match
                # For empty params, ensure we send '{}' not empty string
                if not payload or payload == '':
                    body_bytes = b'{}'
                    payload = '{}'  # Ensure payload string matches what we send
                else:
                    body_bytes = payload.encode('utf-8')
                
                logger.debug(f"Coinstore POST payload bytes: {body_bytes[:200]}")
                
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
        """Get ticker data for a symbol.
        
        According to Coinstore docs (https://coinstore-openapi.github.io/en/):
        - GET /v1/ticker/price?symbol=SYMBOL - PUBLIC endpoint, NO authentication needed
        - Response format: {"code": 0, "data": [{"id": 1, "symbol": "btcusdt", "price": "400"}]}
        - "Public interface can be used to obtain basic information and ticker data. 
           Public interfaces can be called without authentication."
        """
        # Format: BTC/USDT -> BTCUSDT (remove separator, uppercase)
        symbol_formatted = symbol.replace('/', '').upper()
        
        # Use standard query parameter format: /v1/ticker/price?symbol=SHARPUSDT
        endpoint = "/v1/ticker/price"
        params = {"symbol": symbol_formatted}
        
        # Ticker is a PUBLIC endpoint - NO authentication headers!
        return await self._request('GET', endpoint, params, authenticated=False)
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get orderbook depth. Public endpoint, no auth."""
        symbol_formatted = symbol.replace('/', '').upper()
        endpoint = f"/v1/market/depth/{symbol_formatted}"
        params = {"depth": limit}
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
        price: Optional[float] = None,
        is_usdt_amount: bool = False  # True if amount is in USDT (for MARKET BUY), False if in base currency
    ) -> Dict[str, Any]:
        """
        Place an order on Coinstore.
        
        Per Coinstore API docs:
        - Endpoint: /trade/order/place
        - For MARKET orders:
          * BUY: use ordAmt (spend X USDT)
          * SELL: use ordQty (sell X tokens)
        - Must use ordType: "MARKET" (not "LIMIT")
        - timestamp is REQUIRED in payload (per docs: https://coinstore-openapi.github.io/en/#order-related)
        """
        endpoint = "/trade/order/place"
        
        # Format symbol (SHARP/USDT -> SHARPUSDT)
        symbol_formatted = symbol.replace('/', '')
        
        # Generate timestamp ONCE - will be used for both payload and expires header
        # This ensures they match exactly (critical for signature validation)
        timestamp_ms = int(time.time() * 1000)
        
        # Build payload per Coinstore docs
        # Note: timestamp is REQUIRED per API docs parameter table
        params = {
            'symbol': symbol_formatted,
            'side': side.upper(),  # 'BUY' or 'SELL'
            'ordType': order_type.upper(),  # 'MARKET' or 'LIMIT'
            'timestamp': timestamp_ms,  # Milliseconds timestamp (REQUIRED per docs)
        }
        
        # For MARKET orders: BUY uses ordAmt (USDT), SELL uses ordQty (tokens)
        if order_type.lower() == 'market':
            if side.lower() == 'buy':
                # Market BUY: spend X USDT (ordAmt)
                # amount is already in USDT if is_usdt_amount=True, otherwise convert
                if is_usdt_amount:
                    params['ordAmt'] = str(amount)
                else:
                    # If amount is in base currency, we need price to convert
                    # This shouldn't happen if called from adapter correctly
                    logger.warning(f"MARKET BUY received base amount without USDT conversion - using as-is")
                    params['ordAmt'] = str(amount)
            else:
                # Market SELL: sell X tokens (ordQty)
                # amount is in base currency (tokens)
                # Round to integer to avoid precision errors (code 3104)
                params['ordQty'] = str(int(amount))
        else:
            # LIMIT orders: use quantity and price
            params['ordQty'] = str(int(amount))
            if price:
                params['price'] = str(price)
        
        # Log payload before sending
        logger.info(f"🔵 PLACING COINSTORE ORDER: endpoint={endpoint}, payload={params}")
        
        # Log the exact JSON string that will be used for signature
        import json
        payload_json = json.dumps(params)  # Use default JSON format (with spaces) - matches Coinstore expectation
        logger.info(f"🔵 ORDER PAYLOAD JSON (for signature): {payload_json}")
        
        response = await self._request('POST', endpoint, params, authenticated=True)
        
        # Log response
        logger.info(f"🔵 COINSTORE ORDER RESPONSE: {response}")
        
        # Check for exchange-level errors (Coinstore returns HTTP 200 with code!=0 on failure)
        response_code = response.get("code")
        if response_code is not None and response_code != 0 and response_code != "0":
            error_msg = response.get("message") or response.get("msg") or f"code {response_code}"
            raise Exception(f"Coinstore order rejected: code={response_code}, msg={error_msg}")
        
        return response
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order."""
        endpoint = "/api/v1/order/cancel"
        params = {
            'orderId': order_id,
            'symbol': symbol.replace('/', ''),
        }
        return await self._request('POST', endpoint, params, authenticated=True)
