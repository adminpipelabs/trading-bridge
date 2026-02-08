"""
CEX Volume Bot
Generates trading volume on centralized exchanges using ccxt.

Similar to the Jupiter/Solana volume bot but for CEX.
"""

import os
import json
import random
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from decimal import Decimal, ROUND_DOWN

import ccxt.async_support as ccxt
from cryptography.fernet import Fernet

from app.cex_exchanges import get_exchange_config, EXCHANGE_CONFIGS

logger = logging.getLogger("cex_volume_bot")

# Log ccxt version at module load (use sync version just for version check)
try:
    import ccxt as ccxt_sync_version
    logger.info(f"ccxt version: {ccxt_sync_version.__version__}")
except Exception as e:
    logger.warning(f"Could not get ccxt version: {e}")

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")


class CEXVolumeBot:
    """
    Volume generation bot for centralized exchanges.
    
    Places alternating buy/sell market orders to generate organic-looking volume.
    """
    
    def __init__(
        self,
        bot_id: str,
        exchange_name: str,
        symbol: str,  # e.g., "LYNK/USDT"
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        memo: Optional[str] = None,  # BitMart uses memo/uid
        config: dict = None,
        proxy_url: Optional[str] = None,
    ):
        self.bot_id = bot_id
        # Ensure exchange_name is never None
        if not exchange_name or not isinstance(exchange_name, str):
            exchange_name = "bitmart"
        self.exchange_name = exchange_name.lower()
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.memo = memo  # BitMart memo/uid
        self.proxy_url = proxy_url or os.getenv("QUOTAGUARD_PROXY_URL")
        
        # Default config
        self.config = {
            "daily_volume_usd": 5000,
            "min_trade_usd": 10,
            "max_trade_usd": 25,
            "interval_min_seconds": 900,   # 15 min
            "interval_max_seconds": 2700,  # 45 min
            "max_position_imbalance": 0.2,  # Max 20% imbalance before forcing opposite side
            **( config or {})
        }
        
        self.exchange: Optional[ccxt.Exchange] = None
        self.running = False
        self.last_side = None  # 'buy' or 'sell'
        self.daily_volume = 0
        self.daily_reset_date = None
        self.position_imbalance = 0  # Positive = long, negative = short
        
    async def initialize(self) -> bool:
        """Initialize exchange connection."""
        # Log ccxt version (use sync version just for version check)
        try:
            import ccxt as ccxt_sync_version
            logger.info(f"🔍 ccxt version: {ccxt_sync_version.__version__}")
        except Exception as e:
            logger.warning(f"Could not get ccxt version: {e}")
        
        try:
            # Validate exchange_name is set and normalized
            if not self.exchange_name or not isinstance(self.exchange_name, str):
                logger.error(f"Invalid exchange_name: {self.exchange_name} (type: {type(self.exchange_name)})")
                return False
            
            # Ensure exchange_name is lowercase and stripped
            self.exchange_name = self.exchange_name.lower().strip()
            logger.info(f"Initializing exchange: {self.exchange_name} for bot {self.bot_id}")
            
            # Get exchange config
            exchange_config = get_exchange_config(self.exchange_name)
            if not exchange_config:
                logger.error(f"No config found for exchange: {self.exchange_name}")
                return False
            
            ccxt_id = exchange_config.get("ccxt_id")
            if not ccxt_id:
                logger.error(f"No ccxt_id in config for exchange: {self.exchange_name}")
                return False
            
            logger.info(f"Using ccxt exchange ID: {ccxt_id}")
            
            # Get exchange class from ccxt
            exchange_class = getattr(ccxt, ccxt_id, None)
            if exchange_class is None:
                logger.error(f"Exchange class not found in ccxt: {ccxt_id}. Available: {[x for x in dir(ccxt) if not x.startswith('_')]}")
                return False
            
            # Build exchange parameters
            exchange_params = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
                "rateLimit": exchange_config.get("rate_limit_ms", 100),
            }
            
            # Add passphrase if needed
            if self.passphrase and exchange_config.get("requires_passphrase"):
                exchange_params["password"] = self.passphrase
            
            # BitMart requires defaultType option (spot, margin, futures)
            # Without this, ccxt calls .lower() on None account type → crash
            if self.exchange_name == "bitmart":
                exchange_params["options"] = {
                    "defaultType": "spot"  # REQUIRED - prevents NoneType.lower() error
                }
                if self.memo:
                    # Ensure memo is a string and not empty
                    memo_str = str(self.memo).strip() if self.memo else None
                    if memo_str:
                        exchange_params["uid"] = memo_str
                        logger.info(f"BitMart UID set: {memo_str[:4]}...")
                    else:
                        logger.warning(f"⚠️  BitMart memo is empty or invalid: {self.memo}")
                else:
                    logger.debug(f"BitMart memo/UID not provided - using API keys only")
            
            # Add proxy if configured (for QuotaGuard static IP)
            if self.proxy_url:
                exchange_params["proxies"] = {
                    "http": self.proxy_url,
                    "https": self.proxy_url,
                }
                logger.info(f"Using proxy for {self.exchange_name}: {self.proxy_url.split('@')[0]}@...")
            
            # Create exchange instance
            logger.info(f"Creating {ccxt_id} exchange instance...")
            logger.debug(f"Exchange params keys: {list(exchange_params.keys())}")
            if "options" in exchange_params:
                logger.debug(f"Exchange options: {exchange_params['options']}")
            
            # Verify we're using async ccxt
            if not hasattr(exchange_class, '__call__'):
                logger.error(f"Exchange class {ccxt_id} is not callable")
                return False
            
            # Create exchange instance (from async_support, so it's async)
            self.exchange = exchange_class(exchange_params)
            
            # Verify exchange is async (has coroutine methods)
            if not hasattr(self.exchange, 'load_markets') or not asyncio.iscoroutinefunction(self.exchange.load_markets):
                logger.error(f"❌ Exchange {ccxt_id} is NOT async! load_markets is not a coroutine.")
                logger.error(f"This means sync ccxt was imported instead of async_support")
                return False
            
            logger.info(f"✅ Exchange instance created (async verified)")
            
            # Verify options were set correctly
            if self.exchange_name == "bitmart" and hasattr(self.exchange, 'options'):
                logger.info(f"✅ BitMart exchange created with options: {self.exchange.options}")
                if self.exchange.options.get('defaultType'):
                    logger.info(f"✅ defaultType set to: {self.exchange.options['defaultType']}")
                else:
                    logger.warning(f"⚠️  defaultType NOT set in exchange.options!")
            
            if self.exchange is None:
                logger.error(f"Failed to create exchange instance - exchange_class returned None")
                return False
            
            # Test connection by loading markets
            logger.info(f"Loading markets for {self.exchange_name}...")
            await self.exchange.load_markets()
            
            if not hasattr(self.exchange, 'markets') or not self.exchange.markets:
                logger.error(f"Failed to load markets for {self.exchange_name}")
                return False
            
            # Verify symbol exists
            if self.symbol not in self.exchange.markets:
                logger.error(f"Symbol {self.symbol} not found on {self.exchange_name}. Available symbols: {list(self.exchange.markets.keys())[:10]}...")
                return False
            
            # Verify exchange has required methods
            if not hasattr(self.exchange, 'fetch_balance'):
                logger.error(f"Exchange {self.exchange_name} doesn't have fetch_balance method")
                return False
            
            # Store market info for debugging
            market_info = self.exchange.markets.get(self.symbol)
            logger.info(f"Market info for {self.symbol}: {market_info}")
            
            logger.info(f"✅ CEX Volume Bot initialized successfully: {self.exchange_name} {self.symbol}")
            return True
            
        except AttributeError as e:
            logger.error(f"AttributeError initializing exchange {self.exchange_name}: {e}. Check if ccxt.{ccxt_id} exists.", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_name}: {e}", exc_info=True)
            return False
    
    async def close(self):
        """Close exchange connection."""
        if self.exchange:
            try:
                await self.exchange.close()
            except:
                pass
    
    async def get_balances(self) -> Tuple[float, float]:
        """
        Get base and quote balances.
        Returns: (base_balance, quote_balance)
        """
        try:
            # Validate exchange is initialized
            if self.exchange is None:
                logger.error(f"Exchange not initialized for bot {self.bot_id}. Call initialize() first.")
                return 0, 0
            
            # Validate exchange_name is set
            if not self.exchange_name or not isinstance(self.exchange_name, str):
                logger.error(f"Invalid exchange_name when fetching balance: {self.exchange_name} (type: {type(self.exchange_name)})")
                return 0, 0
            
            logger.debug(f"Fetching balance from {self.exchange_name} for {self.symbol}")
            
            # DEBUG: Check exchange object state before calling fetch_balance
            logger.debug(f"Exchange object type: {type(self.exchange)}")
            logger.debug(f"Exchange has fetch_balance: {hasattr(self.exchange, 'fetch_balance')}")
            if hasattr(self.exchange, 'apiKey'):
                logger.debug(f"Exchange apiKey present: {bool(self.exchange.apiKey)}")
            if hasattr(self.exchange, 'secret'):
                logger.debug(f"Exchange secret present: {bool(self.exchange.secret)}")
            if hasattr(self.exchange, 'uid'):
                logger.debug(f"Exchange uid: {self.exchange.uid}")
            if hasattr(self.exchange, 'options'):
                logger.debug(f"Exchange options: {self.exchange.options}")
            
            # Call fetch_balance with full error context
            # BitMart requires type parameter - pass it explicitly to prevent NoneType.lower() error
            try:
                if self.exchange_name == "bitmart":
                    # Explicitly pass type='spot' to prevent ccxt calling .lower() on None
                    balance = await self.exchange.fetch_balance({'type': 'spot'})
                else:
                    balance = await self.exchange.fetch_balance()
            except AttributeError as attr_err:
                # This error is from ccxt's error handler - BitMart API returned error with None message
                error_msg = str(attr_err)
                logger.error(f"❌ AttributeError in ccxt error handler: {error_msg}")
                logger.error(f"This means BitMart API returned an error, but error message was None")
                
                # Log ccxt version (use sync version just for version check)
                import ccxt as ccxt_sync_version
                logger.error(f"🔍 ccxt version: {ccxt_sync_version.__version__}")
                
                # Log actual BitMart response body
                if hasattr(self.exchange, 'last_http_response'):
                    logger.error(f"🔍 BitMart HTTP response: {self.exchange.last_http_response}")
                if hasattr(self.exchange, 'last_json_response'):
                    logger.error(f"🔍 BitMart JSON response: {self.exchange.last_json_response}")
                if hasattr(self.exchange, 'last_response_body'):
                    logger.error(f"🔍 BitMart response body: {self.exchange.last_response_body}")
                if hasattr(self.exchange, 'last_response_headers'):
                    logger.error(f"🔍 BitMart response headers: {self.exchange.last_response_headers}")
                if hasattr(self.exchange, 'last_response'):
                    logger.error(f"🔍 BitMart last_response: {self.exchange.last_response}")
                
                logger.error(f"Exchange config: apiKey present={bool(self.api_key)}, uid={self.memo}, options={getattr(self.exchange, 'options', {})}")
                raise
            except Exception as e:
                # Catch any other API errors
                error_msg = str(e)
                logger.error(f"❌ Error fetching balance from {self.exchange_name}: {error_msg}")
                
                # Log ccxt version (use sync version just for version check)
                try:
                    import ccxt as ccxt_sync_version
                    logger.error(f"🔍 ccxt version: {ccxt_sync_version.__version__}")
                except Exception:
                    pass
                
                # Log actual BitMart response body for any exception
                if self.exchange_name == "bitmart":
                    if hasattr(self.exchange, 'last_http_response'):
                        logger.error(f"🔍 BitMart HTTP response: {self.exchange.last_http_response}")
                    if hasattr(self.exchange, 'last_json_response'):
                        logger.error(f"🔍 BitMart JSON response: {self.exchange.last_json_response}")
                    if hasattr(self.exchange, 'last_response_body'):
                        logger.error(f"🔍 BitMart response body: {self.exchange.last_response_body}")
                
                logger.error(f"Full traceback:", exc_info=True)
                raise
            
            if not balance:
                logger.warning(f"Empty balance response from {self.exchange_name}")
                return 0, 0
            
            base, quote = self.symbol.split("/")
            base_free = float(balance.get(base, {}).get("free", 0) or 0)
            quote_free = float(balance.get(quote, {}).get("free", 0) or 0)
            
            logger.debug(f"Balance for {self.symbol}: {base}={base_free}, {quote}={quote_free}")
            return base_free, quote_free
            
        except AttributeError as e:
            # Check if error is about .lower() being called on None
            error_str = str(e)
            logger.error(f"❌ AttributeError fetching balance: {e}")
            logger.error(f"   Bot ID: {self.bot_id}")
            logger.error(f"   Exchange name: {self.exchange_name}")
            logger.error(f"   Exchange initialized: {self.exchange is not None}")
            logger.error(f"   Exchange type: {type(self.exchange) if self.exchange else None}")
            if self.exchange:
                logger.error(f"   Exchange apiKey: {getattr(self.exchange, 'apiKey', None)}")
                logger.error(f"   Exchange secret: {getattr(self.exchange, 'secret', None)}")
                logger.error(f"   Exchange uid: {getattr(self.exchange, 'uid', None)}")
            logger.error(f"   Full traceback:", exc_info=True)
            return 0, 0
        except Exception as e:
            error_str = str(e)
            logger.error(f"❌ Exception fetching balance: {e}")
            logger.error(f"   Bot ID: {self.bot_id}")
            logger.error(f"   Exchange name: {self.exchange_name}")
            logger.error(f"   Exchange initialized: {self.exchange is not None}")
            logger.error(f"   Full traceback:", exc_info=True)
            return 0, 0
    
    async def get_price(self) -> Optional[float]:
        """Get current market price."""
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            return float(ticker["last"])
        except Exception as e:
            logger.error(f"Failed to fetch price: {e}")
            return None
    
    def reset_daily_volume_if_needed(self):
        """Reset daily volume counter at midnight UTC."""
        today = datetime.now(timezone.utc).date()
        if self.daily_reset_date != today:
            self.daily_volume = 0
            self.daily_reset_date = today
            logger.info(f"Daily volume reset for bot {self.bot_id}")
    
    def should_continue(self) -> bool:
        """Check if bot should continue trading."""
        self.reset_daily_volume_if_needed()
        
        if self.daily_volume >= self.config["daily_volume_usd"]:
            logger.info(f"Daily target reached: ${self.daily_volume:.2f} / ${self.config['daily_volume_usd']}")
            return False
        
        return True
    
    def decide_side(self) -> str:
        """
        Decide whether to buy or sell.
        
        Alternates sides but respects position imbalance limits.
        Adds randomness to look organic.
        """
        # If too imbalanced, force the opposite side
        if self.position_imbalance > self.config["max_position_imbalance"]:
            return "sell"
        if self.position_imbalance < -self.config["max_position_imbalance"]:
            return "buy"
        
        # Otherwise, alternate with some randomness
        if self.last_side is None:
            return random.choice(["buy", "sell"])
        
        # 80% chance to alternate, 20% to repeat
        if random.random() < 0.8:
            return "sell" if self.last_side == "buy" else "buy"
        else:
            return self.last_side
    
    def calculate_trade_size(self, side: str, base_balance: float, quote_balance: float, price: float) -> Optional[float]:
        """
        Calculate trade size in base asset.
        
        Respects config limits and available balance.
        """
        # Random USD amount within range
        target_usd = random.uniform(
            self.config["min_trade_usd"],
            self.config["max_trade_usd"]
        )
        
        # Convert to base asset amount
        base_amount = target_usd / price
        
        # Check if we have enough balance
        if side == "sell":
            max_amount = base_balance * 0.95  # Keep 5% buffer
            if base_amount > max_amount:
                if max_amount * price < self.config["min_trade_usd"]:
                    logger.warning(f"Insufficient base balance for sell: {base_balance}")
                    return None
                base_amount = max_amount
        else:  # buy
            max_quote_spend = quote_balance * 0.95
            max_base_amount = max_quote_spend / price
            if base_amount > max_base_amount:
                if max_base_amount * price < self.config["min_trade_usd"]:
                    logger.warning(f"Insufficient quote balance for buy: {quote_balance}")
                    return None
                base_amount = max_base_amount
        
        # Check exchange minimums
        exchange_config = get_exchange_config(self.exchange_name)
        min_usd = exchange_config["min_order_value_usd"]
        if base_amount * price < min_usd:
            logger.warning(f"Trade size ${base_amount * price:.2f} below exchange min ${min_usd}")
            return None
        
        # Round to appropriate precision
        market = self.exchange.markets.get(self.symbol, {})
        precision = market.get("precision", {}).get("amount", 8)
        base_amount = float(Decimal(str(base_amount)).quantize(
            Decimal(10) ** -precision, rounding=ROUND_DOWN
        ))
        
        return base_amount
    
    async def execute_trade(self, side: str, amount: float) -> Optional[dict]:
        """Execute a trade order."""
        try:
            logger.info(f"Executing {side} {amount} {self.symbol}")
            
            # BitMart requires price for market buy orders, so use limit orders instead
            # Get current price for limit order
            current_price = await self.get_price()
            if not current_price:
                logger.error(f"Could not get current price for {self.symbol}")
                return None
            
            # BitMart requires type parameter for orders
            order_params = {}
            if self.exchange_name == "bitmart":
                order_params['type'] = 'spot'
            
            # Use limit orders for BitMart (market orders require price anyway)
            # For buy: use current price (will fill immediately if market price)
            # For sell: use current price (will fill immediately if market price)
            price = current_price
            
            # Slight price adjustment to ensure fill:
            # Buy: slightly above market (0.1% higher)
            # Sell: slightly below market (0.1% lower)
            if side == "buy":
                price = current_price * 1.001  # 0.1% above market
            else:
                price = current_price * 0.999  # 0.1% below market
            
            logger.info(f"Placing limit {side} order: {amount} {self.symbol} @ {price}")
            
            order = await self.exchange.create_limit_order(
                symbol=self.symbol,
                side=side,
                amount=amount,
                price=price,
                params=order_params,
            )
            
            # For limit orders, check if filled immediately or wait for fill
            order_id = order.get("id")
            logger.info(f"Limit order placed: {order_id}, status: {order.get('status', 'unknown')}")
            
            # Check if order was filled immediately
            if order.get("status") == "closed" or order.get("filled", 0) > 0:
                filled_amount = float(order.get("filled", amount))
                avg_price = float(order.get("average", 0) or order.get("price", price))
                cost = float(order.get("cost", filled_amount * avg_price))
                logger.info(f"Order filled immediately: {side} {filled_amount} @ {avg_price} = ${cost:.2f}")
            else:
                # Order is open, wait a moment and check status
                await asyncio.sleep(2)
                try:
                    order_status = await self.exchange.fetch_order(order_id, self.symbol)
                    filled_amount = float(order_status.get("filled", 0))
                    if filled_amount > 0:
                        avg_price = float(order_status.get("average", 0) or order_status.get("price", price))
                        cost = float(order_status.get("cost", filled_amount * avg_price))
                        logger.info(f"Order filled: {side} {filled_amount} @ {avg_price} = ${cost:.2f}")
                    else:
                        # Cancel unfilled order
                        await self.exchange.cancel_order(order_id, self.symbol)
                        logger.warning(f"Order {order_id} not filled, cancelled")
                        return None
                except Exception as check_err:
                    logger.warning(f"Could not check order status: {check_err}, assuming filled")
                    filled_amount = amount
                    avg_price = price
                    cost = filled_amount * avg_price
            
            filled_amount = float(order.get("filled", filled_amount))
            avg_price = float(order.get("average", 0) or order.get("price", avg_price))
            cost = float(order.get("cost", filled_amount * avg_price))
            
            return {
                "order_id": order.get("id"),
                "side": side,
                "amount": filled_amount,
                "price": avg_price,
                "cost_usd": cost,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"Invalid order: {e}")
            return None
        except Exception as e:
            logger.error(f"Trade execution failed: {e}", exc_info=True)
            return None
    
    async def run_single_cycle(self) -> Optional[dict]:
        """
        Run a single trade cycle.
        
        Returns trade info if successful, None if skipped or failed.
        """
        if not self.should_continue():
            return None
        
        # Get current state
        price = await self.get_price()
        if not price:
            return None
        
        # SKIP BALANCE CHECK - Try to place order directly
        # If balance check fails but credentials are valid, we can still try trading
        # The exchange will reject with InsufficientFunds if needed
        base_balance = None
        quote_balance = None
        try:
            base_balance, quote_balance = await self.get_balances()
            logger.info(f"Balance check successful: base={base_balance}, quote={quote_balance}")
        except Exception as balance_error:
            logger.warning(f"⚠️  Balance check failed: {balance_error}. Skipping balance check and trying direct trade.")
            logger.info(f"This is OK - we'll try placing order and exchange will reject if insufficient funds")
            # Set default balances to allow trade attempt
            base_balance = 0.0
            quote_balance = 0.0
        
        # Decide trade
        side = self.decide_side()
        
        # Calculate trade size (use defaults if balance check failed)
        if base_balance is None or quote_balance is None:
            # Use minimum trade size if we don't know balance
            min_usd = self.config["min_trade_usd"]
            amount = min_usd / price
            logger.info(f"Using minimum trade size (balance check skipped): ${min_usd} = {amount} {self.symbol.split('/')[0]}")
        else:
            amount = self.calculate_trade_size(side, base_balance, quote_balance, price)
            
            if not amount:
                # Try opposite side if this side has no balance
                side = "buy" if side == "sell" else "sell"
                amount = self.calculate_trade_size(side, base_balance, quote_balance, price)
                if not amount:
                    # If balance check worked but no valid size, use minimum
                    min_usd = self.config["min_trade_usd"]
                    amount = min_usd / price
                    logger.info(f"Using minimum trade size (no valid size calculated): ${min_usd} = {amount} {self.symbol.split('/')[0]}")
        
        # Execute trade
        result = await self.execute_trade(side, amount)
        
        if result:
            # Update tracking
            self.last_side = side
            self.daily_volume += result["cost_usd"]
            
            # Update position imbalance (normalized estimate)
            imbalance_delta = (result["cost_usd"] / self.config["daily_volume_usd"])
            if side == "buy":
                self.position_imbalance += imbalance_delta
            else:
                self.position_imbalance -= imbalance_delta
            
            result["daily_volume_total"] = self.daily_volume
            result["daily_target"] = self.config["daily_volume_usd"]
            result["progress_pct"] = (self.daily_volume / self.config["daily_volume_usd"]) * 100
        
        return result
    
    def get_next_interval(self) -> int:
        """Get random interval until next trade."""
        return random.randint(
            self.config["interval_min_seconds"],
            self.config["interval_max_seconds"]
        )


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def decrypt_credential(encrypted: str) -> str:
    """Decrypt an API key/secret."""
    if not ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not set")
    fernet = Fernet(ENCRYPTION_KEY.encode())
    return fernet.decrypt(encrypted.encode()).decode()


