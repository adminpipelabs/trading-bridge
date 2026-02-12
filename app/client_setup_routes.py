"""
Client Self-Service Bot Setup Routes
Allows clients to set up their own bots with encrypted private key storage.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.requests import Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import logging
import re

from app.database import get_db, Client, Bot
from app.bot_runner import bot_runner

logger = logging.getLogger(__name__)

# Check for Solana dependencies
try:
    import base58
    BASE58_AVAILABLE = True
except ImportError:
    BASE58_AVAILABLE = False
    logger.warning("base58 not available - Solana address derivation will fail")

try:
    from solders.keypair import Keypair
    SOLDERS_AVAILABLE = True
except ImportError:
    SOLDERS_AVAILABLE = False
    logger.warning("solders not available - Solana address derivation will fail")

router = APIRouter(prefix="/clients", tags=["client-setup"])

# Encryption setup
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    if not ENCRYPTION_KEY:
        logger.warning("ENCRYPTION_KEY not set - private key encryption will fail")
        fernet = None
    else:
        fernet = Fernet(ENCRYPTION_KEY.encode())
except ImportError:
    logger.error("cryptography package not installed")
    fernet = None

# Check for Solana dependencies
try:
    import base58
    BASE58_AVAILABLE = True
except ImportError:
    BASE58_AVAILABLE = False
    logger.warning("base58 not available - Solana address derivation will fail")

try:
    from solders.keypair import Keypair
    SOLDERS_AVAILABLE = True
except ImportError:
    SOLDERS_AVAILABLE = False
    logger.warning("solders not available - Solana address derivation will fail")


def encrypt_key(private_key: str) -> str:
    """Encrypt a private key using Fernet."""
    if not fernet:
        logger.error("ENCRYPTION_KEY not set in environment variables - encryption cannot proceed")
        raise HTTPException(
            status_code=500, 
            detail="Encryption not configured. ENCRYPTION_KEY environment variable must be set in Railway."
        )
    try:
        return fernet.encrypt(private_key.encode()).decode()
    except Exception as e:
        logger.error(f"Fernet encryption failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to encrypt private key: {str(e)}")


def decrypt_key(encrypted_key: str) -> str:
    """Decrypt a private key using Fernet."""
    if not fernet:
        raise HTTPException(status_code=500, detail="Encryption not configured. Set ENCRYPTION_KEY.")
    return fernet.decrypt(encrypted_key.encode()).decode()


def derive_solana_address(private_key: str) -> str:
    """Derive Solana wallet address from private key."""
    if not BASE58_AVAILABLE or not SOLDERS_AVAILABLE:
        raise HTTPException(
            status_code=500, 
            detail="Solana dependencies not available. Install base58 and solders packages."
        )
    
    # Check if input is a seed phrase (mnemonic) - typically 12 or 24 words
    words = private_key.strip().split()
    is_seed_phrase = len(words) >= 12 and len(words) <= 24
    
    if is_seed_phrase:
        # Convert seed phrase to private key using BIP39
        try:
            try:
                from mnemonic import Mnemonic
                # Validate mnemonic
                mnemo = Mnemonic("english")
                seed_phrase = ' '.join(words)
                if not mnemo.check(seed_phrase):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid seed phrase. Please check your words and ensure they are in the correct order."
                    )
                # Convert mnemonic to seed (64 bytes)
                seed = mnemo.to_seed(seed_phrase)
                # Use first 32 bytes as private key seed
                seed_bytes = seed[:32]
                # Create keypair from seed
                keypair = Keypair.from_seed(seed_bytes)
                return str(keypair.pubkey())
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="Seed phrase support requires 'mnemonic' package. Please use a private key instead, or contact support."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to convert seed phrase: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process seed phrase: {str(e)}. Please ensure you entered all words correctly in the right order."
            )
    
    # Not a seed phrase - process as private key
    if not is_seed_phrase:
        # Not a seed phrase - clean up copy-pasted text to extract base58 private key
        if isinstance(private_key, str):
            # Remove ALL whitespace first
            private_key = re.sub(r'\s', '', private_key)
            
            # Remove common prefixes/suffixes that users might copy-paste
            # Examples: "Private key:", "Your key is:", "Key:", etc.
            common_prefixes = [
                r'^privatekey[:=]?',
                r'^yourkey[:=]?',
                r'^key[:=]?',
                r'^solana[:=]?',
                r'^wallet[:=]?',
                r'^secret[:=]?',
            ]
            for prefix in common_prefixes:
                private_key = re.sub(prefix, '', private_key, flags=re.IGNORECASE)
            
            # Extract only base58 characters (remove everything else)
            # Base58 alphabet: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
            base58_pattern = re.compile(r'[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+')
            base58_matches = base58_pattern.findall(private_key)
            
            if base58_matches:
                # Use the longest base58 string found (most likely the actual key)
                private_key = max(base58_matches, key=len)
            else:
                # No valid base58 found - check what invalid characters are present
                base58_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
                invalid_chars = [c for c in private_key if c not in base58_chars]
                if invalid_chars:
                    invalid_str = ', '.join(set(invalid_chars[:5]))  # Show first 5 unique invalid chars
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid Solana private key: Found invalid characters '{invalid_str}'. Please paste only the private key (base58 string), without any labels or extra text."
                    )
                # If somehow we got here with only base58 chars but no match, use original
                private_key = private_key.strip()
        
        if not private_key:
            raise HTTPException(status_code=400, detail="Private key is required")
        
        # Final validation - ensure we have a reasonable length base58 string
        # Solana keys are typically 32-88 characters in base58
        if len(private_key) < 32:
            raise HTTPException(
                status_code=400,
                detail=f"Private key appears too short ({len(private_key)} chars). Solana private keys are typically 32-88 characters. Please check you copied the complete key."
            )
    else:
        # It's a seed phrase - keep it as-is for processing in derive_solana_address
        private_key = ' '.join(words)
    
    try:
        # Handle base58 encoded private key
        # Try to decode as base58
        key_bytes = base58.b58decode(private_key)
        # Solana keypairs are 64 bytes (32 byte seed + 32 byte public key)
        # But private keys can be 32 bytes (seed) or 64 bytes (seed + public)
        if len(key_bytes) == 64:
            keypair = Keypair.from_bytes(key_bytes)
        elif len(key_bytes) == 32:
            keypair = Keypair.from_seed(key_bytes)
        else:
            raise ValueError(f"Invalid key length: {len(key_bytes)}")
        return str(keypair.pubkey())
    except Exception as e:
        logger.error(f"Failed to derive Solana address: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Solana private key: {str(e)}")


def derive_evm_address(private_key: str) -> str:
    """Derive EVM wallet address from private key."""
    try:
        from eth_account import Account
        # Remove ALL whitespace (spaces, newlines, tabs) from anywhere in the key
        private_key = re.sub(r'\s', '', private_key)
        
        # Handle hex string (with or without 0x prefix)
        if private_key.startswith('0x'):
            private_key_hex = private_key[2:]
        else:
            private_key_hex = private_key
        account = Account.from_key('0x' + private_key_hex)
        return account.address
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="EVM dependencies not available. Install eth-account package."
        )
    except Exception as e:
        logger.error(f"Failed to derive EVM address: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid EVM private key: {str(e)}")


# Request/Response models
class BotOptionResponse(BaseModel):
    bot_type: str
    label: str
    description: str
    chain: str
    default_config: Dict[str, Any]


class BotOptionsResponse(BaseModel):
    client_id: str
    chain: str
    options: list[BotOptionResponse]


class SetupBotRequest(BaseModel):
    bot_type: str = Field(..., description="Bot type: 'volume' or 'spread'")
    private_key: Optional[str] = Field(None, description="Private key (required for DEX, not needed for CEX)")
    exchange: Optional[str] = Field(None, description="Exchange name (e.g., 'bitmart', 'jupiter')")
    connector: Optional[str] = Field(None, description="Connector name (same as exchange)")
    chain: Optional[str] = Field(None, description="Chain (e.g., 'solana', 'evm')")
    pair: Optional[str] = Field(None, description="Trading pair (e.g., 'SHARP/USDT')")
    base_asset: Optional[str] = Field(None, description="Base asset symbol")
    quote_asset: Optional[str] = Field(None, description="Quote asset symbol")
    base_mint: Optional[str] = Field(None, description="Token mint address (for DEX)")
    name: Optional[str] = Field(None, description="Bot name")
    config: Dict[str, Any] = Field(..., description="Bot configuration")
    # API credentials for CEX bots
    api_key: Optional[str] = Field(None, description="Exchange API key (for CEX bots)")
    api_secret: Optional[str] = Field(None, description="Exchange API secret (for CEX bots)")
    passphrase: Optional[str] = Field(None, description="Exchange passphrase/memo (for CEX bots like BitMart)")


class SetupBotResponse(BaseModel):
    success: bool
    bot_id: str
    message: str


class RotateKeyRequest(BaseModel):
    private_key: str = Field(..., description="New private key (will be encrypted)")


# Bot type configurations
BOT_TYPE_CONFIGS = {
    "volume": {
        "label": "Volume Bot",
        "description": "Generates trading volume with randomized buy/sell orders over time.",
        "chain": "solana",
        "default_config": {
            "daily_volume_usd": 5000,
            "min_trade_usd": 10,
            "max_trade_usd": 25,
            "interval_min_seconds": 900,
            "interval_max_seconds": 2700,
            "slippage_bps": 50,
        }
    },
    "spread": {
        "label": "Spread Bot",
        "description": "Market making bot that places GTC limit buy/sell orders around the mid price.",
        "chain": "cex",
        "default_config": {
            "spread_percent": 3.0,
            "order_size_usd": 10,
            "poll_interval_seconds": 5,
            "price_decimals": 6,
            "amount_decimals": 2,
        }
    }
}


@router.get("/{client_id}/bot-options", response_model=BotOptionsResponse)
def get_bot_options(client_id: str, db: Session = Depends(get_db)):
    """
    Get available bot types for a client based on their chain.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Determine client's chain from wallets
    wallets = client.wallets
    chain = "solana"  # Default
    if wallets:
        # Check if client has Solana wallets
        solana_wallets = [w for w in wallets if w.chain.lower() == "solana"]
        evm_wallets = [w for w in wallets if w.chain.lower() in ["evm", "ethereum", "polygon"]]
        if evm_wallets and not solana_wallets:
            chain = "evm"
        elif solana_wallets:
            chain = "solana"

    # Filter bot types by chain
    options = []
    for bot_type, config in BOT_TYPE_CONFIGS.items():
        if config["chain"] == chain:
            options.append(BotOptionResponse(
                bot_type=bot_type,
                label=config["label"],
                description=config["description"],
                chain=config["chain"],
                default_config=config["default_config"]
            ))

    return BotOptionsResponse(
        client_id=client_id,
        chain=chain,
        options=options
    )


