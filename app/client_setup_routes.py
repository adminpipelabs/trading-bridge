"""
Client Self-Service Bot Setup Routes
Allows clients to set up their own bots with encrypted private key storage.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import logging
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

from app.database import get_db, Client, Bot
from app.bot_runner import bot_runner

logger = logging.getLogger(__name__)

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
    
    try:
        # Handle base58 encoded private key
        if isinstance(private_key, str):
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

    # Derive wallet address from private key (for Solana)
    wallet_address = None
    if chain == "solana":
        try:
            wallet_address = derive_solana_address(request.private_key)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to derive wallet address: {str(e)}")

    # Encrypt private key
    try:
        encrypted_key = encrypt_key(request.private_key)
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt private key")

    # Store encrypted key in trading_keys table (using raw SQL since it's not in SQLAlchemy model)
    try:
        db.execute(text("""
            INSERT INTO trading_keys (client_id, encrypted_key, chain, created_at, updated_at)
            VALUES (:client_id, :encrypted_key, :chain, NOW(), NOW())
            ON CONFLICT (client_id) 
            DO UPDATE SET 
                encrypted_key = :encrypted_key,
                chain = :chain,
                updated_at = NOW()
        """), {
            "client_id": client_id,
            "encrypted_key": encrypted_key,
            "chain": chain
        })
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store encrypted key: {e}")
        raise HTTPException(status_code=500, detail="Failed to store encrypted key")

    # Create bot record
    import uuid
    bot_id = str(uuid.uuid4())
    
    # Merge config with defaults
    merged_config = {**bot_config["default_config"], **request.config}
    
    # For Solana bots, add base_mint and quote_mint if not provided
    if chain == "solana" and request.bot_type == "volume":
        if "base_mint" not in merged_config:
            # Default to LYNK token if not specified
            merged_config["base_mint"] = "HZG1RVn4zcRM7zEFEVGYPGoPzPAWAj2AAdvQivfmLYNK"
        if "quote_mint" not in merged_config:
            merged_config["quote_mint"] = "So11111111111111111111111111111111111111112"  # SOL

    # Create bot
    bot = Bot(
        id=bot_id,
        client_id=client_id,
        account=client.account_identifier,
        instance_name=f"{client.account_identifier}_{bot_id[:8]}",
        name=f"{bot_config['label']} - {client.name}",
        connector="jupiter" if chain == "solana" else "uniswap",
        pair="LYNK/SOL" if chain == "solana" else "SHARP/USDT",  # Default pairs
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
