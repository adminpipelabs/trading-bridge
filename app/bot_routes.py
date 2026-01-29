"""
Bot management routes with PostgreSQL persistence.
Synchronous routes for SQLAlchemy compatibility.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import logging

from app.database import get_db, Bot, Client, Wallet, BotWallet, BotTrade
from app.security import get_current_client
from app.wallet_encryption import encrypt_private_key, decrypt_private_key
from app.bot_runner import bot_runner
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["bots"])


# ============================================================
# Request/Response Models
# ============================================================

class BotConfig(BaseModel):
    bid_spread: Optional[float] = 0.003
    ask_spread: Optional[float] = 0.003
    order_amount: Optional[float] = 1000
    order_interval: Optional[int] = 60


class CreateBotRequest(BaseModel):
    name: str = Field(..., description="Bot display name")
    account: str = Field(..., description="Account identifier (must match client account_identifier)")
    connector: Optional[str] = Field(None, description="Exchange connector: 'bitmart', 'jupiter' (optional for Solana bots)")
    pair: Optional[str] = Field(None, description="Trading pair: 'SHARP/USDT', 'SOL/USDC' (optional for Solana bots)")
    strategy: Optional[str] = Field(None, description="Strategy: 'spread', 'volume', 'grid' (optional for Solana bots)")
    bot_type: Optional[str] = Field(None, description="Bot type: 'volume', 'spread' (for Solana bots)")
    config: Optional[dict] = Field(default_factory=dict, description="Bot configuration (JSON object)")
    wallets: Optional[List[dict]] = Field(default_factory=list, description="Wallets for Solana bots: [{'address': str, 'private_key': str}]")


class WalletInfo(BaseModel):
    address: str
    private_key: str


# ============================================================
# Database Dependency
# ============================================================
# Using get_db from app.database (imported above)


# ============================================================
# Helper Functions
# ============================================================

def generate_instance_name(bot_id: str, account: str) -> str:
    """Generate Hummingbot instance name."""
    return f"{account}_{bot_id[:8]}"


# ============================================================
# Routes (Synchronous)
# ============================================================

@router.post("/create")
def create_bot(request: CreateBotRequest, db: Session = Depends(get_db)):
    """
    Create a new bot and persist to database.
    Supports both Hummingbot-style bots and Solana bots.
    """
    bot_id = str(uuid.uuid4())
    
    # Verify client exists
    client = db.query(Client).filter(
        Client.account_identifier == request.account
    ).first()

    if not client:
        raise HTTPException(
            status_code=400,
            detail=f"No client found with account_identifier '{request.account}'"
        )

    # Determine if this is a Solana bot
    is_solana_bot = request.bot_type in ['volume', 'spread']
    
    # Validate bot_type if provided
    if request.bot_type and request.bot_type not in ['volume', 'spread']:
        raise HTTPException(
            status_code=400,
            detail="bot_type must be 'volume' or 'spread' for Solana bots"
        )
    
    # Validate Solana bot requirements
    if is_solana_bot:
        if not request.config:
            raise HTTPException(
                status_code=400,
                detail="config is required for Solana bots"
            )
        if not request.wallets or len(request.wallets) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one wallet is required for Solana bots"
            )
        # Validate wallet format
        for wallet_info in request.wallets:
            if 'address' not in wallet_info or 'private_key' not in wallet_info:
                raise HTTPException(
                    status_code=400,
                    detail="Each wallet must have 'address' and 'private_key' fields"
                )
            # Basic Solana address validation (32-44 base58 chars)
            addr = wallet_info['address']
            if not (32 <= len(addr) <= 44):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid Solana wallet address format: {addr} (must be 32-44 characters)"
                )
    
    # Generate instance_name only for Hummingbot bots
    instance_name = None
    if not is_solana_bot:
        instance_name = generate_instance_name(bot_id, request.account)
        if not request.connector or not request.pair or not request.strategy:
            raise HTTPException(
                status_code=400,
                detail="connector, pair, and strategy are required for Hummingbot bots"
            )

    # Create bot record
    bot = Bot(
        id=bot_id,
        client_id=client.id,
        account=request.account,
        instance_name=instance_name,
        name=request.name,
        connector=request.connector,
        pair=request.pair,
        strategy=request.strategy,
        bot_type=request.bot_type,
        status="stopped",  # Start stopped, user must explicitly start
        config=request.config if isinstance(request.config, dict) else (request.config.dict() if request.config else {}),
        stats={}  # Initialize empty stats
    )

    db.add(bot)
    db.flush()  # Flush to get bot.id

    # For Solana bots, add wallets
    if is_solana_bot and request.wallets:
        for wallet_info in request.wallets:
            try:
                encrypted_key = encrypt_private_key(wallet_info['private_key'])
                bot_wallet = BotWallet(
                    id=str(uuid.uuid4()),
                    bot_id=bot_id,
                    wallet_address=wallet_info['address'],
                    encrypted_private_key=encrypted_key
                )
                db.add(bot_wallet)
            except Exception as e:
                logger.error(f"Failed to add wallet to bot {bot_id}: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to encrypt wallet private key: {e}"
                )

    # Deploy to Hummingbot (only for Hummingbot bots)
    if not is_solana_bot:
        try:
            # TODO: Integrate with hummingbot_client when ready
            # from app.hummingbot_client import hummingbot
            # hummingbot.deploy_script(...)
            bot.status = "created"
            logger.info(f"Bot {bot_id} created successfully")
        except Exception as e:
            logger.error(f"Failed to deploy bot {bot_id}: {e}")
            bot.status = "deploy_failed"
            bot.error = str(e)
    else:
        logger.info(f"Solana bot {bot_id} created successfully")

    db.commit()
    db.refresh(bot)

    return bot.to_dict()


@router.get("")
def list_bots(
    request: Request,
    account: Optional[str] = Query(None, description="Filter by account identifier"),
    bot_type: Optional[str] = Query(None, description="Filter by bot type: 'volume', 'spread'"),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
):
    """
    List bots with authentication and authorization.
    - Admin users can see all bots (wallet_address optional if authenticated via token)
    - Client users must provide X-Wallet-Address header and only see their own bots
    - If account parameter is provided, verifies user has access to that account
    """
    current_client = None
    is_admin = False
    
    # Get wallet_address from header (use parameter or request header)
    wallet_address = wallet_address or request.headers.get("X-Wallet-Address")
    
    logger.info(f"🔍 list_bots called with wallet_address: {wallet_address[:8] if wallet_address else 'None'}...")
    
    # If wallet_address provided, get client and check if admin
    if wallet_address:
        try:
            # Try to find wallet (handle case sensitivity for Solana)
            wallet = None
            
            # Try original case first (for Solana addresses - case sensitive)
            wallet = db.query(Wallet).filter(Wallet.address == wallet_address).first()
            logger.debug(f"  Original case lookup: {'found' if wallet else 'not found'}")
            
            # Try lowercase if not found (for EVM addresses and case-insensitive lookups)
            if not wallet:
                wallet_lower = wallet_address.lower()
                wallet = db.query(Wallet).filter(Wallet.address == wallet_lower).first()
                logger.debug(f"  Lowercase lookup: {'found' if wallet else 'not found'}")
            
            # Also try case-insensitive match (some wallets might be stored in different case)
            if not wallet:
                # Use ILIKE for case-insensitive match (PostgreSQL specific)
                from sqlalchemy import func
                wallet = db.query(Wallet).filter(
                    func.lower(Wallet.address) == wallet_address.lower()
                ).first()
                logger.debug(f"  Case-insensitive lookup: {'found' if wallet else 'not found'}")
            
            if wallet:
                try:
                    current_client = wallet.client
                    if current_client:
                        is_admin = current_client.account_identifier == "admin" or (current_client.role and current_client.role.lower() == "admin")
                        logger.info(f"  ✅ Wallet found, client: {current_client.account_identifier}, is_admin: {is_admin}")
                    else:
                        logger.warning(f"  ⚠️  Wallet found but wallet.client is None (client_id: {wallet.client_id})")
                        # Fallback: Load client directly
                        current_client = db.query(Client).filter(Client.id == wallet.client_id).first()
                        if current_client:
                            is_admin = current_client.account_identifier == "admin" or (current_client.role and current_client.role.lower() == "admin")
                            logger.info(f"  ✅ Fallback: Loaded client directly: {current_client.account_identifier}, is_admin: {is_admin}")
                        else:
                            logger.error(f"  ❌ Client not found for wallet.client_id: {wallet.client_id}")
                except Exception as client_error:
                    logger.error(f"  ❌ Error accessing wallet.client: {client_error}")
                    logger.exception(client_error)
                    # Fallback: Try to load client directly
                    try:
                        current_client = db.query(Client).filter(Client.id == wallet.client_id).first()
                        if current_client:
                            is_admin = current_client.account_identifier == "admin" or (current_client.role and current_client.role.lower() == "admin")
                            logger.info(f"  ✅ Exception fallback: Loaded client directly: {current_client.account_identifier}, is_admin: {is_admin}")
                        else:
                            logger.error(f"  ❌ Exception fallback: Client not found for wallet.client_id: {wallet.client_id}")
                            raise HTTPException(
                                status_code=500,
                                detail=f"Wallet found but associated client not found: {wallet.client_id}"
                            )
                    except HTTPException:
                        raise
                    except Exception as fallback_error:
                        logger.error(f"  ❌ Fallback client load also failed: {fallback_error}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Error loading client for wallet: {str(fallback_error)}"
                        )
        except Exception as wallet_lookup_error:
            logger.error(f"  ❌ Error in wallet lookup: {wallet_lookup_error}")
            logger.exception(wallet_lookup_error)
            raise HTTPException(
                status_code=500,
                detail=f"Error looking up wallet: {str(wallet_lookup_error)}"
            )
        else:
            # Wallet not in wallets table - try to find client directly
            # This handles cases where admin wallet is only in clients table
            client_by_wallet = db.query(Client).filter(
                Client.wallet_address == wallet_address
            ).first()
            
            # Also try lowercase for EVM addresses
            if not client_by_wallet:
                client_by_wallet = db.query(Client).filter(
                    Client.wallet_address == wallet_address.lower()
                ).first()
            
            if client_by_wallet:
                current_client = client_by_wallet
                is_admin = current_client.account_identifier == "admin" or current_client.role == "admin"
            else:
                # Wallet not found - check if admin account exists and allow access
                # This handles cases where admin wallet isn't in wallets table
                admin_client = db.query(Client).filter(
                    Client.account_identifier == "admin"
                ).first()
                
                if admin_client:
                    # Allow admin access even if wallet not in wallets table
                    # Check by account_identifier == "admin" (more reliable than role field)
                    current_client = admin_client
                    is_admin = admin_client.account_identifier == "admin"
                    if is_admin:
                        logger.info(f"Admin access granted via account_identifier check for wallet: {wallet_address[:8]}...")
                    else:
                        logger.warning(f"Account with identifier 'admin' found but is_admin=False. Role: {admin_client.role}")
                else:
                    # Wallet not found and no admin account - raise error
                    raise HTTPException(
                        status_code=403,
                        detail="Wallet address not registered. Please ensure your wallet is registered in the system."
                    )
    
    # Admin can list all bots (or filter by client_id/account)
    if is_admin:
        query = db.query(Bot)
        if account:
            query = query.filter(Bot.account == account)
        if bot_type:
            query = query.filter(Bot.bot_type == bot_type)
        bots = query.all()
        return {"bots": [bot.to_dict() for bot in bots]}
    
    # Non-admin must have wallet, only sees their bots
    if not wallet_address:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide X-Wallet-Address header."
        )
    
    # Ensure current_client is set for non-admin users
    if not current_client:
        raise HTTPException(
            status_code=403,
            detail="Wallet address not registered or associated with a client."
        )
    
    # Build query for client's bots only
    query = db.query(Bot).filter(Bot.account == current_client.account_identifier)
    
    if account:
        # Account parameter provided - verify access
        if account != current_client.account_identifier:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. You can only access your own account ({current_client.account_identifier})"
            )
        query = query.filter(Bot.account == account)
    
    # Filter by bot_type if provided
    if bot_type:
        query = query.filter(Bot.bot_type == bot_type)
    
    bots = query.all()
    
    return {"bots": [bot.to_dict() for bot in bots]}


@router.get("/{bot_id}")
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get a specific bot by ID."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return bot.to_dict()


@router.post("/{bot_id}/start")
async def start_bot(bot_id: str, db: Session = Depends(get_db)):
    """Start a stopped bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if bot.status == "running":
        return {"status": "already_running", "bot_id": bot_id}

    try:
        # For Solana bots, start via bot runner
        if bot.bot_type in ['volume', 'spread']:
            bot.status = "running"
            bot.error = None
            db.commit()
            # Start bot in background
            await bot_runner.start_bot(bot_id, db)
            logger.info(f"Solana bot {bot_id} started")
        else:
            # Hummingbot bots (future)
            # TODO: Integrate with hummingbot_client when ready
            bot.status = "running"
            bot.error = None
            db.commit()
            logger.info(f"Bot {bot_id} started")
        
        return {"status": "started", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Failed to start bot {bot_id}: {e}")
        bot.status = "error"
        bot.error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str, db: Session = Depends(get_db)):
    """Stop a running bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if bot.status == "stopped":
        return {"status": "already_stopped", "bot_id": bot_id}

    try:
        # For Solana bots, stop via bot runner
        if bot.bot_type in ['volume', 'spread']:
            await bot_runner.stop_bot(bot_id)
            bot.status = "stopped"
            db.commit()
            logger.info(f"Solana bot {bot_id} stopped")
        else:
            # Hummingbot bots (future)
            # TODO: Integrate with hummingbot_client when ready
            bot.status = "stopped"
            db.commit()
            logger.info(f"Bot {bot_id} stopped")
        
        return {"status": "stopped", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Failed to stop bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{bot_id}")
def update_bot(bot_id: str, request: dict, db: Session = Depends(get_db)):
    """Update bot configuration."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Update fields if provided
    if "name" in request:
        bot.name = request["name"]
    if "config" in request:
        bot.config = request["config"]
    if "status" in request:
        bot.status = request["status"]
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)

    return bot.to_dict()


