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
import json

from app.database import get_db, Bot, Client, Wallet, BotWallet, BotTrade
from app.security import get_current_client, check_bot_access
from app.wallet_encryption import encrypt_private_key, decrypt_private_key
from app.bot_runner import bot_runner
from typing import List
from sqlalchemy import text

logger = logging.getLogger(__name__)

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
    logger.info(f"🔵 Creating bot via /bots/create: id={bot_id}, name={request.name}, bot_type={request.bot_type}, account={request.account}")
    
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
    
    # Verify bot_type was saved correctly
    db.refresh(bot)
    if bot.bot_type != request.bot_type:
        logger.error(f"⚠️ WARNING: Bot bot_type mismatch in /bots/create! Expected: {request.bot_type}, Got: {bot.bot_type}")
        # Fix it via raw SQL if needed
        from sqlalchemy import text
        db.execute(text("UPDATE bots SET bot_type = :bot_type WHERE id = :bot_id"), {
            "bot_type": request.bot_type,
            "bot_id": bot_id
        })
        db.commit()
        logger.info(f"✅ Fixed bot_type for bot {bot_id}: {request.bot_type}")
    else:
        logger.info(f"✅ Bot {bot_id} created successfully with bot_type={bot.bot_type}")

    # For Solana bots, add wallets
    # Note: Keys are stored in BOTH trading_keys (client-level) and bot_wallets (bot-level)
    # - trading_keys: For client-level key management (rotation, revocation)
    # - bot_wallets: For bot-level execution (bot runner reads from here)
    if is_solana_bot and request.wallets:
        # Determine chain from bot config or default to solana
        chain = "solana"  # Solana bots are always on Solana chain
        
        # Import address derivation functions
        from app.client_setup_routes import derive_solana_address, derive_evm_address
        
        for wallet_info in request.wallets:
            try:
                encrypted_key = encrypt_private_key(wallet_info['private_key'])
                
                # Use provided address or derive from private key
                wallet_address = wallet_info.get('address')
                if not wallet_address:
                    # Derive address from private key
                    try:
                        wallet_address = derive_solana_address(wallet_info['private_key'])
                    except Exception as e:
                        logger.warning(f"Failed to derive wallet address, using provided address: {e}")
                        raise HTTPException(
                            status_code=400,
                            detail="Wallet address required or provide valid private key to derive address"
                        )
                
                # Store in bot_wallets table (for bot execution)
                bot_wallet = BotWallet(
                    id=str(uuid.uuid4()),
                    bot_id=bot_id,
                    wallet_address=wallet_address,
                    encrypted_private_key=encrypted_key
                )
                db.add(bot_wallet)
                
                # Also store in trading_keys table (for client-level key management)
                # This allows key rotation/revocation to work for admin-created bots too
                # Mark as added by admin since this is the admin endpoint
                try:
                    db.execute(text("""
                        INSERT INTO trading_keys (client_id, encrypted_key, chain, wallet_address, added_by, created_at, updated_at)
                        VALUES (:client_id, :encrypted_key, :chain, :wallet_address, 'admin', NOW(), NOW())
                        ON CONFLICT (client_id) 
                        DO UPDATE SET 
                            encrypted_key = :encrypted_key,
                            chain = :chain,
                            wallet_address = :wallet_address,
                            added_by = 'admin',
                            updated_at = NOW()
                    """), {
                        "client_id": client.id,
                        "encrypted_key": encrypted_key,
                        "chain": chain,
                        "wallet_address": wallet_address
                    })
                    logger.info(f"Stored encrypted key in trading_keys table for client {client.id} (added by admin)")
                except Exception as trading_keys_error:
                    # If trading_keys table doesn't exist yet (migration not run), log warning but don't fail
                    # The bot can still be created and work, just key rotation won't be available
                    logger.warning(
                        f"Failed to store key in trading_keys table (migration may not be run): {trading_keys_error}. "
                        f"Bot will still work, but key rotation/revocation may not be available."
                    )
                
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