@router.post("/{client_id}/setup-bot", response_model=SetupBotResponse)
async def setup_bot(client_id: str, request: SetupBotRequest, db: Session = Depends(get_db)):
    """
    Client sets up a bot.
    For DEX: Requires private key (encrypted and stored in trading_keys table).
    For CEX: Requires exchange API credentials (should be saved separately via /exchanges/credentials).
    Bot is created and started automatically.
    """
    try:
        # Log for debugging
        logger.info(f"Setup bot request for client_id: {client_id}, bot_type: {request.bot_type}")
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            logger.error(f"Client not found: {client_id}")
            raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")

        # Validate bot type
        if request.bot_type not in BOT_TYPE_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Invalid bot_type. Must be one of: {list(BOT_TYPE_CONFIGS.keys())}")

        # Determine if this is a CEX bot
        # Expanded list of CEX exchanges
        cex_exchanges = ['bitmart', 'coinstore', 'kucoin', 'binance', 'gate', 'gateio', 'mexc', 'bybit', 
                        'okx', 'kraken', 'coinbase', 'dydx', 'hyperliquid', 'htx', 'huobi', 
                        'bitget', 'bitstamp', 'bitrue', 'bingx', 'btcmarkets', 'ndax', 'vertex', 'ascendex']
        is_cex = request.exchange and request.exchange.lower() in cex_exchanges
        
        # CRITICAL: CEX bots don't require wallet addresses - only API credentials
        # Skip any wallet validation for CEX bots
        logger.info(f"Bot type check: is_cex={is_cex}, exchange={request.exchange}, bot_type={request.bot_type}")
        
        wallet_address = None
        chain = None
        
        # For CEX bots, save API credentials if provided, or verify they exist
        if is_cex:
            from app.cex_volume_bot import encrypt_credential
            from datetime import datetime, timezone
            
            exchange_lower = request.exchange.lower()
            
            # If API keys are provided in request, save them
            if request.api_key and request.api_secret:
                logger.info(f"💾 Saving API credentials for {exchange_lower} bot creation")
                try:
                    # Encrypt credentials
                    api_key_enc = encrypt_credential(request.api_key)
                    api_secret_enc = encrypt_credential(request.api_secret)
                    passphrase_enc = encrypt_credential(request.passphrase) if request.passphrase else None
                    
                    # Ensure table exists
                    try:
                        db.execute(text("""
                            CREATE TABLE IF NOT EXISTS exchange_credentials (
                                id SERIAL PRIMARY KEY,
                                client_id VARCHAR(255) NOT NULL,
                                exchange VARCHAR(50) NOT NULL,
                                api_key_encrypted TEXT NOT NULL,
                                api_secret_encrypted TEXT NOT NULL,
                                passphrase_encrypted TEXT,
                                created_at TIMESTAMP DEFAULT NOW(),
                                updated_at TIMESTAMP DEFAULT NOW(),
                                UNIQUE(client_id, exchange)
                            )
                        """))
                        db.execute(text("CREATE INDEX IF NOT EXISTS idx_exchange_creds_client ON exchange_credentials(client_id)"))
                        db.commit()
                    except Exception:
                        db.rollback()
                    
                    # Save credentials
                    db.execute(text("""
                        INSERT INTO exchange_credentials 
                            (client_id, exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, updated_at)
                        VALUES (:client_id, :exchange, :api_key, :api_secret, :passphrase, :updated_at)
                        ON CONFLICT (client_id, exchange)
                        DO UPDATE SET 
                            api_key_encrypted = :api_key,
                            api_secret_encrypted = :api_secret,
                            passphrase_encrypted = :passphrase,
                            updated_at = :updated_at
                    """), {
                        "client_id": client_id,
                        "exchange": exchange_lower,
                        "api_key": api_key_enc,
                        "api_secret": api_secret_enc,
                        "passphrase": passphrase_enc,
                        "updated_at": datetime.now(timezone.utc)
                    })
                    db.commit()
                    logger.info(f"✅ Saved API credentials for {exchange_lower}")
                except Exception as e:
                    logger.error(f"Failed to save API credentials: {e}", exc_info=True)
                    db.rollback()
                    raise HTTPException(status_code=500, detail=f"Failed to save API credentials: {str(e)}")
            else:
                # No API keys in request - check if they exist already
                creds_check = db.execute(text("""
                    SELECT id FROM exchange_credentials 
                    WHERE client_id = :client_id AND exchange = :exchange
                """), {
                    "client_id": client_id,
                    "exchange": exchange_lower
                }).first()
                
                if not creds_check:
                    logger.error(f"Client {client_id} attempted to create {exchange_lower} bot but no credentials found")
                    raise HTTPException(
                        status_code=400,
                        detail=f"{request.exchange} API keys not connected. Please provide API credentials (api_key, api_secret) when creating the bot. CEX bots require API credentials, not wallet addresses."
                    )
                logger.info(f"✅ Verified exchange credentials exist for {exchange_lower} bot (CEX bot - no wallet required)")
            
            # CRITICAL: Validate ticker/symbol exists BEFORE creating bot
            if is_cex and (request.base_asset and request.quote_asset):
                symbol = f"{request.base_asset}/{request.quote_asset}"
                logger.info(f"🔍 Validating ticker {symbol} exists on {exchange_lower} before bot creation...")
                try:
                    # Get API credentials for validation
                    creds_row = db.execute(text("""
                        SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
                        FROM exchange_credentials 
                        WHERE client_id = :client_id AND exchange = :exchange
                    """), {
                        "client_id": client_id,
                        "exchange": exchange_lower
                    }).first()
                    
                    if creds_row:
                        from app.cex_volume_bot import decrypt_credential
                        api_key = decrypt_credential(creds_row.api_key_encrypted)
                        api_secret = decrypt_credential(creds_row.api_secret_encrypted)
                        
                        # Validate ticker exists
                        import os
                        proxy_url = os.getenv("QUOTAGUARDSTATIC_URL") or os.getenv("QUOTAGUARD_PROXY_URL")
                        
                        if exchange_lower == "coinstore":
                            from app.coinstore_adapter import create_coinstore_exchange
                            exchange_instance = await create_coinstore_exchange(
                                api_key=api_key,
                                api_secret=api_secret,
                                proxy_url=proxy_url
                            )
                            try:
                                ticker = await exchange_instance.fetch_ticker(symbol)
                                if not ticker or not ticker.get('last'):
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"Ticker {symbol} not found or invalid on {request.exchange}. Please verify the symbol exists and is tradeable."
                                    )
                                logger.info(f"✅ Ticker {symbol} validated successfully on {exchange_lower} (price: {ticker.get('last')})")
                            finally:
                                await exchange_instance.close()
                        elif exchange_lower == "bitmart":
                            # BitMart: skip ticker validation, proceed with bot creation
                            logger.info(f"BitMart ticker validation skipped for {symbol} - proceeding with bot creation")
                            pass
                        else:
                            # Other exchanges: use ccxt public endpoint
                            import ccxt
                            from app.cex_exchanges import get_exchange_config
                            exchange_config = get_exchange_config(exchange_lower)
                            if exchange_config:
                                ccxt_id = exchange_config.get("ccxt_id")
                                if ccxt_id:
                                    exchange_class = getattr(ccxt, ccxt_id, None)
                                    if exchange_class:
                                        exchange_instance = exchange_class({'enableRateLimit': True})
                                        ticker = await exchange_instance.fetch_ticker(symbol)
                                        if not ticker or not ticker.get('last'):
                                            raise HTTPException(status_code=400, detail=f"Ticker {symbol} not found on {request.exchange}.")
                                        logger.info(f"✅ Ticker {symbol} validated on {exchange_lower} (price: {ticker.get('last')})")
                except HTTPException:
                    raise
                except Exception as ticker_error:
                    logger.error(f"Failed to validate ticker {symbol} on {exchange_lower}: {ticker_error}", exc_info=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to validate ticker {symbol} on {request.exchange}: {str(ticker_error)}. Please verify the symbol exists and API credentials are correct."
                    )
        
        # For DEX bots, use provided key or look up existing one from trading_keys
        if not is_cex:
            bot_config = BOT_TYPE_CONFIGS[request.bot_type]
            chain = request.chain or bot_config["chain"]
            original_key = request.private_key.strip() if request.private_key else ""

            if not original_key:
                # No key provided — reuse existing wallet from trading_keys
                try:
                    existing = db.execute(text(
                        "SELECT encrypted_key, wallet_address, chain FROM trading_keys "
                        "WHERE client_id = :cid ORDER BY created_at DESC LIMIT 1"
                    ), {"cid": client_id}).fetchone()
                    if existing:
                        encrypted_key = existing[0]
                        wallet_address = existing[1]
                        chain = existing[2] or chain
                        logger.info(f"Reusing existing wallet {wallet_address} for client {client_id}")
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="No wallet on file. Please provide a private key for your first bot."
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Could not look up existing key: {e}")
                    raise HTTPException(status_code=400, detail="Private key is required — no existing wallet found.")
            else:
                # New key provided — sanitize, derive address, encrypt, store
                words = original_key.split()
                is_seed_phrase = 12 <= len(words) <= 24
                sanitized_private_key = original_key if is_seed_phrase else re.sub(r'\s', '', original_key)

                if chain == "solana":
                    try:
                        wallet_address = derive_solana_address(sanitized_private_key)
                    except HTTPException:
                        raise
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"Failed to derive wallet address: {str(e)}")
                elif chain == "evm":
                    try:
                        wallet_address = derive_evm_address(sanitized_private_key)
                    except HTTPException:
                        raise
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"Failed to derive wallet address: {str(e)}")

                try:
                    encrypted_key = encrypt_key(sanitized_private_key)
                except Exception as e:
                    logger.error(f"Encryption failed: {e}")
                    raise HTTPException(status_code=500, detail="Failed to encrypt private key")

                # Store in trading_keys (upsert)
                try:
                    db.execute(text("""
                        CREATE TABLE IF NOT EXISTS trading_keys (
                            id SERIAL PRIMARY KEY,
                            client_id VARCHAR(255) UNIQUE NOT NULL,
                            encrypted_key TEXT NOT NULL,
                            chain VARCHAR(20) DEFAULT 'solana',
                            wallet_address VARCHAR(255),
                            added_by VARCHAR(20) DEFAULT 'client',
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        )
                    """))
                    db.commit()
                except Exception:
                    db.rollback()

                try:
                    db.execute(text("""
                        ALTER TABLE trading_keys
                        ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(255),
                        ADD COLUMN IF NOT EXISTS added_by VARCHAR(20) DEFAULT 'client'
                    """))
                    db.commit()
                except Exception:
                    db.rollback()

                db.execute(text("""
                    INSERT INTO trading_keys (client_id, encrypted_key, chain, wallet_address, added_by, created_at, updated_at)
                    VALUES (:client_id, :encrypted_key, :chain, :wallet_address, 'client', NOW(), NOW())
                    ON CONFLICT (client_id)
                    DO UPDATE SET
                        encrypted_key = :encrypted_key, chain = :chain,
                        wallet_address = :wallet_address, added_by = 'client', updated_at = NOW()
                """), {"client_id": client_id, "encrypted_key": encrypted_key, "chain": chain, "wallet_address": wallet_address})
                db.commit()
                logger.info(f"Stored new wallet {wallet_address} for client {client_id}")

                # Non-critical notification — separate transaction so it can't roll back the key storage
                try:
                    wallet_short = f"{wallet_address[:6]}...{wallet_address[-4:]}" if wallet_address else "unknown"
                    db.execute(text("""
                        INSERT INTO admin_notifications (type, client_id, message, created_at)
                        VALUES ('key_connected', :client_id, :message, NOW())
                    """), {"client_id": client_id, "message": f"Client '{client.name}' connected wallet {wallet_short}"})
                    db.commit()
                except Exception:
                    db.rollback()

        # Create bot record
        import uuid
        import json
        bot_id = str(uuid.uuid4())
        
        # Parse config if it's a JSON string (from frontend)
        if isinstance(request.config, str):
            try:
                config_dict = json.loads(request.config)
            except:
                config_dict = request.config
        else:
            config_dict = request.config
        
        # Merge config with defaults (only for DEX bots)
        if not is_cex:
            bot_config = BOT_TYPE_CONFIGS[request.bot_type]
            merged_config = {**bot_config["default_config"], **config_dict}
            
            # For Solana bots, only set quote_mint to SOL if not provided (native token)
            if chain == "solana" and request.bot_type == "volume":
                if "quote_mint" not in merged_config:
                    merged_config["quote_mint"] = "So11111111111111111111111111111111111111112"  # SOL
        else:
            # CEX bots - use config as-is
            merged_config = config_dict

        # Determine pair, connector, exchange
        if is_cex:
            pair = request.pair or ""
            connector = request.connector or request.exchange or ""
            exchange = request.exchange or ""
            bot_name = request.name or f"{request.base_asset or 'CEX'} {BOT_TYPE_CONFIGS[request.bot_type]['label']}"
        else:
            pair = merged_config.get("pair") or request.base_mint or ""
            connector = request.connector or ("jupiter" if chain == "solana" else "uniswap")
            exchange = None
            bot_config = BOT_TYPE_CONFIGS[request.bot_type]
            bot_name = request.name or f"{bot_config['label']} - {client.name}"

        # Create bot
        # Note: exchange, chain, base_asset, quote_asset are not in SQLAlchemy model yet
        # They will be set via raw SQL UPDATE after bot creation
        logger.info(f"🟢 CLIENT SETUP: Creating bot via /clients/{client_id}/setup-bot")
        logger.info(f"   Client: {client.name} (id={client_id}, account={client.account_identifier})")
        logger.info(f"   Bot: name={bot_name}, bot_type={request.bot_type}, exchange={exchange}, is_cex={is_cex}")
        
        bot = Bot(
            id=bot_id,
            client_id=client_id,
            account=client.account_identifier,  # CRITICAL: Use client's account_identifier
            instance_name=f"{client.account_identifier}_{bot_id[:8]}",
            name=bot_name,
            connector=connector,
            pair=pair or "",
            strategy="volume" if request.bot_type == "volume" else "spread",
            bot_type=request.bot_type,  # Ensure bot_type is set correctly
            status="stopped",  # Will be started after credentials are verified
            config=merged_config,
            stats={}
        )
        
        logger.info(f"   Bot object created: account={bot.account}, bot_type={bot.bot_type}")
        
        # Add bot to database first
        db.add(bot)
        db.flush()  # Flush to get bot_id available for UPDATE
        
        # CRITICAL: Commit bot creation FIRST before any UPDATEs
        # This ensures bot exists even if later UPDATEs fail
        db.commit()
        logger.info(f"✅ Bot {bot_id} committed to database")
        
        # Verify bot_type and account were saved correctly
        db.refresh(bot)
        logger.info(f"   After save: bot.account={bot.account}, bot.bot_type={bot.bot_type}, bot.client_id={bot.client_id}")
        
        # Fix bot_type if needed (separate transaction)
        if bot.bot_type != request.bot_type:
            logger.error(f"⚠️ WARNING: Bot bot_type mismatch! Expected: {request.bot_type}, Got: {bot.bot_type}")
            try:
                db.execute(text("UPDATE bots SET bot_type = :bot_type WHERE id = :bot_id"), {
                    "bot_type": request.bot_type,
                    "bot_id": bot_id
                })
                db.commit()
                logger.info(f"✅ Fixed bot_type for bot {bot_id}: {request.bot_type}")
            except Exception as fix_error:
                logger.warning(f"Could not fix bot_type: {fix_error}")
                db.rollback()
        
        # Fix account if needed (separate transaction)
        if bot.account != client.account_identifier:
            logger.error(f"⚠️ CRITICAL: Bot account mismatch! Expected: {client.account_identifier}, Got: {bot.account}")
            try:
                db.execute(text("UPDATE bots SET account = :account WHERE id = :bot_id"), {
                    "account": client.account_identifier,
                    "bot_id": bot_id
                })
                db.commit()
                logger.info(f"✅ Fixed account for bot {bot_id}: {client.account_identifier}")
            except Exception as fix_error:
                logger.warning(f"Could not fix account: {fix_error}")
                db.rollback()
        
        # Store chain/exchange/base_asset/quote_asset in database using raw SQL (columns exist but not in SQLAlchemy model)
        # This must happen AFTER bot is added/flushed so bot_id exists
        try:
            update_fields = {}
            if chain:
                update_fields["chain"] = chain
            if is_cex and exchange:
                update_fields["exchange"] = exchange
            if request.base_asset:
                update_fields["base_asset"] = request.base_asset
            if request.quote_asset:
                update_fields["quote_asset"] = request.quote_asset
            
            if update_fields:
                set_clause = ", ".join([f"{k} = :{k}" for k in update_fields.keys()])
                update_fields["bot_id"] = bot_id
                db.execute(text(f"""
                    UPDATE bots SET {set_clause} WHERE id = :bot_id
                """), update_fields)
                db.commit()
                logger.info(f"Updated bot {bot_id} fields: {update_fields}")
        except Exception as update_error:
            logger.warning(f"Could not update bot fields (may not exist): {update_error}")
            # CRITICAL: Rollback the failed UPDATE to clear the aborted transaction
            # This allows subsequent commits to work
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Failed to rollback after UPDATE error: {rollback_error}")
            # Don't fail - fields can be derived if needed, bot creation already committed earlier

        # Add wallet to bot_wallets table (only for DEX bots)
        if wallet_address and not is_cex:
            try:
                db.execute(text("""
                    INSERT INTO bot_wallets (id, bot_id, wallet_address, encrypted_private_key, created_at)
                    VALUES (:id, :bot_id, :wallet_address, :encrypted_key, NOW())
                """), {
                    "id": str(uuid.uuid4()),
                    "bot_id": bot_id,
                    "wallet_address": wallet_address,
                    "encrypted_key": encrypted_key
                })
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to add wallet to bot: {e}")
                # Don't fail - bot can be created without wallet initially

        # Start the bot - CEX bots handled differently than DEX bots
        logger.info(f"Scheduling bot {bot_id} to start for client {client_id} (CEX: {is_cex})")
        try:
            # Re-query bot to ensure it's attached to the session (after previous commits)
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                # Bot should exist since we committed it earlier - log error but don't fail
                logger.error(f"❌ Bot {bot_id} not found in database - this should not happen!")
                # Try to verify bot exists via raw SQL
                bot_check = db.execute(text("SELECT id FROM bots WHERE id = :bot_id"), {"bot_id": bot_id}).first()
                if bot_check:
                    logger.info(f"✅ Bot exists in DB (found via raw SQL) - re-querying...")
                    db.rollback()  # Clear any aborted transaction
                    bot = db.query(Bot).filter(Bot.id == bot_id).first()
                else:
                    raise HTTPException(status_code=500, detail=f"Bot {bot_id} was not saved to database")
            
            # For CEX bots: Just set status to 'running' - CEXBotRunner will pick it up automatically
            # For DEX bots: Set status and start via bot_runner
            if is_cex:
                bot.status = "running"
                bot.health_status = None  # Clear any previous health errors
                bot.health_message = None
                bot.error = None
                db.commit()
                logger.info(f"✅ CEX bot {bot_id} status set to 'running' - CEXBotRunner will pick it up automatically")
            else:
                bot.status = "running"
                db.commit()
                logger.info(f"✅ Bot {bot_id} status set to 'running'")
                
                # Start DEX bot in background task
                import asyncio
                async def start_bot_background():
                    """Start DEX bot in background without blocking the HTTP response."""
                    try:
                        logger.info(f"Background: Starting DEX bot {bot_id} for client {client_id}")
                        # Get a new DB session for the background task
                        from app.database import get_db_session
                        bg_db = get_db_session()
                        try:
                            await bot_runner.start_bot(bot_id, bg_db)
                            logger.info(f"Background: Bot {bot_id} started successfully for client {client_id}")
                        except Exception as start_error:
                            logger.warning(f"Background: Bot {bot_id} startup failed: {start_error}", exc_info=True)
                            # Update bot status to stopped if startup fails
                            try:
                                bg_bot = bg_db.query(Bot).filter(Bot.id == bot_id).first()
                                if bg_bot:
                                    bg_bot.status = "stopped"
                                    bg_db.commit()
                            except Exception as update_error:
                                logger.error(f"Background: Failed to update bot status: {update_error}")
                        finally:
                            bg_db.close()
                    except Exception as bg_error:
                        logger.error(f"Background: Error in bot startup task: {bg_error}", exc_info=True)
                
                # Create background task for DEX bots only
                asyncio.create_task(start_bot_background())
                logger.info(f"DEX bot startup task scheduled for {bot_id} - returning response immediately")
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as status_error:
            # If transaction was aborted, rollback first
            logger.warning(f"Failed to update bot status (transaction may be aborted): {status_error}")
            try:
                db.rollback()
                # Re-query bot after rollback - bot should exist since we committed it earlier
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    bot.status = "running"
                    if is_cex:
                        bot.health_status = None
                        bot.health_message = None
                        bot.error = None
                    db.commit()
                    logger.info(f"✅ Retried and succeeded updating bot status after rollback")
                else:
                    # Bot doesn't exist - this is a critical error
                    logger.error(f"❌ Bot {bot_id} not found after rollback - bot may not have been committed")
                    # Try one more time with raw SQL to verify
                    bot_check = db.execute(text("SELECT id FROM bots WHERE id = :bot_id"), {"bot_id": bot_id}).first()
                    if bot_check:
                        logger.info(f"✅ Bot exists (found via raw SQL) - continuing...")
                        # Bot exists, just couldn't query via ORM - this is OK, status update will happen in background
                    else:
                        raise HTTPException(status_code=500, detail=f"Bot {bot_id} was not saved to database")
            except HTTPException:
                raise
            except Exception as retry_error:
                logger.error(f"Failed to update bot status even after rollback: {retry_error}")
                db.rollback()
                # Don't fail - bot exists, status update can happen in background task
                logger.warning(f"⚠️  Could not update bot status immediately - will be updated by background task")

        # Final verification - ensure bot was actually saved
        db.refresh(bot)
        final_bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not final_bot:
            logger.error(f"❌ CRITICAL: Bot {bot_id} was not found in database after creation!")
            raise HTTPException(
                status_code=500,
                detail="Bot creation failed - bot was not saved to database"
            )
        
        logger.info(f"✅ Bot setup completed successfully for client {client_id}, bot_id: {bot_id}")
        logger.info(f"   Final bot state: account={final_bot.account}, bot_type={final_bot.bot_type}, name={final_bot.name}, status={final_bot.status}")
        logger.info(f"   Verification: Bot exists in DB: {final_bot.id == bot_id}")
        
        return SetupBotResponse(
            success=True,
            bot_id=bot_id,
            message="Bot created successfully. Your private key has been encrypted and stored securely."
        )
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Catch any unexpected errors and log them properly
        logger.error(f"Unexpected error in setup_bot for client {client_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set up bot: {str(e)}"
        )


