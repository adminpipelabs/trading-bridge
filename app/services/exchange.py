"""
Exchange Manager Service
Manages exchange connections via ccxt
"""
import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

# Get proxy from environment variables (for QuotaGuard static IP)
PROXY_URL = os.getenv("QUOTAGUARD_PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


# Supported exchanges and their ccxt class names
# Note: Coinstore is handled specially (not in ccxt)
EXCHANGE_MAP = {
    "bitmart": ccxt.bitmart,
    "binance": ccxt.binance,
    "kucoin": ccxt.kucoin,
    "gate": ccxt.gate,
    "gateio": ccxt.gate,
    "mexc": ccxt.mexc,
    "bybit": ccxt.bybit,
    "okx": ccxt.okx,
    "htx": ccxt.htx,
    "huobi": ccxt.htx,
    "coinbase": ccxt.coinbase,
    "kraken": ccxt.kraken,
    # Coinstore handled via custom adapter in add_connector
}


class Account:
    """Represents a trading account with one or more exchange connections"""
    
    def __init__(self, name: str):
        self.name = name
        self.connectors: Dict[str, ccxt.Exchange] = {}
        self.created_at = datetime.utcnow()
    
    async def add_connector(
        self,
        connector_name: str,
        api_key: str,
        api_secret: str,
        password: Optional[str] = None,
        memo: Optional[str] = None
    ) -> Dict:
        """Add an exchange connector to this account"""
        
        connector_lower = connector_name.lower()
        
        # Handle Coinstore specially (custom adapter)
        if connector_lower == "coinstore":
            from app.coinstore_adapter import create_coinstore_exchange
            proxy_url = PROXY_URL
            exchange = await create_coinstore_exchange(
                api_key=api_key,
                api_secret=api_secret,
                proxy_url=proxy_url
            )
            self.connectors[connector_lower] = exchange
            logger.info(f"Added Coinstore connector to account {self.name}")
            return {
                "success": True,
                "connector": connector_name,
                "markets_loaded": len(exchange.markets)
            }
        
        if connector_lower not in EXCHANGE_MAP:
            raise ValueError(f"Unsupported exchange: {connector_name}. Supported: {list(EXCHANGE_MAP.keys())} + coinstore")
        
        exchange_class = EXCHANGE_MAP[connector_lower]
        
        # Build config
        config = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "timeout": 30000,
        }
        
        # BitMart requires defaultType option (spot, margin, futures)
        # Without this, ccxt calls .lower() on None account type → crash
        if connector_lower == "bitmart":
            config["options"] = {
                "defaultType": "spot"  # REQUIRED - prevents NoneType.lower() error
            }
        
        # Add proxy if configured (for QuotaGuard static IP)
        if PROXY_URL:
            config["proxies"] = {
                "http": PROXY_URL,
                "https": PROXY_URL,
            }
            logger.info(f"Using proxy for {connector_name}: {PROXY_URL.split('@')[0]}@...")
        
        # Some exchanges need password/passphrase
        if password:
            config["password"] = password
        
        # BitMart uses memo
        if memo:
            config["uid"] = memo  # BitMart memo goes in uid field
        
        # KuCoin uses passphrase
        if connector_lower == "kucoin" and password:
            config["password"] = password
        
        try:
            exchange = exchange_class(config)
            
            # Test connection by loading markets
            # Catch AttributeError for BitMart ccxt bug (calls .lower() on None message)
            try:
                await exchange.load_markets()
            except AttributeError as attr_err:
                if "'NoneType' object has no attribute 'lower'" in str(attr_err):
                    logger.warning(f"⚠️  BitMart ccxt error handler bug detected (None message). Exchange may still work for trading.")
                    # Continue anyway - exchange might still work
                else:
                    raise
            
            self.connectors[connector_lower] = exchange
            
            logger.info(f"Added {connector_name} connector to account {self.name}")
            
            return {
                "success": True,
                "connector": connector_name,
                "markets_loaded": len(exchange.markets) if hasattr(exchange, 'markets') and exchange.markets is not None else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to add connector {connector_name}: {e}")
            raise
    
    async def get_balances(self) -> Dict[str, Any]:
        """Get balances from all connectors"""
        all_balances = {}
        
        for connector_name, exchange in self.connectors.items():
            try:
                # BitMart requires type parameter - pass it explicitly
                if connector_name.lower() == 'bitmart':
                    balance = await exchange.fetch_balance({'type': 'spot'})
                elif connector_name.lower() == 'coinstore':
                    # Coinstore uses custom adapter
                    balance = await exchange.fetch_balance()
                else:
                    balance = await exchange.fetch_balance()
                
                # Filter to non-zero balances
                non_zero = {}
                for currency, amounts in balance.get("total", {}).items():
                    if amounts and float(amounts) > 0:
                        non_zero[currency] = {
                            "total": float(amounts),
                            "free": float(balance.get("free", {}).get(currency, 0)),
                            "used": float(balance.get("used", {}).get(currency, 0))
                        }
                
                all_balances[connector_name] = non_zero
                
            except Exception as e:
                logger.error(f"Failed to get balances from {connector_name}: {e}")
                all_balances[connector_name] = {"error": str(e)}
        
        return all_balances
    
    async def get_orders(self, trading_pair: Optional[str] = None) -> List[Dict]:
        """Get open orders from all connectors"""
        all_orders = []
        
        for connector_name, exchange in self.connectors.items():
            try:
                # Format pair for ccxt (SHARP-USDT -> SHARP/USDT)
                symbol = trading_pair.replace("-", "/") if trading_pair else None
                
                if symbol:
                    orders = await exchange.fetch_open_orders(symbol)
                else:
                    orders = await exchange.fetch_open_orders()
                
                for order in orders:
                    all_orders.append({
                        "connector": connector_name,
                        "id": order["id"],
                        "symbol": order["symbol"],
                        "side": order["side"],
                        "type": order["type"],
                        "price": order["price"],
                        "amount": order["amount"],
                        "filled": order["filled"],
                        "remaining": order["remaining"],
                        "status": order["status"],
                        "timestamp": order["timestamp"]
                    })
                    
            except Exception as e:
                logger.error(f"Failed to get orders from {connector_name}: {e}")
        
        return all_orders
    
    async def get_trades(self, trading_pair: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get trade history from all connectors"""
        all_trades = []
        
        for connector_name, exchange in self.connectors.items():
            try:
                symbol = trading_pair.replace("-", "/") if trading_pair else None
                
                if symbol:
                    trades = await exchange.fetch_my_trades(symbol, limit=limit)
                else:
                    # Some exchanges require symbol, so we might need to iterate
                    trades = []
                    try:
                        trades = await exchange.fetch_my_trades(limit=limit)
                    except:
                        pass
                
                for trade in trades:
                    all_trades.append({
                        "connector": connector_name,
                        "id": trade["id"],
                        "order_id": trade.get("order"),
                        "symbol": trade["symbol"],
                        "side": trade["side"],
                        "price": trade["price"],
                        "amount": trade["amount"],
                        "cost": trade["cost"],
                        "fee": trade.get("fee"),
                        "timestamp": trade["timestamp"]
                    })
                    
            except Exception as e:
                logger.error(f"Failed to get trades from {connector_name}: {e}")
        
        return all_trades
    
    async def place_order(
        self,
        connector_name: str,
        trading_pair: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict:
        """Place an order on specified exchange"""
        
        connector_lower = connector_name.lower()
        
        if connector_lower not in self.connectors:
            raise ValueError(f"Connector {connector_name} not found in account {self.name}")
        
        exchange = self.connectors[connector_lower]
        symbol = trading_pair.replace("-", "/")
        
        try:
            if order_type.lower() == "market":
                if side.lower() == "buy":
                    order = await exchange.create_market_buy_order(symbol, amount)
                else:
                    order = await exchange.create_market_sell_order(symbol, amount)
            else:
                # Limit order
                if price is None:
                    raise ValueError("Price required for limit orders")
                if side.lower() == "buy":
                    order = await exchange.create_limit_buy_order(symbol, amount, price)
                else:
                    order = await exchange.create_limit_sell_order(symbol, amount, price)
            
            logger.info(f"Order placed: {order['id']} on {connector_name}")
            
            return {
                "success": True,
                "order_id": order["id"],
                "symbol": order["symbol"],
                "side": order["side"],
                "type": order["type"],
                "price": order.get("price"),
                "amount": order["amount"],
                "status": order["status"]
            }
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    async def cancel_order(self, connector_name: str, order_id: str, symbol: Optional[str] = None) -> Dict:
        """Cancel an order"""
        
        connector_lower = connector_name.lower()
        
        if connector_lower not in self.connectors:
            raise ValueError(f"Connector {connector_name} not found in account {self.name}")
        
        exchange = self.connectors[connector_lower]
        
        try:
            # Some exchanges require symbol for cancellation
            if symbol:
                symbol = symbol.replace("-", "/")
                result = await exchange.cancel_order(order_id, symbol)
            else:
                result = await exchange.cancel_order(order_id)
            
            logger.info(f"Order cancelled: {order_id} on {connector_name}")
            
            return {
                "success": True,
                "order_id": order_id,
                "status": "cancelled"
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    async def close(self):
        """Close all exchange connections"""
        for name, exchange in self.connectors.items():
            try:
                await exchange.close()
            except:
                pass


class ExchangeManager:
    """Manages all trading accounts"""
    
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
    
    def create_account(self, account_name: str) -> Account:
        """Create a new trading account"""
        if account_name in self.accounts:
            raise ValueError(f"Account {account_name} already exists")
        
        account = Account(account_name)
        self.accounts[account_name] = account
        logger.info(f"Created account: {account_name}")
        return account
    
    def get_account(self, account_name: str) -> Optional[Account]:
        """Get an account by name"""
        return self.accounts.get(account_name)
    
    def get_or_create_account(self, account_name: str) -> Account:
        """Get existing account or create new one"""
        if account_name not in self.accounts:
            return self.create_account(account_name)
        return self.accounts[account_name]
    
    async def get_price(self, connector_name: str, trading_pair: str) -> Optional[float]:
        """Get current price for a trading pair from any available connection"""
        
        connector_lower = connector_name.lower()
        symbol = trading_pair.replace("-", "/")
        
        # First, try to find an account with this connector
        for account in self.accounts.values():
            if connector_lower in account.connectors:
                exchange = account.connectors[connector_lower]
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    return ticker.get("last") or ticker.get("close")
                except Exception as e:
                    logger.error(f"Failed to get price from {connector_name}: {e}")
        
        # If no authenticated connection, create a public one temporarily
        if connector_lower in EXCHANGE_MAP:
            try:
                public_config = {"enableRateLimit": True}
                # Add proxy if configured
                if PROXY_URL:
                    public_config["proxies"] = {
                        "http": PROXY_URL,
                        "https": PROXY_URL,
                    }
                exchange = EXCHANGE_MAP[connector_lower](public_config)
                ticker = await exchange.fetch_ticker(symbol)
                price = ticker.get("last") or ticker.get("close")
                await exchange.close()
                return price
            except Exception as e:
                logger.error(f"Failed to get public price from {connector_name}: {e}")
        
        return None
    
    async def close_all(self):
        """Close all accounts and connections"""
        for account in self.accounts.values():
            await account.close()


# Global instance
exchange_manager = ExchangeManager()