@router.get("/{bot_id}/stats")
def get_bot_stats(bot_id: str, db: Session = Depends(get_db)):
    """Get bot statistics."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Get recent trades
    recent_trades = db.query(BotTrade).filter(
        BotTrade.bot_id == bot_id
    ).order_by(BotTrade.created_at.desc()).limit(100).all()

    trades_data = [{
        "id": t.id,
        "side": t.side,
        "amount": float(t.amount) if t.amount else None,
        "price": float(t.price) if t.price else None,
        "value_usd": float(t.value_usd) if t.value_usd else None,
        "tx_signature": t.tx_signature,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in recent_trades]

    return {
        "bot_id": bot_id,
        "stats": bot.stats or {},
        "recent_trades": trades_data,
        "total_trades": len(trades_data)
    }


@router.get("/{bot_id}/wallets")
def get_bot_wallets(bot_id: str, db: Session = Depends(get_db)):
    """Get all wallets for a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot_wallets = db.query(BotWallet).filter(BotWallet.bot_id == bot_id).all()
    
    return [{
        "id": w.id,
        "wallet_address": w.wallet_address,
        "created_at": w.created_at.isoformat() if w.created_at else None
    } for w in bot_wallets]


@router.post("/{bot_id}/wallets")
def add_bot_wallet(bot_id: str, wallet: WalletInfo, db: Session = Depends(get_db)):
    """Add a wallet to a Solana bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if not bot.bot_type:
        raise HTTPException(
            status_code=400,
            detail="Wallets can only be added to Solana bots (bot_type must be set)"
        )

    # Check if wallet already exists
    existing = db.query(BotWallet).filter(
        BotWallet.bot_id == bot_id,
        BotWallet.wallet_address == wallet.address
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Wallet already exists for this bot"
        )

    try:
        encrypted_key = encrypt_private_key(wallet.private_key)
        bot_wallet = BotWallet(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            wallet_address=wallet.address,
            encrypted_private_key=encrypted_key
        )
        db.add(bot_wallet)
        db.commit()
        db.refresh(bot_wallet)

        return {
            "id": bot_wallet.id,
            "wallet_address": bot_wallet.wallet_address,
            "created_at": bot_wallet.created_at.isoformat() if bot_wallet.created_at else None
        }
    except Exception as e:
        logger.error(f"Failed to add wallet to bot {bot_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to add wallet: {e}"
        )


@router.delete("/{bot_id}/wallets/{wallet_address}")
def remove_bot_wallet(bot_id: str, wallet_address: str, db: Session = Depends(get_db)):
    """Remove a wallet from a Solana bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    bot_wallet = db.query(BotWallet).filter(
        BotWallet.bot_id == bot_id,
        BotWallet.wallet_address == wallet_address
    ).first()

    if not bot_wallet:
        raise HTTPException(status_code=404, detail="Wallet not found for this bot")

    db.delete(bot_wallet)
    db.commit()

    return {"status": "deleted", "wallet_address": wallet_address}


@router.delete("/{bot_id}")
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    """Delete a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Stop bot first if running
    if bot.status == "running":
        try:
            # hummingbot.stop_bot(bot.instance_name)
            pass
        except Exception as e:
            logger.warning(f"Failed to stop bot before deletion: {e}")

    db.delete(bot)
    db.commit()

    return {"status": "deleted", "bot_id": bot_id}