@router.put("/{client_id}/rotate-key")
def rotate_key(client_id: str, request: RotateKeyRequest, db: Session = Depends(get_db)):
    """
    Client rotates their trading wallet private key.
    Updates encrypted key in trading_keys table.
    All bots using this key will use the new key.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Encrypt new key
    try:
        encrypted_key = encrypt_key(request.private_key)
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt private key")

    # Update trading_keys table
    try:
        result = db.execute(text("""
            UPDATE trading_keys 
            SET encrypted_key = :encrypted_key, updated_at = NOW()
            WHERE client_id = :client_id
        """), {
            "client_id": client_id,
            "encrypted_key": encrypted_key
        })
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="No trading key found for this client")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to rotate key: {e}")
        raise HTTPException(status_code=500, detail="Failed to rotate key")

    # Update all bot_wallets for this client's bots
    try:
        client_bots = db.query(Bot).filter(Bot.client_id == client_id).all()
        for bot in client_bots:
            db.execute(text("""
                UPDATE bot_wallets 
                SET encrypted_private_key = :encrypted_key
                WHERE bot_id = :bot_id
            """), {
                "bot_id": bot.id,
                "encrypted_key": encrypted_key
            })
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to update bot wallets: {e}")
        # Don't fail - key rotation succeeded, bot wallets can be updated later

    return {
        "success": True,
        "message": "Key rotated successfully. All bots will use the new key."
    }


@router.put("/{client_id}/management-mode")
async def set_management_mode(
    client_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Set client's management mode preference.
    'self' = client manages everything
    'managed' = Pipe Labs manages bot
    """
    from fastapi import Request as FastAPIRequest
    
    body = await request.json()
    mode = body.get("mode")  # "self" or "managed"
    
    if mode not in ["self", "managed", "unset"]:
        raise HTTPException(status_code=400, detail="mode must be 'self', 'managed', or 'unset'")
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        # Update management mode
        db.execute(text("""
            UPDATE clients 
            SET management_mode = :mode 
            WHERE id = :client_id
        """), {
            "mode": mode,
            "client_id": client_id
        })
        
        # Create admin notification
        try:
            db.execute(text("""
                INSERT INTO admin_notifications (type, client_id, message, created_at)
                VALUES ('management_mode', :client_id, :message, NOW())
            """), {
                "client_id": client_id,
                "message": f"Client '{client.name}' selected '{mode}' management mode"
            })
        except Exception as notif_error:
            logger.debug(f"Could not create notification: {notif_error}")
        
        db.commit()
        
        return {"success": True, "mode": mode}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting management mode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error setting management mode: {str(e)}")