def encrypt_credential(plaintext: str) -> str:
    """Encrypt an API key/secret."""
    if not ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not set")
    fernet = Fernet(ENCRYPTION_KEY.encode())
    return fernet.encrypt(plaintext.encode()).decode()


async def create_bot_from_db(bot_record: dict, credentials: dict) -> Optional[CEXVolumeBot]:
    """
    Create a CEXVolumeBot instance from database records.
    
    Args:
        bot_record: Row from bots table
        credentials: Row from exchange_credentials table
    """
    try:
        api_key = decrypt_credential(credentials["api_key_encrypted"])
        api_secret = decrypt_credential(credentials["api_secret_encrypted"])
        passphrase = None
        if credentials.get("passphrase_encrypted"):
            passphrase = decrypt_credential(credentials["passphrase_encrypted"])
        
        # Build symbol from base/quote or pair
        if bot_record.get("base_asset") and bot_record.get("quote_asset"):
            symbol = f"{bot_record['base_asset']}/{bot_record['quote_asset']}"
        else:
            symbol = bot_record.get("pair", "").replace("_", "/").replace("-", "/")
        
        config = bot_record.get("config", {})
        if isinstance(config, str):
            config = json.loads(config)
        
        bot = CEXVolumeBot(
            bot_id=bot_record["id"],
            exchange_name=bot_record.get("exchange") or bot_record.get("connector", "bitmart"),
            symbol=symbol,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            config=config,
        )
        
        if await bot.initialize():
            return bot
        else:
            await bot.close()
            return None
            
    except Exception as e:
        logger.error(f"Failed to create bot from DB: {e}", exc_info=True)
        return None
