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
        config: dict = None,
        proxy_url: Optional[str] = None,
    ):
        self.bot_id = bot_id
        self.exchange_name = exchange_name.lower()
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
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
        try:
            exchange_config = get_exchange_config(self.exchange_name)
            exchange_class = getattr(ccxt, exchange_config["ccxt_id"])
            
            exchange_params = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
                "rateLimit": exchange_config["rate_limit_ms"],
            }
            
            if self.passphrase and exchange_config.get("requires_passphrase"):
                exchange_params["password"] = self.passphrase
            
            # Add proxy if configured (for QuotaGuard static IP)
            if self.proxy_url:
                exchange_params["proxies"] = {
                    "http": self.proxy_url,
                    "https": self.proxy_url,
                }
                logger.info(f"Using proxy for {self.exchange_name}: {self.proxy_url.split('@')[0]}@...")
            
            self.exchange = exchange_class(exchange_params)
            
            # Test connection
            await self.exchange.load_markets()
            
            if self.symbol not in self.exchange.markets:
                logger.error(f"Symbol {self.symbol} not found on {self.exchange_name}")
                return False
            
            logger.info(f"CEX Volume Bot initialized: {self.exchange_name} {self.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}", exc_info=True)
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
            balance = await self.exchange.fetch_balance()
            
            base, quote = self.symbol.split("/")
            base_free = float(balance.get(base, {}).get("free", 0))
            quote_free = float(balance.get(quote, {}).get("free", 0))
            
            return base_free, quote_free
            
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
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
        """Execute a market order."""
        try:
            logger.info(f"Executing {side} {amount} {self.symbol}")
            
            order = await self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=amount,
            )
            
            # Extract fill info
            filled_amount = float(order.get("filled", amount))
            avg_price = float(order.get("average", 0) or order.get("price", 0))
            cost = float(order.get("cost", filled_amount * avg_price))
            
            logger.info(f"Order filled: {side} {filled_amount} @ {avg_price} = ${cost:.2f}")
            
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
        
        base_balance, quote_balance = await self.get_balances()
        if base_balance == 0 and quote_balance == 0:
            logger.error("No balance available")
            return None
        
        # Decide trade
        side = self.decide_side()
        amount = self.calculate_trade_size(side, base_balance, quote_balance, price)
        
        if not amount:
            # Try opposite side if this side has no balance
            side = "buy" if side == "sell" else "sell"
            amount = self.calculate_trade_size(side, base_balance, quote_balance, price)
            if not amount:
                logger.warning("No valid trade size for either side — check balances")
                return None
        
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