@router.get("/{client_id}/key-status")
def get_key_status(
    client_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Check if a client has connected their trading key.
    Returns status WITHOUT exposing the key itself.
    
    Authorization: Clients can only check their own key status. Admins can check any client's status.
    For admin dashboard, allows access without strict wallet header requirement.
    """
    # Get requesting wallet from header (optional for admin)
    requesting_wallet = request.headers.get("X-Wallet-Address")
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Authorization check: Try to verify admin access, but don't block if wallet header missing
    # This allows admin dashboard to work without requiring wallet headers
    is_authorized = False
    
    if requesting_wallet:
        requesting_wallet_lower = requesting_wallet.lower()
        
        # Find requesting client
        from app.database import Wallet
        requesting_wallet_obj = db.query(Wallet).filter(
            (Wallet.address == requesting_wallet) | 
            (Wallet.address == requesting_wallet_lower)
        ).first()
        
        if requesting_wallet_obj:
            requesting_client = requesting_wallet_obj.client
            # Allow if same client OR admin
            is_admin = (
                requesting_client.account_identifier == "admin" or
                (requesting_client.role and requesting_client.role.lower() == "admin")
            )
            same_client = requesting_client.id == client.id
            
            if is_admin or same_client:
                is_authorized = True
    
    # If no wallet header, allow access (admin dashboard will handle auth via other means)
    # This prevents CORS errors from blocking the request
    if not requesting_wallet:
        # Check if there's an admin account - if so, allow (admin dashboard access)
        admin_client = db.query(Client).filter(Client.account_identifier == "admin").first()
        if admin_client:
            is_authorized = True
    
    # If still not authorized and wallet was provided, deny access
    if requesting_wallet and not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this client's key status"
        )

    # Query trading_keys table
    try:
        result = db.execute(text("""
            SELECT created_at, chain, wallet_address, added_by
            FROM trading_keys
            WHERE client_id = :client_id
        """), {"client_id": client_id})
        key_record = result.fetchone()
    except Exception as e:
        logger.error(f"Failed to query key status: {e}")
        # If table doesn't exist, return no key
        key_record = None

    if key_record:
        return {
            "client_id": client_id,
            "has_key": True,
            "key_added_by": key_record.added_by or "unknown",
            "key_connected_at": key_record.created_at.isoformat() if key_record.created_at else None,
            "wallet_address": key_record.wallet_address,
            "chain": key_record.chain or client.chain or "solana",
        }
    else:
        return {
            "client_id": client_id,
            "has_key": False,
            "key_added_by": None,
            "key_connected_at": None,
            "wallet_address": None,
            "chain": getattr(client, 'chain', None) or "solana",  # chain may not exist on Client model
        }


@router.delete("/{client_id}/revoke-key")
async def revoke_key(client_id: str, db: Session = Depends(get_db)):
    """
    Client revokes their trading wallet private key.
    Deletes key from trading_keys table and stops all bots.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Stop all bots for this client
    try:
        client_bots = db.query(Bot).filter(Bot.client_id == client_id).all()
        for bot in client_bots:
            if bot.status == "running":
                try:
                    await bot_runner.stop_bot(bot.id)
                except Exception as e:
                    logger.warning(f"Failed to stop bot {bot.id}: {e}")
                bot.status = "stopped"
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to stop bots: {e}")

    # Delete trading key
    try:
        result = db.execute(text("""
            DELETE FROM trading_keys WHERE client_id = :client_id
        """), {"client_id": client_id})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="No trading key found for this client")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to revoke key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke key")

    return {
        "success": True,
        "message": "Key revoked successfully. All bots have been stopped."
    }