@router.get("/debug/auth")
def debug_auth(
    request: Request,
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test wallet lookup and admin check"""
    wallet_address = wallet_address or request.headers.get("X-Wallet-Address")
    
    result = {
        "wallet_address": wallet_address,
        "wallet_found": False,
        "client_found": False,
        "is_admin": False,
        "error": None
    }
    
    try:
        if wallet_address:
            # Try wallet lookup
            wallet = db.query(Wallet).filter(Wallet.address == wallet_address.lower()).first()
            if wallet:
                result["wallet_found"] = True
                result["wallet_client_id"] = wallet.client_id
                
                # Try to get client
                client = db.query(Client).filter(Client.id == wallet.client_id).first()
                if client:
                    result["client_found"] = True
                    result["client_account_identifier"] = client.account_identifier
                    result["client_role"] = client.role
                    result["is_admin"] = client.account_identifier == "admin" or (client.role and client.role.lower() == "admin")
        else:
            result["error"] = "No wallet address provided"
    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
    
    return result


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
    
    # FIRST: Check if admin account exists (for admin access without wallet_address)
    # This allows admin to access without X-Wallet-Address header
    admin_client = db.query(Client).filter(Client.account_identifier == "admin").first()
    if admin_client:
        # If no wallet_address provided, assume admin access (for admin users)
        # Admin can access via JWT token without wallet_address header
        if not wallet_address:
            logger.info("  ℹ️  No wallet_address provided - checking for admin access...")
            # Check Authorization header for admin token
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # Token provided - allow admin access if admin account exists
                logger.info("  ✅ Authorization token found - granting admin access")
                current_client = admin_client
                is_admin = True
            else:
                logger.warning("  ⚠️  No Authorization token - requiring wallet_address")
        else:
            # Wallet address provided - check if it's admin wallet
            logger.info(f"  🔍 Wallet address provided: {wallet_address[:8]}...")
    
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
            logger.info(f"🔍 Admin query: account={account}, found {query.count()} bots before bot_type filter")
        if bot_type:
            # Filter by bot_type, but also include NULL bot_type if explicitly requested
            # This allows finding bots that need bot_type fixed
            query = query.filter((Bot.bot_type == bot_type) | (Bot.bot_type.is_(None) if bot_type == "null" else False))
            logger.info(f"🔍 Admin query: bot_type={bot_type}, found {query.count()} bots after bot_type filter")
        bots = query.all()
        logger.info(f"✅ Admin returning {len(bots)} bots for account={account}, bot_type={bot_type}")
        for bot in bots:
            logger.info(f"  - Bot: id={bot.id}, name={bot.name}, bot_type={bot.bot_type or 'NULL'}, account={bot.account}")
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
    
    logger.info(f"✅ Client returning {len(bots)} bots for account={current_client.account_identifier}, bot_type={bot_type}")
    for bot in bots:
        logger.info(f"  - Bot: id={bot.id}, name={bot.name}, bot_type={bot.bot_type or 'NULL'}, account={bot.account}")
    
    return {"bots": [bot.to_dict() for bot in bots]}


@router.post("/debug/test-volume-bot-insert")
def test_volume_bot_insert(
    account: str = Query(..., description="Account identifier (e.g., client_new_sharp_foundation)"),
    db: Session = Depends(get_db)
):
    """
    Test endpoint: Manually insert a volume bot via SQL to test if database/UI can handle it.
    This helps isolate whether the issue is in backend creation logic or UI/database.
    """
    try:
        from sqlalchemy import text
        import uuid
        
        # Get client_id from account
        client = db.query(Client).filter(Client.account_identifier == account).first()
        if not client:
            raise HTTPException(status_code=404, detail=f"Client not found for account: {account}")
        
        bot_id = str(uuid.uuid4())
        instance_name = f"{account}_{bot_id[:8]}"
        
        # Insert volume bot via raw SQL
        config_json = json.dumps({
            "daily_volume_usd": 5000,
            "min_trade_usd": 10,
            "max_trade_usd": 25,
            "interval_min_seconds": 900,
            "interval_max_seconds": 2700,
            "slippage_bps": 50
        })
        
        # Use SQLAlchemy Bot model to create bot (simpler and safer)
        # Only use columns that exist in the Bot model
        test_bot = Bot(
            id=bot_id,
            client_id=client.id,
            account=account,
            instance_name=instance_name,
            name="Sharp-VB-BitMart-Test",
            bot_type="volume",
            connector="bitmart",
            pair="SHARP/USDT",
            strategy="volume",
            status="created",
            config={
                "daily_volume_usd": 5000,
                "min_trade_usd": 10,
                "max_trade_usd": 25,
                "interval_min_seconds": 900,
                "interval_max_seconds": 2700,
                "slippage_bps": 50
            },
            stats={}
        )
        
        db.add(test_bot)
        db.flush()
        
        # Try to update exchange/chain/base_asset/quote_asset via raw SQL if columns exist
        # These columns may not exist in all database schemas
        try:
            # Check if columns exist first
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            columns = [col['name'] for col in inspector.get_columns('bots')]
            
            update_fields = {}
            if 'exchange' in columns:
                update_fields['exchange'] = 'bitmart'
            if 'chain' in columns:
                update_fields['chain'] = 'evm'
            if 'base_asset' in columns:
                update_fields['base_asset'] = 'SHARP'
            if 'quote_asset' in columns:
                update_fields['quote_asset'] = 'USDT'
            
            if update_fields:
                set_clause = ", ".join([f"{k} = :{k}" for k in update_fields.keys()])
                update_fields['bot_id'] = bot_id
                db.execute(text(f"""
                    UPDATE bots SET {set_clause} WHERE id = :bot_id
                """), update_fields)
        except Exception as update_error:
            logger.warning(f"Could not update bot fields (columns may not exist): {update_error}")
            # Don't fail - these are optional fields
        
        db.commit()
        db.refresh(test_bot)
        
        row = (test_bot.id, test_bot.name, test_bot.bot_type, test_bot.account, test_bot.client_id, test_bot.status, test_bot.created_at)
        
        db.commit()
        
        row = result.fetchone()
        
        logger.info(f"✅ Test volume bot inserted: {bot_id}")
        
        return {
            "success": True,
            "message": "Test volume bot inserted successfully. Check UI to see if it appears.",
            "bot": {
                "id": row[0],
                "name": row[1],
                "bot_type": row[2],
                "account": row[3],
                "client_id": row[4],
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None
            }
        }
    except Exception as e:
        logger.error(f"Error inserting test volume bot: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/debug/fix-bot-type/{bot_id}")
def fix_bot_type(
    bot_id: str,
    bot_type: str = Query(..., description="Bot type to set: 'volume' or 'spread'"),
    db: Session = Depends(get_db)
):
    """
    Fix bot_type for a bot that has NULL bot_type.
    Admin only.
    """
    try:
        from sqlalchemy import text
        
        # Check if bot exists
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
        
        if bot_type not in ["volume", "spread"]:
            raise HTTPException(status_code=400, detail="bot_type must be 'volume' or 'spread'")
        
        # Update bot_type
        db.execute(text("UPDATE bots SET bot_type = :bot_type WHERE id = :bot_id"), {
            "bot_type": bot_type,
            "bot_id": bot_id
        })
        db.commit()
        
        # Refresh and verify
        db.refresh(bot)
        
        logger.info(f"Fixed bot_type for {bot_id}: {bot_type}")
        
        return {
            "success": True,
            "bot_id": bot_id,
            "bot_type": bot.bot_type,
            "message": f"Bot type updated to {bot_type}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fixing bot_type: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/debug/check-bots", name="debug_check_bots")
def debug_check_bots(
    account: Optional[str] = Query(None, description="Filter by account identifier"),
    client_id: Optional[str] = Query(None, description="Filter by client_id"),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to check if bots exist in database.
    Returns raw database data for troubleshooting.
    """
    try:
        from sqlalchemy import text
        
        # First check what columns exist in bots table
        check_cols = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bots' 
            ORDER BY ordinal_position
        """))
        available_columns = [row[0] for row in check_cols.fetchall()]
        
        # Build SELECT clause with only existing columns
        select_cols = []
        col_map = {
            "id": "id",
            "name": "name", 
            "bot_type": "bot_type",
            "account": "account",
            "client_id": "client_id",
            "exchange": "exchange" if "exchange" in available_columns else None,
            "status": "status",
            "created_at": "created_at"
        }
        
        for key, col in col_map.items():
            if col and col in available_columns:
                select_cols.append(col)
        
        query = f"SELECT {', '.join(select_cols)} FROM bots WHERE 1=1"
        params = {}
        
        if account:
            query += " AND account LIKE :account"
            params["account"] = f"%{account}%"
        
        if client_id:
            query += " AND client_id LIKE :client_id"
            params["client_id"] = f"%{client_id}%"
        
        # If no filters, check for 'sharp' in name/account/client_id
        if not account and not client_id:
            query += " AND (account LIKE '%sharp%' OR client_id LIKE '%sharp%' OR name LIKE '%sharp%')"
        
        query += " ORDER BY created_at DESC LIMIT 10"
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        bots = []
        for row in rows:
            bot_dict = {}
            idx = 0
            for key, col in col_map.items():
                if col and col in available_columns:
                    value = row[idx] if idx < len(row) else None
                    if key == "created_at" and value:
                        bot_dict[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                    else:
                        bot_dict[key] = value
                    idx += 1
            bots.append(bot_dict)
        
        # Also get bot type counts
        count_query = "SELECT bot_type, COUNT(*) as count FROM bots"
        count_params = {}
        if account:
            count_query += " WHERE account LIKE :account"
            count_params["account"] = f"%{account}%"
        elif client_id:
            count_query += " WHERE client_id LIKE :client_id"
            count_params["client_id"] = f"%{client_id}%"
        else:
            count_query += " WHERE (account LIKE '%sharp%' OR client_id LIKE '%sharp%')"
        count_query += " GROUP BY bot_type"
        
        count_result = db.execute(text(count_query), count_params)
        type_counts = {row[0] or 'NULL': row[1] for row in count_result.fetchall()}
        
        return {
            "count": len(bots),
            "bots": bots,
            "bot_type_counts": type_counts,
            "available_columns": available_columns,
            "query_used": query,
            "params": params
        }
    except Exception as e:
        logger.error(f"Debug check-bots error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error querying database: {str(e)}")


@router.get("/{bot_id}")
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get a specific bot by ID."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return bot.to_dict()


@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address")
):
    """Start a stopped bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Authorization check - try wallet first, then token
    wallet_address = wallet_address or request.headers.get("X-Wallet-Address", None)
    auth_header = request.headers.get("Authorization", "")
    
    if wallet_address:
        try:
            current_client = get_current_client(wallet_address=wallet_address, db=db)
            check_bot_access(bot, current_client)
        except HTTPException:
            # Wallet auth failed - try token (admin)
            if not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Authentication required")
    elif auth_header.startswith("Bearer "):
        # Token auth (admin)
        pass
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    if bot.status == "running":
        return {"status": "already_running", "bot_id": bot_id}

    try:
        # Check if this is a CEX bot (has exchange field and not Solana)
        # Use raw SQL since exchange column may not be in SQLAlchemy model yet
        exchange = None
        chain = None
        exchange_column_exists = True
        try:
            bot_check = db.execute(text("""
                SELECT exchange, chain FROM bots WHERE id = :bot_id
            """), {"bot_id": bot_id}).first()
            
            if bot_check:
                exchange = bot_check[0] if len(bot_check) > 0 else None
                chain = bot_check[1] if len(bot_check) > 1 else None
        except Exception as sql_error:
            # Columns might not exist yet - rollback transaction and continue
            db.rollback()
            exchange_column_exists = False
            logger.warning(f"⚠️  exchange/chain columns don't exist (will use bot name fallback): {sql_error}")
        
        # CEX bot detection - check exchange field OR bot name as fallback
        # CEX exchanges: bitmart, coinstore, binance, kucoin, gateio, mexc, etc.
        # IMPORTANT: Chain must NOT be 'solana' for CEX bots
        cex_exchanges = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'okx', 'bybit', 'gate', 'htx', 'kraken']
        
        # DEBUG: Log exchange/chain detection
        logger.info(f"🔍 CEX Detection for bot {bot_id}: bot_type={bot.bot_type}, exchange={exchange}, chain={chain}, exchange_column_exists={exchange_column_exists}")
        
        # Primary detection: Use exchange column if available
        is_cex_bot = (
            bot.bot_type == 'volume' and 
            exchange and 
            exchange.lower() not in ['jupiter', ''] and
            exchange.lower() in cex_exchanges and
            (not chain or chain.lower() != 'solana')  # Chain must NOT be solana
        )
        
        # Fallback 1: If exchange is set and chain is explicitly NOT solana, treat as CEX
        if not is_cex_bot and exchange and chain and chain.lower() not in ['solana', '']:
            # Additional check: exchange should not be a known DEX
            if exchange.lower() not in ['jupiter', 'uniswap', 'pancakeswap']:
                is_cex_bot = True
                logger.info(f"✅ Detected CEX bot via fallback: exchange={exchange}, chain={chain}")
        
        # Fallback 2: If exchange column doesn't exist, detect from bot name
        if not is_cex_bot and not exchange_column_exists:
            bot_name = (bot.name or '').lower()
            cex_keywords = ['bitmart', 'binance', 'kucoin', 'coinstore', 'gateio', 'gate', 'mexc', 'bybit', 'okx', 'htx', 'kraken']
            is_cex_from_name = any(kw in bot_name for kw in cex_keywords)
            
            if is_cex_from_name and bot.bot_type == 'volume':
                is_cex_bot = True
                logger.info(f"✅ Detected CEX bot from name fallback: bot_name='{bot.name}' contains CEX keyword")
        
        logger.info(f"🔍 CEX Detection result: is_cex_bot={is_cex_bot}")
        
        # For Solana/EVM bots, start via bot runner
        if bot.bot_type in ['volume', 'spread'] and not is_cex_bot:
            try:
                bot.status = "running"
                bot.error = None
                db.commit()
            except Exception as commit_error:
                logger.warning(f"Failed to commit bot status (transaction may be aborted): {commit_error}")
                try:
                    db.rollback()
                    bot.status = "running"
                    bot.error = None
                    db.commit()
                    logger.info(f"✅ Retried and succeeded updating bot status after rollback")
                except Exception as retry_error:
                    logger.error(f"Failed to update bot status even after rollback: {retry_error}")
                    db.rollback()
                    raise
            # Start bot in background
            if bot_runner is None:
                logger.error("bot_runner is None - cannot start Solana/EVM bot")
                raise HTTPException(status_code=500, detail="Bot runner not initialized")
            await bot_runner.start_bot(bot_id, db)
            logger.info(f"Solana/EVM bot {bot_id} started")
        elif is_cex_bot:
            # CEX bots are handled by CEX bot runner automatically
            # Just set status to running and CEX runner will pick it up
            try:
                bot.status = "running"
                bot.error = None
                db.commit()
            except Exception as commit_error:
                logger.warning(f"Failed to commit bot status (transaction may be aborted): {commit_error}")
                try:
                    db.rollback()
                    bot.status = "running"
                    bot.error = None
                    db.commit()
                    logger.info(f"✅ Retried and succeeded updating bot status after rollback")
                except Exception as retry_error:
                    logger.error(f"Failed to update bot status even after rollback: {retry_error}")
                    db.rollback()
                    raise
            logger.info(f"CEX bot {bot_id} started (will be picked up by CEX runner)")
        else:
            # Hummingbot bots (future)
            # TODO: Integrate with hummingbot_client when ready
            try:
                bot.status = "running"
                bot.error = None
                db.commit()
            except Exception as commit_error:
                logger.warning(f"Failed to commit bot status (transaction may be aborted): {commit_error}")
                try:
                    db.rollback()
                    bot.status = "running"
                    bot.error = None
                    db.commit()
                    logger.info(f"✅ Retried and succeeded updating bot status after rollback")
                except Exception as retry_error:
                    logger.error(f"Failed to update bot status even after rollback: {retry_error}")
                    db.rollback()
                    raise
            logger.info(f"Bot {bot_id} started")
        
        # Update reported_status for health monitor (using raw SQL since column may not be in model yet)
        try:
            db.execute(text("""
                UPDATE bots 
                SET reported_status = 'running', status_updated_at = NOW()
                WHERE id = :bot_id
            """), {"bot_id": bot_id})
            db.commit()
        except Exception as e:
            # Column might not exist yet if migration hasn't run - log but don't fail
            logger.warning(f"Could not update reported_status (migration may not have run): {e}")
            # Rollback the failed UPDATE to clear aborted transaction
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.debug(f"Rollback after reported_status update failed: {rollback_error}")
        
        return {"status": "started", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Failed to start bot {bot_id}: {e}")
        logger.exception(e)  # Log full traceback
        # Rollback database session if transaction failed
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback database session: {rollback_error}")
        # Try to update bot status, but don't fail if session is broken
        try:
            bot.status = "error"
            bot.error = str(e)
            db.commit()
        except Exception as commit_error:
            logger.error(f"Failed to update bot error status: {commit_error}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address")
):
    """Stop a running bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Authorization check
    try:
        wallet_address = wallet_address or request.headers.get("X-Wallet-Address", None)
        if wallet_address:
            current_client = get_current_client(wallet_address=wallet_address, db=db)
            check_bot_access(bot, current_client)
        # If no wallet_address, allow (for admin with token)
    except HTTPException:
        # If get_current_client fails, check if admin token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        # Admin access allowed

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
        
        # Update reported_status and health_status for health monitor (using raw SQL since column may not be in model yet)
        try:
            db.execute(text("""
                UPDATE bots 
                SET reported_status = 'stopped', status = 'stopped',
                    health_status = 'stopped', status_updated_at = NOW()
                WHERE id = :bot_id
            """), {"bot_id": bot_id})
            db.commit()
        except Exception as e:
            # Column might not exist yet if migration hasn't run - log but don't fail
            logger.warning(f"Could not update reported_status (migration may not have run): {e}")
        
        return {"status": "stopped", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Failed to stop bot {bot_id}: {e}")
        logger.exception(e)  # Log full traceback
        # Rollback database session if transaction failed
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback database session: {rollback_error}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdateBotRequest(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None

@router.put("/{bot_id}")
def update_bot(
    bot_id: str,
    request_data: UpdateBotRequest,
    request: Request,
    db: Session = Depends(get_db),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address")
):
    """Update bot configuration."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Authorization check
    try:
        wallet_address = wallet_address or request.headers.get("X-Wallet-Address", None)
        if wallet_address:
            current_client = get_current_client(wallet_address=wallet_address, db=db)
            check_bot_access(bot, current_client)
        # If no wallet_address, allow (for admin with token)
    except HTTPException:
        # If get_current_client fails, check if admin token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        # Admin access allowed

    # Update fields if provided
    if request_data.name is not None:
        bot.name = request_data.name
    if request_data.config is not None:
        bot.config = request_data.config
    if request_data.status is not None:
        bot.status = request_data.status
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)
    
    logger.info(f"✅ Bot {bot_id} updated: name={bot.name}, status={bot.status}")

    return bot.to_dict()


