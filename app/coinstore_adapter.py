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
        """Fetch ticker data."""
        try:
            data = await self.connector.get_ticker(symbol)
            if data.get('code') == 0:
                ticker_data = data.get('data', {})
                return {
                    'symbol': symbol,
                    'last': float(ticker_data.get('lastPrice', 0)),
                    'bid': float(ticker_data.get('bidPrice', 0)),
                    'ask': float(ticker_data.get('askPrice', 0)),
                    'high': float(ticker_data.get('high24h', 0)),
                    'low': float(ticker_data.get('low24h', 0)),
                    'volume': float(ticker_data.get('volume24h', 0)),
                    'timestamp': int(time.time() * 1000),
                }
            else:
                raise Exception(f"API error: {data.get('msg')}")
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise
    
    async def fetch_balance(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Fetch account balance."""
        try:
            data = await self.connector.get_balances()
            
            # Log full response for debugging
            logger.debug(f"Coinstore balance API response: code={data.get('code')}, data type={type(data.get('data'))}")
            
            code = data.get('code')
            # Coinstore returns code as string "0" for success or int 0
            if code == 0 or code == "0":
                balances_list = data.get('data', [])
                
                # Coinstore returns balance as a list of account objects
                if not isinstance(balances_list, list):
                    logger.error(f"Coinstore balance data is not a list: {type(balances_list)} = {balances_list}")
                    raise Exception(f"Invalid balance response format: expected list, got {type(balances_list)}")
                
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
        """Create market buy order."""
        return await self.connector.place_order(symbol, 'buy', 'market', amount)
    
    async def create_market_sell_order(self, symbol: str, amount: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create market sell order."""
        return await self.connector.place_order(symbol, 'sell', 'market', amount)
    
    async def create_limit_buy_order(self, symbol: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create limit buy order."""
        return await self.connector.place_order(symbol, 'buy', 'limit', amount, price)
    
    async def create_limit_sell_order(self, symbol: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create limit sell order."""
        return await self.connector.place_order(symbol, 'sell', 'limit', amount, price)
    
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
