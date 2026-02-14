"""
Coinstore ccxt-compatible Adapter
Provides ccxt-like interface for Coinstore exchange.
"""
import logging
import time
from typing import Dict, Any, Optional
from app.coinstore_connector import CoinstoreConnector

logger = logging.getLogger(__name__)


class CoinstoreExchange:
    """ccxt-compatible wrapper for Coinstore API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = "coinstore"
        self.id = "coinstore"
        self.apiKey = config.get('apiKey', '')
        self.secret = config.get('secret', '')
        self.proxy_url = config.get('aiohttp_proxy') or config.get('proxy') or config.get('proxies', {}).get('https')
        self.markets: Dict[str, Any] = {}
        self.connector = CoinstoreConnector(
            api_key=self.apiKey,
            api_secret=self.secret,
            proxy_url=self.proxy_url
        )
    
    async def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """Load trading markets."""
        if self.markets and not reload:
            return self.markets
        
        try:
            symbols_data = await self.connector.get_symbols()
            code = symbols_data.get('code')
            # Coinstore returns code as string "0" for success or int 0
            if code == 0 or code == "0":
                markets = {}
                for symbol_info in symbols_data.get('data', []):
                    symbol_code = symbol_info.get('symbolCode', '')
                    if symbol_code:
                        # Format: BTCUSDT -> BTC/USDT
                        if len(symbol_code) > 4 and symbol_code.endswith('USDT'):
                            base = symbol_code[:-4]
                            markets[f"{base}/USDT"] = {
                                'id': symbol_code,
                                'symbol': f"{base}/USDT",
                                'base': base,
                                'quote': 'USDT',
                                'active': symbol_info.get('openTrade', True),
                            }
                self.markets = markets
                logger.info(f"Loaded {len(markets)} Coinstore markets")
                return markets
            else:
                error_msg = symbols_data.get('message') or symbols_data.get('msg') or str(symbols_data)
                logger.error(f"Failed to load markets: {error_msg}")
                return {}
        except Exception as e:
            logger.error(f"Error loading Coinstore markets: {e}", exc_info=True)
            return {}
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker data.
        
        Coinstore docs: GET /v1/ticker/price?symbol=SYMBOL
        Returns: {"code": 0, "data": [{"id": 1, "symbol": "btcusdt", "price": "400"}, ...]}
        Note: API returns ALL tickers, we need to find our symbol in the list
        """
        try:
            data = await self.connector.get_ticker(symbol)
            logger.debug(f"Ticker API response for {symbol}: code={data.get('code')}, keys={list(data.keys())}")
            
            # Coinstore returns code as 0 (int) or "0" (string) for success
            code = data.get('code')
            if code == 0 or code == "0":
                # /v1/ticker/price returns data as array of ALL tickers
                ticker_list = data.get('data', [])
                if not isinstance(ticker_list, list):
                    raise Exception(f"API error: Expected list in data field, got {type(ticker_list)}")
                
                # Find our symbol in the list (case-insensitive)
                symbol_formatted = symbol.replace('/', '').upper()
                ticker_item = None
                for item in ticker_list:
                    if isinstance(item, dict):
                        item_symbol = item.get('symbol', '').upper()
                        if item_symbol == symbol_formatted:
                            ticker_item = item
                            break
                
                if not ticker_item:
                    logger.error(f"Symbol {symbol_formatted} not found in ticker response. Available symbols: {[t.get('symbol') for t in ticker_list[:10] if isinstance(t, dict)]}")
                    raise Exception(f"API error: Symbol {symbol} not found in ticker data")
                
                price = ticker_item.get('price')
                if not price or price == "0":
                    logger.error(f"Ticker price missing or zero for {symbol}: {ticker_item}")
                    raise Exception(f"API error: No valid price for {symbol}")
                
                # For /v1/ticker/price, we only get price, so use it as last
                return {
                    'symbol': symbol,
                    'last': float(price),
                    'close': float(price),  # Use price as close
                    'bid': float(price),  # Approximate - /v1/ticker/price doesn't provide bid/ask
                    'ask': float(price),  # Approximate
                    'high': 0.0,  # Not available from /v1/ticker/price
                    'low': 0.0,
                    'volume': 0.0,
                    'timestamp': int(time.time() * 1000),
                }
            else:
                error_msg = data.get('msg') or data.get('message') or f"Code {code}"
                logger.error(f"Ticker API error for {symbol}: code={code}, msg={error_msg}, full response: {data}")
                raise Exception(f"API error: {error_msg}")
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}", exc_info=True)
            raise
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Fetch orderbook depth — returns ccxt-style dict."""
        try:
            data = await self.connector.get_orderbook(symbol, limit)
            code = data.get('code')
            if code == 0 or code == "0":
                raw = data.get('data', {})
                # Coinstore depth: {"b": [["price","amount"], ...], "a": [...]}
                bids = [[float(b[0]), float(b[1])] for b in raw.get('b', [])]
                asks = [[float(a[0]), float(a[1])] for a in raw.get('a', [])]
                return {"bids": bids, "asks": asks, "symbol": symbol}
            else:
                raise Exception(f"Orderbook API error: code={code}")
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            raise

    async def fetch_balance(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Fetch account balance."""
        try:
            data = await self.connector.get_balances()
            
            # Log full response for debugging
            logger.info(f"💰 Coinstore balance API response: code={data.get('code')}, data type={type(data.get('data'))}")
            logger.info(f"   Full response keys: {list(data.keys())}")
            
            code = data.get('code')
            # Coinstore returns code as string "0" for success or int 0
            if code == 0 or code == "0":
                balances_list = data.get('data', [])
                logger.info(f"   ✅ Success! Found {len(balances_list)} account entries")
                
                # Coinstore returns balance as a list of account objects
                if not isinstance(balances_list, list):
                    logger.error(f"❌ Coinstore balance data is not a list: {type(balances_list)} = {balances_list}")
                    raise Exception(f"Invalid balance response format: expected list, got {type(balances_list)}")
                
                # Log first few entries for debugging
                if balances_list:
                    logger.info(f"   Sample entries (first 3):")
                    for i, entry in enumerate(balances_list[:3]):
                        logger.info(f"      [{i}] currency={entry.get('currency')}, balance={entry.get('balance')}, type={entry.get('type')}, typeName={entry.get('typeName')}")
                
                result = {
                    'free': {},
                    'used': {},
                    'total': {},
                }
                
                # Group balances by currency (can have multiple entries: AVAILABLE and FROZEN)
                for account in balances_list:
                    currency = account.get('currency', '').upper()
                    balance = float(account.get('balance', 0) or 0)
                    account_type = account.get('type', 0)
                    type_name = account.get('typeName', '')
                    
                    # type 1 = AVAILABLE, type 4 = FROZEN
                    if currency:
                        if currency not in result['free']:
                            result['free'][currency] = 0.0
                            result['used'][currency] = 0.0
                            result['total'][currency] = 0.0
                        
                        if account_type == 1 or type_name == 'AVAILABLE':
                            result['free'][currency] += balance
                        elif account_type == 4 or type_name == 'FROZEN':
                            result['used'][currency] += balance
                        
                        result['total'][currency] = result['free'][currency] + result['used'][currency]
                
                # Remove zero balances
                for currency in list(result['free'].keys()):
                    if result['total'][currency] == 0:
                        del result['free'][currency]
                        del result['used'][currency]
                        del result['total'][currency]
                
                return result
            else:
                # Better error message handling
                error_msg = data.get('msg') or data.get('message') or str(data)
                error_code = data.get('code', 'unknown')
                logger.error(f"Coinstore API error: code={error_code}, msg={error_msg}, full response={data}")
                logger.error(f"⚠️  Coinstore authentication failed. Check:")
                logger.error(f"   1. API key is correct")
                logger.error(f"   2. API secret is correct")
                logger.error(f"   3. API key has 'spot trading' permissions enabled")
                logger.error(f"   4. IP whitelist (if enabled) includes Railway IPs")
                raise Exception(f"Coinstore API error (code {error_code}): {error_msg}")
        except Exception as e:
            logger.error(f"Error fetching balance from Coinstore: {e}", exc_info=True)
            raise
    
    async def fetch_open_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params: Optional[Dict] = None) -> list:
        """Fetch open orders."""
        try:
            data = await self.connector.get_open_orders(symbol)
            if data.get('code') == 0:
                orders = []
                for order_data in data.get('data', []):
                    symbol_raw = order_data.get('symbol', '')
                    # Format: BTCUSDT -> BTC/USDT
                    if len(symbol_raw) > 4 and symbol_raw.endswith('USDT'):
                        symbol_formatted = f"{symbol_raw[:-4]}/USDT"
                    else:
                        symbol_formatted = symbol_raw
                    
                    orders.append({
                        'id': str(order_data.get('orderId', '')),
                        'symbol': symbol_formatted,
                        'side': order_data.get('side', '').lower(),
                        'type': order_data.get('type', '').lower(),
                        'amount': float(order_data.get('quantity', 0)),
                        'price': float(order_data.get('price', 0)),
                        'filled': float(order_data.get('filledQuantity', 0)),
                        'remaining': float(order_data.get('quantity', 0)) - float(order_data.get('filledQuantity', 0)),
                        'status': 'open',
                        'timestamp': order_data.get('createTime', 0),
                    })
                return orders
            else:
                raise Exception(f"API error: {data.get('msg')}")
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    async def create_market_buy_order(self, symbol: str, amount: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create market buy order.
        
        For Coinstore MARKET BUY:
        - amount is in base currency (tokens)
        - Need to convert to USDT amount (ordAmt) using current price
        """
        # Get current price to calculate USDT amount
        ticker = await self.fetch_ticker(symbol)
        current_price = ticker.get('last') or ticker.get('close')
        if not current_price:
            raise ValueError(f"Could not get current price for {symbol}")
        
        # Convert base amount to USDT amount for MARKET BUY
        usdt_amount = amount * current_price
        
        logger.info(f"🔵 MARKET BUY: {amount} tokens @ {current_price} = {usdt_amount} USDT")
        
        # Pass USDT amount (Coinstore expects ordAmt for MARKET BUY)
        data = await self.connector.place_order(symbol, 'buy', 'market', usdt_amount, is_usdt_amount=True)
        return self._parse_response(data, symbol, 'buy', amount, current_price)
    
    async def create_market_sell_order(self, symbol: str, amount: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create market sell order.
        
        For Coinstore MARKET SELL:
        - amount is in base currency (tokens)
        - Use ordQty directly (sell X tokens)
        """
        ticker = await self.fetch_ticker(symbol)
        current_price = ticker.get('last') or ticker.get('close') or 0
        logger.info(f"🔵 MARKET SELL: {amount} tokens @ ~{current_price}")
        data = await self.connector.place_order(symbol, 'sell', 'market', amount, is_usdt_amount=False)
        return self._parse_response(data, symbol, 'sell', amount, current_price)
    
    async def create_limit_buy_order(self, symbol: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create limit buy order."""
        data = await self.connector.place_order(symbol, 'buy', 'limit', amount, price)
        return self._parse_response(data, symbol, 'buy', amount, price)
    
    async def create_limit_sell_order(self, symbol: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create limit sell order."""
        data = await self.connector.place_order(symbol, 'sell', 'limit', amount, price)
        return self._parse_response(data, symbol, 'sell', amount, price)
    
    @staticmethod
    def _parse_response(data: Dict, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """Parse Coinstore response into ccxt-style dict."""
        order_id = data.get("data", {}).get("ordId", "") if isinstance(data.get("data"), dict) else ""
        return {
            "id": str(order_id),
            "orderId": str(order_id),
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "filled": amount,
            "price": price,
            "average": price,
            "cost": amount * price,
            "status": "closed",
            "timestamp": int(time.time() * 1000),
        }
    
    async def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create limit order (generic ccxt interface)."""
        data = await self.connector.place_order(symbol, side, 'limit', amount, price)
        return self._parse_response(data, symbol, side, amount, price)
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Cancel an order."""
        if not symbol:
            raise ValueError("Symbol required for Coinstore order cancellation")
        return await self.connector.cancel_order(order_id, symbol)
    
    async def close(self):
        """Close the connection."""
        await self.connector.close()


async def create_coinstore_exchange(
    api_key: str,
    api_secret: str,
    proxy_url: Optional[str] = None
) -> CoinstoreExchange:
    """Create a Coinstore exchange instance."""
    config = {
        'apiKey': api_key,
        'secret': api_secret,
    }
    if proxy_url:
        config['aiohttp_proxy'] = proxy_url
    
    exchange = CoinstoreExchange(config)
    await exchange.load_markets()
    return exchange