@router.get("/{bot_id}/stats")
def get_bot_stats(bot_id: str, db: Session = Depends(get_db)):
    """Get bot statistics including trades from both bot_trades and trade_logs tables."""
    from sqlalchemy import text
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Get trades from bot_trades table (DEX bots)
    recent_trades_dex = db.query(BotTrade).filter(
        BotTrade.bot_id == bot_id
    ).order_by(BotTrade.created_at.desc()).limit(100).all()

    trades_data_dex = [{
        "id": t.id,
        "side": t.side,
        "amount": float(t.amount) if t.amount else None,
        "price": float(t.price) if t.price else None,
        "value_usd": float(t.value_usd) if t.value_usd else None,
        "tx_signature": t.tx_signature,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "source": "bot_trades"  # DEX trades
    } for t in recent_trades_dex]

    # Get trades from trade_logs table (CEX bots)
    trades_data_cex = []
    try:
        trade_logs = db.execute(text("""
            SELECT id, side, amount, price, cost_usd, order_id, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT 100
        """), {"bot_id": bot_id}).fetchall()
        
        trades_data_cex = [{
            "id": str(t.id),
            "side": t.side,
            "amount": float(t.amount) if t.amount else None,
            "price": float(t.price) if t.price else None,
            "value_usd": float(t.cost_usd) if t.cost_usd else None,
            "order_id": t.order_id,
            "status": "success",
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "source": "trade_logs"  # CEX trades
        } for t in trade_logs]
    except Exception as e:
        # Table might not exist - that's OK
        logger.debug(f"Could not query trade_logs table: {e}")

    # Combine and sort by created_at
    all_trades = trades_data_dex + trades_data_cex
    all_trades.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    
    # Calculate totals
    total_volume = sum(float(t.get("value_usd") or 0) for t in all_trades)
    buy_count = sum(1 for t in all_trades if t.get("side", "").lower() == "buy")
    sell_count = sum(1 for t in all_trades if t.get("side", "").lower() == "sell")

    return {
        "bot_id": bot_id,
        "bot_name": bot.name,
        "bot_type": bot.bot_type,
        "status": bot.status,
        "stats": bot.stats or {},
        "recent_trades": all_trades[:100],  # Limit to 100 most recent
        "total_trades": len(all_trades),
        "total_volume_usd": round(total_volume, 2),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "last_trade_time": bot.last_trade_time.isoformat() if bot.last_trade_time else None,
        "health_status": bot.health_status,
        "health_message": bot.health_message
    }


