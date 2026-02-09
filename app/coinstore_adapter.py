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
            if symbols_data.get('code') == 0:
                markets = {}
                for symbol_info in symbols_data.get('data', []):
                    symbol = symbol_info.get('symbol', '')
                    if symbol:
                        # Format: BTCUSDT -> BTC/USDT
                        if len(symbol) > 4 and symbol.endswith('USDT'):
                            base = symbol[:-4]
                            markets[f"{base}/USDT"] = {
                                'id': symbol,
                                'symbol': f"{base}/USDT",
                                'base': base,
                                'quote': 'USDT',
                                'active': True,
                            }
                self.markets = markets
                logger.info(f"Loaded {len(markets)} Coinstore markets")
                return markets
            else:
                logger.error(f"Failed to load markets: {symbols_data.get('msg')}")
                return {}
        except Exception as e:
            logger.error(f"Error loading Coinstore markets: {e}")
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
            logger.debug(f"Coinstore balance API response: code={data.get('code')}, data keys={list(data.get('data', {}).keys()) if isinstance(data.get('data'), dict) else 'not dict'}")
            
            if data.get('code') == 0:
                balances_data = data.get('data', {})
                
                # Handle case where data might not be a dict
                if not isinstance(balances_data, dict):
                    logger.error(f"Coinstore balance data is not a dict: {type(balances_data)} = {balances_data}")
                    raise Exception(f"Invalid balance response format: expected dict, got {type(balances_data)}")
                
                result = {
                    'free': {},
                    'used': {},
                    'total': {},
                }
                
                for currency, amounts in balances_data.items():
                    if not isinstance(amounts, dict):
                        logger.warning(f"Balance entry for {currency} is not a dict: {amounts}")
                        continue
                    
                    available = float(amounts.get('available', 0) or 0)
                    frozen = float(amounts.get('frozen', 0) or 0)
                    total = available + frozen
                    
                    if total > 0:
                        result['free'][currency] = available
                        result['used'][currency] = frozen
                        result['total'][currency] = total
                
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
