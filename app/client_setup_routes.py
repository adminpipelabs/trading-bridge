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
        raise HTTPException(status_code=500, detail="Encryption not configured. Set ENCRYPTION_KEY.")
    return fernet.encrypt(private_key.encode()).decode()


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
    
    # Remove ALL whitespace (spaces, newlines, tabs) from anywhere in the key
    if isinstance(private_key, str):
        private_key = re.sub(r'\s', '', private_key)
    
    if not private_key:
        raise HTTPException(status_code=400, detail="Private key is required")
    
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
    private_key: str = Field(..., description="Private key (will be encrypted)")
    config: Dict[str, Any] = Field(..., description="Bot configuration")


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
        "description": "Market making bot that places bid/ask orders around the current price.",
        "chain": "evm",
        "default_config": {
            "bid_spread": 0.3,
            "ask_spread": 0.3,
            "order_amount": 1600,
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
    Client sets up a bot with their private key.
    Key is encrypted and stored in trading_keys table.
    Bot is created and started automatically.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Validate bot type
    if request.bot_type not in BOT_TYPE_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Invalid bot_type. Must be one of: {list(BOT_TYPE_CONFIGS.keys())}")

    bot_config = BOT_TYPE_CONFIGS[request.bot_type]
    chain = bot_config["chain"]

    # Remove ALL whitespace (spaces, newlines, tabs) from anywhere in the key
    # This prevents copy-paste errors where users accidentally include spaces
    sanitized_private_key = re.sub(r'\s', '', request.private_key) if request.private_key else ""
    if not sanitized_private_key:
        raise HTTPException(status_code=400, detail="Private key is required")

    # Derive wallet address from private key
    wallet_address = None
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

    # Encrypt private key (use sanitized key)
    try:
        encrypted_key = encrypt_key(sanitized_private_key)
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt private key")

    # Store encrypted key in trading_keys table (using raw SQL since it's not in SQLAlchemy model)
    # Mark as added by client since this is the client self-service endpoint
    try:
        # First, ensure the table exists (create if it doesn't)
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
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_trading_keys_client_id ON trading_keys(client_id)
            """))
            db.commit()
            logger.info("trading_keys table created/verified successfully")
        except Exception as create_error:
            # Table might already exist - that's fine
            logger.debug(f"trading_keys table check (may already exist): {create_error}")
            db.rollback()
        
        # Ensure the table has the required columns (for existing deployments)
        try:
            db.execute(text("""
                ALTER TABLE trading_keys 
                ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(255),
                ADD COLUMN IF NOT EXISTS added_by VARCHAR(20) DEFAULT 'client'
            """))
            db.commit()
        except Exception as alter_error:
            # Columns might already exist - that's fine
            logger.debug(f"Could not alter trading_keys table (columns may already exist): {alter_error}")
            db.rollback()
        
        db.execute(text("""
            INSERT INTO trading_keys (client_id, encrypted_key, chain, wallet_address, added_by, created_at, updated_at)
            VALUES (:client_id, :encrypted_key, :chain, :wallet_address, 'client', NOW(), NOW())
            ON CONFLICT (client_id) 
            DO UPDATE SET 
                encrypted_key = :encrypted_key,
                chain = :chain,
                wallet_address = :wallet_address,
                added_by = 'client',
                updated_at = NOW()
        """), {
            "client_id": client_id,
            "encrypted_key": encrypted_key,
            "chain": chain,
            "wallet_address": wallet_address
        })
        
        # Create admin notification for key connection
        try:
            wallet_short = f"{wallet_address[:6]}...{wallet_address[-4:]}" if wallet_address else "unknown"
            db.execute(text("""
                INSERT INTO admin_notifications (type, client_id, message, created_at)
                VALUES ('key_connected', :client_id, :message, NOW())
            """), {
                "client_id": client_id,
                "message": f"Client '{client.name}' connected trading wallet {wallet_short}"
            })
        except Exception as notif_error:
            # Notification table might not exist yet - log but don't fail
            logger.debug(f"Could not create notification (table may not exist): {notif_error}")
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store encrypted key: {e}", exc_info=True)
        # Provide more detailed error message
        error_detail = str(e)
        if "column" in error_detail.lower() and "does not exist" in error_detail.lower():
            error_detail = f"Database schema issue: {error_detail}. Please run migrations to add wallet_address and added_by columns to trading_keys table."
        raise HTTPException(status_code=500, detail=f"Failed to store encrypted key: {error_detail}")

    # Create bot record
    import uuid
    bot_id = str(uuid.uuid4())
    
    # Merge config with defaults
    merged_config = {**bot_config["default_config"], **request.config}
    
    # For Solana bots, only set quote_mint to SOL if not provided (native token)
    # Don't default base_mint - user must specify which token they want to trade
    if chain == "solana" and request.bot_type == "volume":
        if "quote_mint" not in merged_config:
            # Default quote_mint to SOL (native token for Solana)
            merged_config["quote_mint"] = "So11111111111111111111111111111111111111112"  # SOL
        # base_mint must be provided by user - don't default to specific tokens

    # Determine pair from config
    # Pair should be provided by user in config, or derived from base_mint/quote_mint later
    pair = merged_config.get("pair")  # Use pair from config if provided, otherwise None

    # Create bot
    bot = Bot(
        id=bot_id,
        client_id=client_id,
        account=client.account_identifier,
        instance_name=f"{client.account_identifier}_{bot_id[:8]}",
        name=f"{bot_config['label']} - {client.name}",
        connector="jupiter" if chain == "solana" else "uniswap",
        pair=pair,  # Use configured pair or None (user will set)
        strategy="volume" if request.bot_type == "volume" else "spread",
        bot_type=request.bot_type,
        status="stopped",  # Will be started after wallet is added
        config=merged_config,
        chain=chain,
        stats={}
    )
    
    db.add(bot)
    db.flush()

    # Add wallet to bot_wallets table
    if wallet_address:
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

    # Start the bot
    try:
        bot.status = "running"
        db.commit()
        await bot_runner.start_bot(bot_id, db)
        logger.info(f"Bot {bot_id} created and started for client {client_id}")
    except Exception as e:
        logger.error(f"Failed to start bot {bot_id}: {e}")
        # Bot is created but not started - client can start it manually
        bot.status = "stopped"
        db.commit()

    return SetupBotResponse(
        success=True,
        bot_id=bot_id,
        message="Bot created successfully. Your private key has been encrypted and stored securely."
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
    """
    from app.security import get_current_client
    
    # Get requesting wallet from header
    requesting_wallet = request.headers.get("X-Wallet-Address")
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Authorization check: Client can only check their own key status
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
            
            if not (is_admin or same_client):
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this client's key status"
                )
        else:
            # Requesting wallet not found - check if admin account exists
            admin_client = db.query(Client).filter(Client.account_identifier == "admin").first()
            if not admin_client:
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
            "chain": client.chain or "solana",
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