@router.get("/{bot_id}/trades")
def get_bot_trades(
    bot_id: str,
    limit: int = Query(50, description="Max trades to return"),
    db: Session = Depends(get_db)
):
    """
    Get all trades for a bot from both bot_trades (DEX) and trade_logs (CEX) tables.
    Returns unified format with source indicator.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    all_trades = []

    # Get trades from bot_trades table (DEX bots)
    try:
        recent_trades_dex = db.query(BotTrade).filter(
            BotTrade.bot_id == bot_id
        ).order_by(BotTrade.created_at.desc()).limit(limit).all()

        for t in recent_trades_dex:
            all_trades.append({
                "id": t.id,
                "side": t.side,
                "amount": float(t.amount) if t.amount else None,
                "price": float(t.price) if t.price else None,
                "value_usd": float(t.value_usd) if t.value_usd else None,
                "tx_signature": t.tx_signature,
                "order_id": None,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "source": "bot_trades"  # DEX trades
            })
    except Exception as e:
        logger.warning(f"Error querying bot_trades: {e}")

    # Get trades from trade_logs table (CEX bots)
    try:
        trade_logs = db.execute(text("""
            SELECT id, side, amount, price, cost_usd, order_id, created_at
            FROM trade_logs
            WHERE bot_id = :bot_id
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"bot_id": bot_id, "limit": limit}).fetchall()
        
        for t in trade_logs:
            all_trades.append({
                "id": str(t.id),
                "side": t.side,
                "amount": float(t.amount) if t.amount else None,
                "price": float(t.price) if t.price else None,
                "value_usd": float(t.cost_usd) if t.cost_usd else None,
                "tx_signature": None,
                "order_id": t.order_id,
                "status": "success",
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "source": "trade_logs"  # CEX trades
            })
    except Exception as e:
        # Table might not exist - that's OK
        logger.debug(f"Could not query trade_logs table: {e}")

    # Sort by created_at descending
    all_trades.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    
    # Calculate summary stats
    total_volume = sum(float(t.get("value_usd") or 0) for t in all_trades)
    buy_count = sum(1 for t in all_trades if t.get("side", "").lower() == "buy")
    sell_count = sum(1 for t in all_trades if t.get("side", "").lower() == "sell")

    return {
        "bot_id": bot_id,
        "bot_name": bot.name,
        "bot_type": bot.bot_type,
        "exchange": bot.exchange,
        "trades": all_trades[:limit],
        "total_trades": len(all_trades),
        "total_volume_usd": round(total_volume, 2),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "last_trade_time": bot.last_trade_time.isoformat() if bot.last_trade_time else None
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

    # Get client for trading_keys storage
    client = db.query(Client).filter(Client.id == bot.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found for this bot")
    
    # Import address derivation functions
    from app.client_setup_routes import derive_solana_address, derive_evm_address
    
    try:
        encrypted_key = encrypt_private_key(wallet.private_key)
        chain = bot.chain or "solana"  # Default to solana for Solana bots
        
        # Use provided address or derive from private key
        wallet_address = wallet.address
        if not wallet_address:
            # Derive address from private key
            try:
                if chain == "solana":
                    wallet_address = derive_solana_address(wallet.private_key)
                elif chain in ["evm", "ethereum", "polygon"]:
                    wallet_address = derive_evm_address(wallet.private_key)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Wallet address required or provide valid private key to derive address"
                    )
            except Exception as e:
                logger.warning(f"Failed to derive wallet address: {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Wallet address required or provide valid private key to derive address"
                )
        
        # Store in bot_wallets table (for bot execution)
        bot_wallet = BotWallet(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            wallet_address=wallet_address,
            encrypted_private_key=encrypted_key
        )
        db.add(bot_wallet)
        
        # Also store in trading_keys table (for client-level key management)
        # This allows key rotation/revocation to work for admin-added wallets too
        # Mark as added by admin since this is the admin endpoint
        try:
            db.execute(text("""
                INSERT INTO trading_keys (client_id, encrypted_key, chain, wallet_address, added_by, created_at, updated_at)
                VALUES (:client_id, :encrypted_key, :chain, :wallet_address, 'admin', NOW(), NOW())
                ON CONFLICT (client_id) 
                DO UPDATE SET 
                    encrypted_key = :encrypted_key,
                    chain = :chain,
                    wallet_address = :wallet_address,
                    added_by = 'admin',
                    updated_at = NOW()
            """), {
                "client_id": client.id,
                "encrypted_key": encrypted_key,
                "chain": chain,
                "wallet_address": wallet_address
            })
            logger.info(f"Stored encrypted key in trading_keys table for client {client.id} (added by admin)")
        except Exception as trading_keys_error:
            # If trading_keys table doesn't exist yet (migration not run), log warning but don't fail
            logger.warning(
                f"Failed to store key in trading_keys table (migration may not be run): {trading_keys_error}. "
                f"Wallet will still work, but key rotation/revocation may not be available."
            )
        
        db.commit()
        db.refresh(bot_wallet)

        return {
            "id": bot_wallet.id,
            "wallet_address": bot_wallet.wallet_address,
            "created_at": bot_wallet.created_at.isoformat() if bot_wallet.created_at else None
        }
    except Exception as e:
        logger.error(f"Failed to add wallet to bot {bot_id}: {e}")
        db.rollback()
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
