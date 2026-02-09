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

from app.database import get_db, Bot, Client, Wallet, BotWallet, BotTrade, Connector
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
    include_balances: Optional[bool] = Query(True, description="Include balance data for each bot (default: true)"),
    db: Session = Depends(get_db)
):
    logger.info(f"📋 GET /bots called: account={account}, bot_type={bot_type}, include_balances={include_balances}, wallet={wallet_address[:10] if wallet_address else 'None'}...")
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
        
        bot_dicts = [bot.to_dict() for bot in bots]
        
        # Include balances if requested - BUT DON'T BLOCK THE RESPONSE
        if include_balances:
            import asyncio
            from app.database import SessionLocal
            
            async def fetch_balance_for_bot(bot_id: str):
                """Helper to fetch balance for a single bot with timeout"""
                try:
                    async_db = SessionLocal()
                    try:
                        # Add timeout per bot - don't wait more than 5 seconds per bot
                        balance_data = await asyncio.wait_for(
                            get_bot_stats(bot_id, async_db),
                            timeout=5.0
                        )
                        return balance_data
                    finally:
                        async_db.close()
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching balance for bot {bot_id} (5s)")
                    return None
                except Exception as e:
                    logger.warning(f"Could not fetch balance for bot {bot_id}: {e}")
                    return None
            
            async def fetch_all_balances():
                tasks = [fetch_balance_for_bot(bot.id) for bot in bots]
                # Overall timeout - don't wait more than 8 seconds total
                return await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=8.0
                )
            
            try:
                # Handle event loop - check if one exists
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Event loop is running - can't use asyncio.run()
                        # Fall back to creating a new loop in a thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, fetch_all_balances())
                            balances = future.result(timeout=10)  # Overall timeout
                    else:
                        balances = loop.run_until_complete(fetch_all_balances())
                except (RuntimeError, asyncio.TimeoutError, concurrent.futures.TimeoutError):
                    # Timeout or no event loop - return bots without balances
                    logger.warning(f"Timeout or error fetching balances - returning bots without balances")
                    balances = [None] * len(bots)
                
                for bot_dict, balance_data in zip(bot_dicts, balances):
                    if isinstance(balance_data, Exception) or balance_data is None:
                        bot_dict["balance"] = {"available": {}, "locked": {}, "volume_24h": 0, "trades_24h": {"buys": 0, "sells": 0}}
                    else:
                        bot_dict["balance"] = {
                            "available": balance_data.get("available", {}),
                            "locked": balance_data.get("locked", {}),
                            "volume_24h": balance_data.get("volume_24h", 0),
                            "trades_24h": balance_data.get("trades_24h", {"buys": 0, "sells": 0})
                        }
            except Exception as e:
                logger.error(f"Error fetching balances: {e} - returning bots without balances")
                # Don't fail - just return bots without balances
                for bot_dict in bot_dicts:
                    bot_dict["balance"] = {"available": {}, "locked": {}, "volume_24h": 0, "trades_24h": {"buys": 0, "sells": 0}}
        
        return {"bots": bot_dicts}
    
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
    
    bot_dicts = [bot.to_dict() for bot in bots]
    
    logger.info(f"📊 Client has {len(bot_dicts)} bots, include_balances={include_balances}")
    
    # Include balances if requested
    if include_balances:
        logger.info(f"💰 Balance fetch requested for {len(bot_dicts)} bots")
        import asyncio
        from app.database import SessionLocal
        
        async def fetch_balance_for_bot(bot_id: str):
            """Helper to fetch balance for a single bot"""
            try:
                async_db = SessionLocal()
                try:
                    balance_data = await get_bot_stats(bot_id, async_db)
                    return balance_data
                finally:
                    async_db.close()
            except Exception as e:
                logger.warning(f"Could not fetch balance for bot {bot_id}: {e}")
                return None
        
        async def fetch_all_balances():
            tasks = [fetch_balance_for_bot(bot.id) for bot in bots]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        try:
            # Handle event loop - check if one exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Event loop is running - can't use asyncio.run()
                    # Fall back to creating a new loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, fetch_all_balances())
                        balances = future.result(timeout=30)
                else:
                    balances = loop.run_until_complete(fetch_all_balances())
            except (RuntimeError, asyncio.TimeoutError):
                # No event loop or timeout - create one
                import concurrent.futures
                try:
                    balances = asyncio.run(fetch_all_balances())
                except Exception as e:
                    logger.error(f"Error fetching balances: {e} - returning bots without balances")
                    balances = [None] * len(bots)
            for bot_dict, balance_data in zip(bot_dicts, balances):
                if isinstance(balance_data, Exception):
                    bot_dict["balance"] = {"available": {}, "locked": {}, "volume_24h": 0, "trades_24h": {"buys": 0, "sells": 0}}
                elif balance_data:
                    bot_dict["balance"] = {
                        "available": balance_data.get("available", {}),
                        "locked": balance_data.get("locked", {}),
                        "volume_24h": balance_data.get("volume_24h", 0),
                        "trades_24h": balance_data.get("trades_24h", {"buys": 0, "sells": 0})
                    }
                else:
                    bot_dict["balance"] = {"available": {}, "locked": {}, "volume_24h": 0, "trades_24h": {"buys": 0, "sells": 0}}
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
    
    return {"bots": bot_dicts}


@router.get("/with-balances")
async def list_bots_with_balances(
    request: Request,
    account: Optional[str] = Query(None, description="Filter by account identifier"),
    bot_type: Optional[str] = Query(None, description="Filter by bot type: 'volume', 'spread'"),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
):
    """
    List bots with balance data included.
    This is an async endpoint that fetches balances for each bot in parallel.
    Returns the same format as /bots but with a 'balance' field added to each bot.
    """
    from starlette.concurrency import run_in_threadpool
    
    # Use the sync list_bots logic to get bots
    def _get_bots():
        return list_bots(request, account, bot_type, wallet_address, db)
    
    bots_response = await run_in_threadpool(_get_bots)
    bots = bots_response.get("bots", [])
    
    # Fetch balances for all bots in parallel
    import asyncio
    
    async def fetch_balance_for_bot(bot_id: str):
        """Helper to fetch balance for a single bot"""
        try:
            # Create a new db session for this async call (required for async operations)
            from app.database import SessionLocal
            async_db = SessionLocal()
            try:
                balance_data = await get_bot_stats(bot_id, async_db)
                return balance_data
            finally:
                async_db.close()
        except Exception as e:
            logger.warning(f"Could not fetch balance for bot {bot_id}: {e}")
            return {
                "available": {},
                "locked": {},
                "volume_24h": 0,
                "trades_24h": {"buys": 0, "sells": 0}
            }
    
    # Fetch balances for all bots in parallel WITH TIMEOUT to prevent hanging
    balance_tasks = [fetch_balance_for_bot(bot["id"]) for bot in bots]
    try:
        # Set overall timeout - don't wait more than 10 seconds total for all balances
        balances = await asyncio.wait_for(
            asyncio.gather(*balance_tasks, return_exceptions=True),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"⚠️  Timeout fetching balances for {len(bots)} bots - returning bots without balances")
        balances = [None] * len(bots)
    
    # Add balances to each bot dict
    for bot_dict, balance_data in zip(bots, balances):
        if isinstance(balance_data, Exception):
            logger.error(f"Error fetching balance for bot {bot_dict['id']}: {balance_data}")
            bot_dict["balance"] = {
                "available": {},
                "locked": {},
                "volume_24h": 0,
                "trades_24h": {"buys": 0, "sells": 0}
            }
        elif balance_data:
            bot_dict["balance"] = {
                "available": balance_data.get("available", {}),
                "locked": balance_data.get("locked", {}),
                "volume_24h": balance_data.get("volume_24h", 0),
                "trades_24h": balance_data.get("trades_24h", {"buys": 0, "sells": 0})
            }
        else:
            bot_dict["balance"] = {
                "available": {},
                "locked": {},
                "volume_24h": 0,
                "trades_24h": {"buys": 0, "sells": 0}
            }
    
    return {"bots": bots}


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


@router.get("/{bot_id}/trades-history")
def get_bot_trades_history(bot_id: str, db: Session = Depends(get_db)):
    """Get bot trade history from both bot_trades and trade_logs tables."""
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
    
    # Calculate last_trade_time from trades
    last_trade_time = None
    if all_trades:
        last_trade = all_trades[0]
        if last_trade.get("created_at"):
            last_trade_time = last_trade["created_at"]

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
        "last_trade_time": last_trade_time,
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
    
    # Calculate last_trade_time from trades
    last_trade_time = None
    if all_trades:
        last_trade = all_trades[0]
        if last_trade.get("created_at"):
            last_trade_time = last_trade["created_at"]

    return {
        "bot_id": bot_id,
        "bot_name": bot.name,
        "bot_type": bot.bot_type,
        "exchange": bot.connector,  # Bot model uses 'connector' field, not 'exchange'
        "trades": all_trades[:limit],
        "total_trades": len(all_trades),
        "total_volume_usd": round(total_volume, 2),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "last_trade_time": last_trade_time
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


@router.get("/{bot_id}/balance-and-volume")
async def get_bot_balance_and_volume(bot_id: str, db: Session = Depends(get_db)):
    """
    Get bot balance (Available | Locked) and Volume stats.
    Returns unified format for all bot types.
    
    For Spread Bots: Volume = total value traded
    For Volume Bots: Volume = buy/sell count
    """
    from sqlalchemy import text
    from app.api.client_data import sync_connectors_to_exchange_manager
    from app.services.exchange import exchange_manager
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get pair to determine base/quote currencies
    pair = bot.pair or (f"{bot.base_asset}/{bot.quote_asset}" if bot.base_asset and bot.quote_asset else None)
    if not pair:
        return {
            "bot_id": bot_id,
            "available": {},
            "locked": {},
            "volume": None,
            "error": "Bot missing pair configuration"
        }
    
    base, quote = pair.split("/")
    
    # Initialize result
    result = {
        "bot_id": bot_id,
        "bot_type": bot.bot_type,
        "pair": pair,
        "available": {base: 0, quote: 0},
        "locked": {base: 0, quote: 0},
        "volume": None
    }
    
    # For CEX bots, fetch balance from exchange (even if bot is stopped)
    # Safely check connector (could be None)
    connector_lower = (bot.connector or '').lower() if bot.connector else ''
    logger.info(f"🔍 Balance-and-volume request for bot {bot_id}: name={bot.name}, type={bot.bot_type}, connector={bot.connector}, account={bot.account}")
    logger.info(f"🔍 Bot details: connector_lower={connector_lower}, bot_type={bot.bot_type}, pair={pair}")
    
    if bot.bot_type == 'volume' or bot.bot_type == 'spread' or (connector_lower and connector_lower not in ['jupiter', 'solana']):
        logger.info(f"✅ Bot {bot_id} identified as CEX bot - proceeding with balance fetch")
        try:
            # Sync connectors for this account WITH TIMEOUT
            logger.info(f"🔄 Syncing connectors for account {bot.account} (bot: {bot.name})")
            import asyncio
            try:
                synced = await asyncio.wait_for(
                    sync_connectors_to_exchange_manager(bot.account, db),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout syncing connectors for {bot.account} (5s) - returning default balances")
                synced = False
            logger.info(f"✅ Sync result for {bot.account}: {synced}, connectors loaded: {list(exchange_manager.get_account(bot.account).connectors.keys()) if exchange_manager.get_account(bot.account) else 'No account'}")
            if not synced:
                logger.warning(f"No connectors synced for account {bot.account} - returning default balances")
            else:
                # Get account from exchange_manager
                account = exchange_manager.get_account(bot.account)
                if not account:
                    logger.warning(f"Account {bot.account} not found in exchange_manager - returning default balances")
                else:
                    # Determine which connector/exchange this bot uses
                    # Bot model only has 'connector' field, not 'exchange'
                    connector_name = (bot.connector or '').lower()
                    if not connector_name:
                        # Try to extract from bot name
                        bot_name_lower = (bot.name or '').lower()
                        cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
                        for kw in cex_keywords:
                            if kw in bot_name_lower:
                                connector_name = kw
                                logger.info(f"Extracted connector '{connector_name}' from bot name '{bot.name}'")
                                break
                    
                    logger.info(f"🔍 Looking for connector '{connector_name}' in account '{bot.account}'")
                    logger.info(f"🔍 Available connectors: {list(account.connectors.keys())}")
                    
                    if not connector_name:
                        logger.warning(f"Could not determine connector for bot {bot_id} (name: {bot.name}, connector: {bot.connector}) - returning default balances")
                    else:
                        # Get exchange instance from account - check both exact match and case-insensitive
                        # exchange_manager stores connectors with lowercase keys
                        exchange = account.connectors.get(connector_name)
                        if not exchange:
                            # Try case-insensitive lookup
                            logger.info(f"🔍 Direct lookup failed, trying case-insensitive match...")
                            for key, val in account.connectors.items():
                                if key.lower() == connector_name.lower():
                                    logger.info(f"✅ Found case-insensitive match: '{key}' matches '{connector_name}'")
                                    exchange = val
                                    connector_name = key  # Use actual key name
                                    break
                        
                        if exchange:
                            logger.info(f"✅ Found exchange connector '{connector_name}' in account '{bot.account}'")
                        else:
                            available_connectors = list(account.connectors.keys())
                            # If no connectors found, try to sync again with more detailed logging
                            logger.warning(f"❌ Exchange connector '{connector_name}' not found in account '{bot.account}'. Available: {available_connectors}")
                            logger.warning(f"❌ Bot connector field: '{bot.connector}', normalized: '{connector_name}'")
                            logger.warning(f"Bot details: id={bot.id}, name={bot.name}, connector={bot.connector}, client_id={bot.client_id}")
                            logger.warning(f"Attempting to re-sync connectors for account {bot.account} (client_id: {bot.client_id})...")
                            
                            # Re-sync connectors - maybe they weren't loaded yet
                            synced_retry = await sync_connectors_to_exchange_manager(bot.account, db)
                            logger.info(f"Re-sync result: {synced_retry}")
                            
                            if synced_retry:
                                account = exchange_manager.get_account(bot.account)
                                exchange = account.connectors.get(connector_name) if account else None
                                if not exchange:
                                    # Try case-insensitive again after re-sync
                                    if account:
                                        for key, val in account.connectors.items():
                                            if key.lower() == connector_name.lower():
                                                exchange = val
                                                connector_name = key
                                                logger.info(f"Found connector via case-insensitive match after re-sync: {key}")
                                                break
                            
                            if not exchange:
                                available_connectors_after = list(account.connectors.keys()) if account else []
                                logger.error(f"Exchange '{connector_name}' still not found after re-sync. Available: {available_connectors_after}. Bot connector: '{bot.connector}', Client ID: {bot.client_id} - returning default balances")
                        
                        if exchange:
                            # Fetch balance
                            try:
                                logger.info(f"🔍 Fetching balance from {connector_name} for pair {pair}")
                                
                                # Log exchange instance details before API call
                                exchange_type = type(exchange).__name__
                                logger.info(f"   Exchange instance: {exchange_type}")
                                if hasattr(exchange, 'apiKey'):
                                    api_key_preview = f"{exchange.apiKey[:4]}...{exchange.apiKey[-4:]}" if exchange.apiKey else "None"
                                    logger.info(f"   Exchange apiKey: {api_key_preview}")
                                if hasattr(exchange, 'secret'):
                                    secret_preview = f"{exchange.secret[:4]}...{exchange.secret[-4:]}" if exchange.secret else "None"
                                    logger.info(f"   Exchange secret: {secret_preview}")
                                if hasattr(exchange, 'uid'):
                                    logger.info(f"   Exchange uid: {exchange.uid}")
                                if hasattr(exchange, 'options'):
                                    logger.info(f"   Exchange options: {exchange.options}")
                                
                                # Ensure markets are loaded for ccxt exchanges (not needed for Coinstore custom adapter)
                                # This is REQUIRED before fetching balance - ccxt needs markets loaded
                                if connector_name.lower() != 'coinstore' and hasattr(exchange, 'load_markets'):
                                    try:
                                        if not hasattr(exchange, 'markets') or not exchange.markets:
                                            logger.info(f"   Markets not loaded, loading now...")
                                            # Add timeout to prevent hanging
                                            import asyncio
                                            await asyncio.wait_for(exchange.load_markets(), timeout=30.0)
                                            logger.info(f"   ✅ Markets loaded: {len(exchange.markets) if exchange.markets else 0} markets")
                                        else:
                                            logger.debug(f"   Markets already loaded: {len(exchange.markets)} markets")
                                    except asyncio.TimeoutError:
                                        logger.error(f"   ❌ Timeout loading markets for {connector_name} (30s)")
                                        raise Exception(f"Timeout loading markets for {connector_name}")
                                    except Exception as market_err:
                                        logger.warning(f"   ⚠️  Could not load markets: {market_err}")
                                        # Don't fail completely - might still work
                                
                                # Wrap in try-except to handle ccxt AttributeError bug and timeouts
                                try:
                                    # Fetch balance with timeout to prevent dashboard hanging
                                    import asyncio
                                    
                                    logger.info(f"💰 Fetching balance from {connector_name}...")
                                    if connector_name.lower() == 'bitmart':
                                        # BitMart has defaultType='spot' in options, so try without parameter first
                                        try:
                                            logger.info(f"   Calling: exchange.fetch_balance() for BitMart (using defaultType from options)")
                                            balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                        except Exception as e:
                                            # If that fails, try with explicit type parameter
                                            logger.warning(f"   First attempt failed: {e}, trying with explicit type parameter...")
                                            balance = await asyncio.wait_for(exchange.fetch_balance({'type': 'spot'}), timeout=15.0)
                                    elif connector_name.lower() == 'coinstore':
                                        logger.info(f"   Calling: exchange.fetch_balance() for Coinstore")
                                        balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                    else:
                                        logger.info(f"   Calling: exchange.fetch_balance() for {connector_name}")
                                        balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                    
                                    if balance:
                                        free_count = len(balance.get('free', {}))
                                        logger.info(f"✅ Balance fetched: {free_count} currencies")
                                        # Log sample balances
                                        sample_balances = []
                                        for currency, amount in balance.get('free', {}).items():
                                            if float(amount or 0) > 0:
                                                sample_balances.append(f"{currency}: {amount}")
                                        if sample_balances:
                                            logger.info(f"   Sample balances: {', '.join(sample_balances[:5])}")
                                    else:
                                        logger.warning(f"⚠️  Balance response is None or empty")
                                    
                                    logger.info(f"✅ Balance fetch successful for {connector_name}")
                                except asyncio.TimeoutError:
                                    logger.error(f"   ❌ Timeout fetching balance for {connector_name} (15s) - returning default values")
                                    balance = None
                                except AttributeError as attr_err:
                                    # BitMart ccxt bug: error message is None, causes AttributeError
                                    if "'NoneType' object has no attribute 'lower'" in str(attr_err):
                                        logger.warning(f"⚠️  BitMart ccxt error handler bug (None message). Balance fetch failed silently.")
                                        # Don't expose error to client - just return default values
                                        balance = None
                                    else:
                                        logger.error(f"❌ AttributeError fetching balance: {attr_err}", exc_info=True)
                                        balance = None
                                except ValueError as val_err:
                                    # Handle format specifier errors (ccxt error message formatting issues)
                                    if "format specifier" in str(val_err).lower():
                                        logger.warning(f"⚠️  ccxt error formatting issue: {val_err} - trying without type parameter...")
                                        try:
                                            # Try without type parameter - BitMart might have it in options already
                                            balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                            logger.info(f"✅ Balance fetch succeeded without type parameter")
                                        except Exception as retry_err:
                                            logger.error(f"❌ Retry also failed: {retry_err}")
                                            balance = None
                                    else:
                                        logger.error(f"❌ ValueError fetching balance: {val_err}", exc_info=True)
                                        balance = None
                                except Exception as balance_fetch_err:
                                    logger.error(f"❌ Exception fetching balance from {connector_name}: {balance_fetch_err}", exc_info=True)
                                    balance = None
                                
                                # Extract balances - check if balance is None first
                                if balance is None:
                                    logger.warning(f"Balance is None for bot {bot_id} - returning default values")
                                    # Default values are already 0, so no need to set them again
                                else:
                                    logger.info(f"Balance response keys: {list(balance.keys()) if balance else 'None'}")
                                    logger.info(f"Looking for base={base}, quote={quote} in balance")
                                    
                                    # Extract available (free) and locked (used) balances
                                    # Handle both dict format and direct access
                                    # SIMPLE: balance.get("free", {}).get(currency, 0) - exactly like Hummingbot
                                    base_available = float(balance.get("free", {}).get(base, 0) or 0)
                                    quote_available = float(balance.get("free", {}).get(quote, 0) or 0)
                                    base_locked = float(balance.get("used", {}).get(base, 0) or 0)
                                    quote_locked = float(balance.get("used", {}).get(quote, 0) or 0)
                                    
                                    logger.info(f"Extracted balances: {base}={base_available} available, {base_locked} locked; {quote}={quote_available} available, {quote_locked} locked")
                                    
                                    result["available"] = {
                                        base: round(base_available, 4),
                                        quote: round(quote_available, 2)
                                    }
                                    result["locked"] = {
                                        base: round(base_locked, 4),
                                        quote: round(quote_locked, 2)
                                    }
                                
                                # Fetch open orders to get more accurate locked balance
                                try:
                                    open_orders = await exchange.fetch_open_orders(pair)
                                    locked_base = sum(float(o.get('amount', 0) or 0) for o in open_orders if o.get('side', '').lower() == 'sell')
                                    locked_quote = sum(float(o.get('cost', 0) or (o.get('amount', 0) or 0) * (o.get('price', 0) or 0)) for o in open_orders if o.get('side', '').lower() == 'buy')
                                    
                                    # Use open orders if more accurate
                                    if locked_base > 0 or locked_quote > 0:
                                        result["locked"][base] = round(locked_base, 4)
                                        result["locked"][quote] = round(locked_quote, 2)
                                except Exception as e:
                                    logger.debug(f"Could not fetch open orders: {e}")
                                    # Use balance.used as fallback (already set above)
                            except AttributeError as attr_err:
                                # Handle ccxt AttributeError bug when error message is None
                                if "'NoneType' object has no attribute 'lower'" in str(attr_err):
                                    logger.error(f"BitMart ccxt AttributeError bug: {attr_err} - returning default balances")
                                    # Don't expose error - just return default values (already set to 0)
                                else:
                                    logger.error(f"AttributeError fetching balance: {attr_err}", exc_info=True)
                                    # Don't expose error - return default values
                            except Exception as e:
                                error_msg = str(e)
                                logger.error(f"Error fetching balance from {connector_name} for bot {bot_id}: {e}", exc_info=True)
                                
                                # Log exchange instance details for debugging
                                if exchange:
                                    logger.error(f"   Exchange type: {type(exchange).__name__}")
                                    if hasattr(exchange, 'apiKey'):
                                        api_key_preview = f"{exchange.apiKey[:4]}...{exchange.apiKey[-4:]}" if exchange.apiKey else "None"
                                        logger.error(f"   Exchange apiKey: {api_key_preview}")
                                    if hasattr(exchange, 'secret'):
                                        secret_preview = f"{exchange.secret[:4]}...{exchange.secret[-4:]}" if exchange.secret else "None"
                                        logger.error(f"   Exchange secret: {secret_preview}")
                                
                                # Log error but don't expose to client - return default values (already 0)
                                # Client will see 0 balances instead of error message
                
        except Exception as e:
            logger.error(f"Error fetching balance for bot {bot_id}: {e}", exc_info=True)
            # Don't expose error - return default values (already 0)
    
    # Calculate Volume and P&L based on bot type (always calculate, even if balance fetch failed)
    try:
        # Get trades from trade_logs (CEX) and bot_trades (DEX)
        all_trades = []
        
        # CEX trades
        try:
            trade_logs = db.execute(text("""
                SELECT side, amount, price, cost_usd, created_at
                FROM trade_logs
                WHERE bot_id = :bot_id
                ORDER BY created_at ASC
                LIMIT 1000
            """), {"bot_id": bot_id}).fetchall()
            
            for t in trade_logs:
                all_trades.append({
                    "side": t.side,
                    "amount": float(t.amount) if t.amount else 0,
                    "price": float(t.price) if t.price else 0,
                    "value_usd": float(t.cost_usd) if t.cost_usd else 0,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "timestamp": t.created_at.timestamp() if t.created_at else 0
                })
        except Exception as e:
            logger.debug(f"Could not query trade_logs: {e}")
        
        # DEX trades
        try:
            dex_trades = db.query(BotTrade).filter(
                BotTrade.bot_id == bot_id
            ).order_by(BotTrade.created_at.asc()).limit(1000).all()
            
            for t in dex_trades:
                all_trades.append({
                    "side": t.side,
                    "amount": float(t.amount) if t.amount else 0,
                    "price": float(t.price) if t.price else 0,
                    "value_usd": float(t.value_usd) if t.value_usd else 0,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "timestamp": t.created_at.timestamp() if t.created_at else 0
                })
        except Exception as e:
            logger.debug(f"Could not query bot_trades: {e}")
        
        # Calculate volume based on bot type
        if bot.bot_type == 'spread':
            # Spread Bot: Buy/sell orders done
            buy_count = sum(1 for t in all_trades if t.get("side", "").lower() == "buy")
            sell_count = sum(1 for t in all_trades if t.get("side", "").lower() == "sell")
            result["volume"] = {
                "type": "buy_sell_count",
                "buy_count": buy_count,
                "sell_count": sell_count,
                "total_trades": len(all_trades)
            }
        else:  # volume bot
            # Volume Bot: Total volume traded (USD)
            total_volume = sum(float(t.get("value_usd") or 0) for t in all_trades)
            result["volume"] = {
                "type": "volume_traded",
                "value_usd": round(total_volume, 2),
                "total_volume_usd": round(total_volume, 2),  # Alias for consistency
                "total_trades": len(all_trades)
            }
        
        # Calculate P&L from trades (FIFO method)
        try:
            positions = []  # List of (amount, price) for FIFO
            total_pnl = 0.0
            
            # Trades are already sorted by created_at ASC from query
            for trade in all_trades:
                side = trade.get("side", "").lower()
                amount = float(trade.get("amount") or 0)
                price = float(trade.get("price") or 0)
                
                if amount <= 0 or price <= 0:
                    continue
                
                if side == "buy":
                    # Add to position
                    positions.append((amount, price))
                elif side == "sell":
                    # Realize P&L using FIFO
                    remaining_sell = amount
                    while remaining_sell > 0 and positions:
                        buy_amount, buy_price = positions.pop(0)
                        sell_amount = min(remaining_sell, buy_amount)
                        pnl = (price - buy_price) * sell_amount
                        total_pnl += pnl
                        remaining_sell -= sell_amount
                        if buy_amount > sell_amount:
                            # Put remaining back
                            positions.insert(0, (buy_amount - sell_amount, buy_price))
            
            # Calculate unrealized P&L from remaining positions (if we have current price)
            unrealized_pnl = 0.0
            if positions and len(all_trades) > 0:
                # Use last trade price as current price estimate
                last_trade = all_trades[-1]
                current_price = float(last_trade.get("price") or 0)
                if current_price > 0:
                    for pos_amount, pos_price in positions:
                        unrealized_pnl += (current_price - pos_price) * pos_amount
            
            result["pnl"] = {
                "total_usd": round(total_pnl, 2),
                "unrealized_usd": round(unrealized_pnl, 2),
                "trade_count": len(all_trades)
            }
        except Exception as pnl_error:
            logger.warning(f"Failed to calculate P&L for bot {bot_id}: {pnl_error}", exc_info=True)
            result["pnl"] = {
                "total_usd": 0,
                "unrealized_usd": 0,
                "trade_count": len(all_trades)
            }
        except Exception as e:
            logger.error(f"Error calculating volume for bot {bot_id}: {e}", exc_info=True)
        result["volume"] = None
        result["pnl"] = {
            "total_usd": 0,
            "unrealized_usd": 0,
            "trade_count": 0
        }
    
    # Log final result before returning
    logger.info(f"📤 Returning balance-and-volume for bot {bot_id}: available={result.get('available')}, locked={result.get('locked')}, volume={result.get('volume')}, pnl={result.get('pnl', {}).get('total_usd', 0)}")
    
    return result


@router.get("/{bot_id}/stats")
async def get_bot_stats(bot_id: str, db: Session = Depends(get_db)):
    """
    Get bot statistics for dashboard display.
    Returns: available funds, locked funds, 24h volume, and 24h trade counts.
    
    IMPORTANT: This endpoint has timeouts to prevent dashboard hanging.
    If balance fetch fails or times out, returns default values (0 balances).
    """
    from sqlalchemy import text
    from datetime import datetime, timedelta, timezone
    from app.api.client_data import sync_connectors_to_exchange_manager
    from app.services.exchange import exchange_manager
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get pair to determine base/quote currencies
    pair = bot.pair or (f"{bot.base_asset}/{bot.quote_asset}" if bot.base_asset and bot.quote_asset else None)
    if not pair:
        return {
            "available": {},
            "locked": {},
            "volume_24h": 0,
            "trades_24h": {"buys": 0, "sells": 0},
            "error": "Bot missing pair configuration"
        }
    
    base, quote = pair.split("/")
    
    # Initialize result
    result = {
        "available": {base: 0, quote: 0},
        "locked": {base: 0, quote: 0},
        "volume_24h": 0,
        "trades_24h": {"buys": 0, "sells": 0}
    }
    
    # Fetch balances for CEX bots (works even when bot is stopped)
    connector_lower = (bot.connector or '').lower() if bot.connector else ''
    logger.info(f"🔍 Balance fetch request for bot {bot_id}: name={bot.name}, type={bot.bot_type}, connector={bot.connector}, account={bot.account}")
    logger.info(f"🔍 Bot details: connector_lower={connector_lower}, bot_type={bot.bot_type}, pair={pair}")
    
    if bot.bot_type in ['volume', 'spread'] or (connector_lower and connector_lower not in ['jupiter', 'solana']):
        logger.info(f"✅ Bot {bot_id} identified as CEX bot - proceeding with balance fetch")
        try:
            # Sync connectors for this account WITH TIMEOUT
            logger.info(f"🔄 Syncing connectors for account {bot.account} (bot: {bot.name})")
            import asyncio
            try:
                synced = await asyncio.wait_for(
                    sync_connectors_to_exchange_manager(bot.account, db),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout syncing connectors for {bot.account} (5s) - returning default balances")
                synced = False
            logger.info(f"✅ Sync result for {bot.account}: {synced}, connectors loaded: {list(exchange_manager.get_account(bot.account).connectors.keys()) if exchange_manager.get_account(bot.account) else 'No account'}")
            if synced:
                account = exchange_manager.get_account(bot.account)
                if account:
                    # Determine connector name
                    connector_name = (bot.connector or '').lower()
                    if not connector_name:
                        bot_name_lower = (bot.name or '').lower()
                        cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
                        for kw in cex_keywords:
                            if kw in bot_name_lower:
                                connector_name = kw
                                break
                    
                    logger.info(f"🔍 Looking for connector '{connector_name}' in account '{bot.account}'")
                    logger.info(f"🔍 Available connectors: {list(account.connectors.keys())}")
                    
                    if connector_name:
                        exchange = account.connectors.get(connector_name)
                        if not exchange:
                            # Try case-insensitive lookup
                            logger.info(f"🔍 Direct lookup failed, trying case-insensitive match...")
                            for key, val in account.connectors.items():
                                if key.lower() == connector_name.lower():
                                    logger.info(f"✅ Found case-insensitive match: '{key}' matches '{connector_name}'")
                                    exchange = val
                                    connector_name = key  # Use the actual key name
                                    break
                        
                        if exchange:
                            logger.info(f"✅ Found exchange connector '{connector_name}' in account '{bot.account}'")
                        else:
                            available_connectors = list(account.connectors.keys())
                            logger.warning(f"❌ Exchange connector '{connector_name}' not found in account '{bot.account}'. Available: {available_connectors}")
                            logger.warning(f"❌ Bot connector field: '{bot.connector}', normalized: '{connector_name}'")
                        
                        if exchange:
                            try:
                                # Log exchange type and API key status (masked)
                                exchange_type = type(exchange).__name__
                                api_key_preview = "***"
                                if hasattr(exchange, 'apiKey') and exchange.apiKey:
                                    api_key_preview = f"{exchange.apiKey[:4]}...{exchange.apiKey[-4:]}" if len(exchange.apiKey) > 8 else "***"
                                elif hasattr(exchange, 'connector') and hasattr(exchange.connector, 'api_key'):
                                    api_key_preview = f"{exchange.connector.api_key[:4]}...{exchange.connector.api_key[-4:]}" if len(exchange.connector.api_key) > 8 else "***"
                                
                                logger.info(f"🔍 Fetching balance for {connector_name} bot {bot_id}: exchange_type={exchange_type}, api_key={api_key_preview}")
                                
                                # Fetch balance (works regardless of bot status)
                                # Log exchange instance details before API call
                                exchange_type = type(exchange).__name__
                                api_key_preview = f"{exchange.apiKey[:4]}...{exchange.apiKey[-4:]}" if hasattr(exchange, 'apiKey') and exchange.apiKey else "None"
                                logger.info(f"🔍 Fetching balance for {connector_name} bot {bot_id}: exchange_type={exchange_type}, api_key={api_key_preview}")
                                
                                # SIMPLE: Just like Hummingbot - load markets, fetch balance, done
                                import asyncio
                                
                                try:
                                    # Load markets if needed (ccxt requirement)
                                    if connector_name.lower() != 'coinstore' and hasattr(exchange, 'load_markets'):
                                        if not hasattr(exchange, 'markets') or not exchange.markets:
                                            logger.info(f"📊 Loading markets for {connector_name}...")
                                            await asyncio.wait_for(exchange.load_markets(), timeout=10.0)
                                            logger.info(f"✅ Markets loaded: {len(exchange.markets) if hasattr(exchange, 'markets') else 0} pairs")
                                    
                                    # Fetch balance - BitMart has defaultType='spot' in options, try without parameter first
                                    logger.info(f"💰 Fetching balance from {connector_name}...")
                                    if connector_name.lower() == 'bitmart':
                                        try:
                                            logger.info(f"   Calling: exchange.fetch_balance() for BitMart (using defaultType from options)")
                                            balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                        except Exception as e:
                                            # If that fails, try with explicit type parameter
                                            logger.warning(f"   First attempt failed: {e}, trying with explicit type parameter...")
                                            balance = await asyncio.wait_for(exchange.fetch_balance({'type': 'spot'}), timeout=15.0)
                                    else:
                                        balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                    
                                    if balance:
                                        free_count = len(balance.get('free', {}))
                                        used_count = len(balance.get('used', {}))
                                        total_count = len(balance.get('total', {}))
                                        logger.info(f"✅ Balance fetched: {free_count} free currencies, {used_count} used, {total_count} total")
                                        
                                        # Log sample balances (non-zero only)
                                        sample_balances = []
                                        for currency, amount in balance.get('free', {}).items():
                                            if float(amount or 0) > 0:
                                                sample_balances.append(f"{currency}: {amount}")
                                        if sample_balances:
                                            logger.info(f"   Sample balances: {', '.join(sample_balances[:5])}")
                                    else:
                                        logger.warning(f"⚠️  Balance response is None or empty")
                                        balance = None
                                except asyncio.TimeoutError:
                                    logger.error(f"❌ Timeout fetching balance from {connector_name} (15s) - exchange may be slow or unreachable")
                                    balance = None
                                except AttributeError as attr_err:
                                    # BitMart ccxt bug: error message is None, causes AttributeError
                                    if "'NoneType' object has no attribute 'lower'" in str(attr_err):
                                        logger.warning(f"⚠️  BitMart ccxt AttributeError bug (None message) - trying without type parameter...")
                                        try:
                                            # Try without type parameter - BitMart might have it in options already
                                            balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                            logger.info(f"✅ Retry without type parameter succeeded")
                                        except Exception as retry_err:
                                            logger.error(f"❌ Retry also failed: {retry_err}")
                                            balance = None
                                    else:
                                        logger.error(f"❌ AttributeError fetching balance: {attr_err}", exc_info=True)
                                        balance = None
                                except ValueError as val_err:
                                    # Handle format specifier errors (ccxt error message formatting issues)
                                    if "format specifier" in str(val_err).lower():
                                        logger.warning(f"⚠️  ccxt error formatting issue: {val_err} - trying without type parameter...")
                                        try:
                                            # Try without type parameter - BitMart might have it in options already
                                            balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=15.0)
                                            logger.info(f"✅ Balance fetch succeeded without type parameter")
                                        except Exception as retry_err:
                                            logger.error(f"❌ Retry also failed: {retry_err}")
                                            balance = None
                                    else:
                                        logger.error(f"❌ ValueError fetching balance: {val_err}", exc_info=True)
                                        balance = None
                                except Exception as balance_fetch_err:
                                    logger.error(f"❌ Exception fetching balance from {connector_name}: {balance_fetch_err}", exc_info=True)
                                    balance = None
                                
                                # Initialize balance variables to 0 (default values)
                                base_available = 0.0
                                quote_available = 0.0
                                base_locked = 0.0
                                quote_locked = 0.0
                                
                                # Extract balances - SIMPLE like Hummingbot: balance['free'][currency]
                                if balance is None:
                                    logger.warning(f"Balance is None for bot {bot_id} - returning default values")
                                else:
                                    # Hummingbot pattern: balance.get("free", {}).get(currency, 0)
                                    base_available = float(balance.get("free", {}).get(base, 0) or 0)
                                    quote_available = float(balance.get("free", {}).get(quote, 0) or 0)
                                    base_locked = float(balance.get("used", {}).get(base, 0) or 0)
                                    quote_locked = float(balance.get("used", {}).get(quote, 0) or 0)
                                    
                                    logger.info(f"✅ Balance: {base}={base_available} free, {base_locked} locked; {quote}={quote_available} free, {quote_locked} locked")
                                
                                # Set result balances (use initialized/default values)
                                result["available"] = {
                                    base: round(base_available, 4),
                                    quote: round(quote_available, 2)
                                }
                                result["locked"] = {
                                    base: round(base_locked, 4),
                                    quote: round(quote_locked, 2)
                                }
                            except Exception as balance_error:
                                error_msg = str(balance_error)
                                logger.error(f"Error fetching balance for bot {bot_id}: {balance_error}", exc_info=True)
                                # Log error but don't expose to client - return default values (already 0)
                                # Client will see 0 balances instead of error message
                        else:
                            logger.warning(f"Exchange connector '{connector_name}' not found - returning default balances")
                    else:
                        logger.warning(f"Could not determine exchange from bot name or connector - returning default balances")
                else:
                    logger.warning(f"Account not found in exchange manager - returning default balances")
            else:
                logger.warning(f"Failed to sync exchange connectors - returning default balances")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in balance fetch for bot {bot_id}: {e}")
            # Don't expose error - return default values (already 0)
    
    # Calculate 24h volume and trade counts
    try:
        # Get trades from last 24 hours
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Query trade_logs table (CEX bots)
        trade_logs = db.execute(text("""
            SELECT side, amount, price, cost_usd
            FROM trade_logs
            WHERE bot_id = :bot_id
              AND created_at >= :since
        """), {"bot_id": bot_id, "since": twenty_four_hours_ago}).fetchall()
        
        # Query bot_trades table (DEX bots)
        bot_trades = db.query(BotTrade).filter(
            BotTrade.bot_id == bot_id,
            BotTrade.created_at >= twenty_four_hours_ago
        ).all()
        
        # Calculate volume from trade_logs (CEX)
        volume_24h = 0
        buys_24h = 0
        sells_24h = 0
        
        for trade in trade_logs:
            # Volume is cost_usd if available, otherwise price * amount
            if trade.cost_usd:
                volume_24h += float(trade.cost_usd)
            elif trade.price and trade.amount:
                volume_24h += float(trade.price) * float(trade.amount)
            
            if trade.side and trade.side.lower() == 'buy':
                buys_24h += 1
            elif trade.side and trade.side.lower() == 'sell':
                sells_24h += 1
        
        # Count trades from bot_trades (DEX)
        for trade in bot_trades:
            if trade.value_usd:
                volume_24h += float(trade.value_usd)
            elif trade.price and trade.amount:
                volume_24h += float(trade.price) * float(trade.amount)
            
            if trade.side and trade.side.lower() == 'buy':
                buys_24h += 1
            elif trade.side and trade.side.lower() == 'sell':
                sells_24h += 1
        
        result["volume_24h"] = round(volume_24h, 2)
        result["trades_24h"] = {
            "buys": buys_24h,
            "sells": sells_24h
        }
    except Exception as e:
        logger.error(f"Error calculating 24h stats for bot {bot_id}: {e}")
        # Return defaults if query fails
    
    return result


@router.get("/test-balance-direct")
async def test_balance_direct(
    account: str = Query(..., description="Account identifier"),
    exchange_name: str = Query("bitmart", description="Exchange name"),
    db: Session = Depends(get_db)
):
    """
    DIRECT TEST: Fetch balance exactly like Hummingbot does.
    Use this to verify balance fetching works independently of bot logic.
    
    This creates exchange directly, loads markets, fetches balance - 3 lines like Hummingbot.
    """
    import ccxt.async_support as ccxt
    from app.api.client_data import sync_connectors_to_exchange_manager
    from app.services.exchange import exchange_manager
    from app.cex_volume_bot import decrypt_credential
    from app.database import Client
    from sqlalchemy import text
    
    try:
        # Get client
        client = db.query(Client).filter(Client.account_identifier == account).first()
        if not client:
            return {"error": f"Client not found for account: {account}"}
        
        # Try to get API keys from exchange_credentials
        creds = db.execute(text("""
            SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
            FROM exchange_credentials
            WHERE client_id = :client_id AND exchange = :exchange
        """), {"client_id": client.id, "exchange": exchange_name}).first()
        
        if not creds:
            return {"error": f"No credentials found for {exchange_name}"}
        
        # Decrypt keys
        api_key = decrypt_credential(creds.api_key_encrypted)
        api_secret = decrypt_credential(creds.api_secret_encrypted)
        memo = decrypt_credential(creds.passphrase_encrypted) if creds.passphrase_encrypted else None
        
        # Create exchange EXACTLY like Hummingbot
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        }
        if memo:
            config['uid'] = memo
        if exchange_name.lower() == 'bitmart':
            config['options'] = {'defaultType': 'spot'}
        
        exchange = ccxt.bitmart(config) if exchange_name.lower() == 'bitmart' else getattr(ccxt, exchange_name.lower())(config)
        
        # Load markets
        await exchange.load_markets()
        
        # Fetch balance
        balance = await exchange.fetch_balance()
        
        # Extract balances
        free_balances = {}
        for currency, amount in balance.get("free", {}).items():
            if float(amount or 0) > 0:
                free_balances[currency] = float(amount)
        
        await exchange.close()
        
        return {
            "success": True,
            "exchange": exchange_name,
            "account": account,
            "balance": {
                "free": free_balances,
                "total_currencies": len(balance.get("free", {})),
                "non_zero_currencies": len(free_balances)
            },
            "raw_balance_keys": list(balance.keys()),
            "sample_free_keys": list(balance.get("free", {}).keys())[:10]
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/{bot_id}/balance-debug")
async def debug_bot_balance(bot_id: str, db: Session = Depends(get_db)):
    """
    Diagnostic endpoint to debug balance fetching issues.
    Returns detailed information about connectors, accounts, and balance fetching.
    Use this to identify why balance is not showing.
    """
    from app.api.client_data import sync_connectors_to_exchange_manager
    from app.services.exchange import exchange_manager
    from sqlalchemy import text
    from app.cex_volume_bot import decrypt_credential
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get client
    client = db.query(Client).filter(Client.id == bot.client_id).first()
    
    # Get connectors from database
    connectors = db.query(Connector).filter(Connector.client_id == bot.client_id).all()
    
    # Check exchange_credentials table
    exchange_creds = []
    if client:
        creds_result = db.execute(text("""
            SELECT exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted
            FROM exchange_credentials
            WHERE client_id = :client_id
        """), {"client_id": client.id}).fetchall()
        
        for cred in creds_result:
            try:
                api_key = decrypt_credential(cred.api_key_encrypted) if cred.api_key_encrypted else None
                api_secret = decrypt_credential(cred.api_secret_encrypted) if cred.api_secret_encrypted else None
                exchange_creds.append({
                    "exchange": cred.exchange,
                    "exchange_lower": cred.exchange.lower() if cred.exchange else None,
                    "has_api_key": bool(api_key),
                    "has_api_secret": bool(api_secret),
                    "has_passphrase": bool(cred.passphrase_encrypted)
                })
            except Exception as e:
                exchange_creds.append({
                    "exchange": cred.exchange,
                    "error": str(e)
                })
    
    # Try to sync
    synced = await sync_connectors_to_exchange_manager(bot.account, db)
    account = exchange_manager.get_account(bot.account) if synced else None
    
    # Determine expected connector name
    bot_connector_lower = (bot.connector or '').lower()
    if not bot_connector_lower:
        bot_name_lower = (bot.name or '').lower()
        cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gateio', 'mexc', 'bybit', 'okx']
        for kw in cex_keywords:
            if kw in bot_name_lower:
                bot_connector_lower = kw
                break
    
    # Check connector match
    connector_match = False
    matched_connector_key = None
    if account:
        for key in account.connectors.keys():
            if key.lower() == bot_connector_lower:
                connector_match = True
                matched_connector_key = key
                break
    
    # Try to actually fetch balance if connector found
    balance_test = None
    if connector_match and account:
        exchange = account.connectors[matched_connector_key]
        try:
            import asyncio
            if bot_connector_lower == 'bitmart':
                balance = await asyncio.wait_for(exchange.fetch_balance({'type': 'spot'}), timeout=10.0)
            else:
                balance = await asyncio.wait_for(exchange.fetch_balance(), timeout=10.0)
            
            if balance:
                base, quote = (bot.pair or "SHARP/USDT").split("/")
                base_available = float(balance.get("free", {}).get(base, 0) or 0)
                quote_available = float(balance.get("free", {}).get(quote, 0) or 0)
                balance_test = {
                    "success": True,
                    "base_available": base_available,
                    "quote_available": quote_available,
                    "total_currencies": len(balance.get("free", {})),
                    "sample_currencies": list(balance.get("free", {}).keys())[:5]
                }
        except Exception as e:
            balance_test = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    return {
        "bot": {
            "id": bot.id,
            "name": bot.name,
            "account": bot.account,
            "connector": bot.connector,
            "connector_lower": bot_connector_lower,
            "bot_type": bot.bot_type,
            "pair": bot.pair,
            "client_id": bot.client_id
        },
        "client": {
            "id": client.id if client else None,
            "name": client.name if client else None,
            "account_identifier": client.account_identifier if client else None
        },
        "connectors_in_db": [
            {
                "id": c.id,
                "name": c.name,
                "name_lower": c.name.lower(),
                "has_api_key": bool(c.api_key),
                "has_api_secret": bool(c.api_secret),
                "has_memo": bool(c.memo)
            } for c in connectors
        ],
        "exchange_credentials_in_db": exchange_creds,
        "sync_result": synced,
        "account_in_manager": account is not None,
        "connectors_in_manager": list(account.connectors.keys()) if account else [],
        "bot_connector_lower": bot_connector_lower,
        "connector_match": connector_match,
        "matched_connector_key": matched_connector_key,
        "balance_test": balance_test,
        "diagnosis": {
            "has_client": client is not None,
            "has_connectors_in_db": len(connectors) > 0,
            "has_exchange_credentials": len(exchange_creds) > 0,
            "sync_succeeded": synced,
            "account_exists": account is not None,
            "connector_found": connector_match,
            "balance_fetch_works": balance_test.get("success") if balance_test else None
        }
    }


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
        logger.error(f"Error adding wallet to bot {bot_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding wallet: {str(e)}")


@router.post("/{bot_id}/add-exchange-credentials")
def add_exchange_credentials_to_bot(
    bot_id: str,
    api_key: str = Query(..., description="Exchange API key"),
    api_secret: str = Query(..., description="Exchange API secret"),
    passphrase: Optional[str] = Query(None, description="Exchange passphrase/memo (for BitMart, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Add exchange API credentials for an existing CEX volume bot.
    This fixes bots that show "Missing API keys" error.
    
    The credentials are saved to exchange_credentials table for the bot's client.
    """
    from sqlalchemy import text
    from app.cex_volume_bot import encrypt_credential
    from datetime import datetime, timezone
    
    try:
        # Get bot
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
        
        # Determine exchange from bot
        exchange = None
        if bot.connector:
            exchange = bot.connector.lower()
        elif bot.name:
            bot_name_lower = bot.name.lower()
            cex_keywords = ['bitmart', 'coinstore', 'binance', 'kucoin', 'gate', 'gateio', 'mexc', 'bybit', 
                           'okx', 'kraken', 'coinbase', 'dydx', 'hyperliquid', 'htx', 'huobi']
            for kw in cex_keywords:
                if kw in bot_name_lower:
                    exchange = kw
                    break
        
        if not exchange:
            raise HTTPException(
                status_code=400,
                detail=f"Could not determine exchange for bot {bot_id}. Please specify exchange name."
            )
        
        # Encrypt credentials
        api_key_enc = encrypt_credential(api_key.strip())
        api_secret_enc = encrypt_credential(api_secret.strip())
        passphrase_enc = encrypt_credential(passphrase.strip()) if passphrase else None
        
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
            "client_id": bot.client_id,
            "exchange": exchange,
            "api_key": api_key_enc,
            "api_secret": api_secret_enc,
            "passphrase": passphrase_enc,
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Clear bot error status
        bot.health_status = None
        bot.health_message = None
        bot.error = None
        
        db.commit()
        
        logger.info(f"✅ Added exchange credentials for bot {bot_id} (exchange: {exchange}, client_id: {bot.client_id})")
        
        return {
            "success": True,
            "message": f"Exchange credentials added for {exchange}",
            "bot_id": bot_id,
            "exchange": exchange,
            "client_id": bot.client_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding exchange credentials to bot {bot_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")(f"Failed to add wallet to bot {bot_id}: {e}")
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
def delete_bot(
    bot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address")
):
    """
    Delete a bot.
    Clients can delete their own bots. Admins can delete any bot.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Authorization check - clients can delete their own bots
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
        # Token auth (admin) - allow
        pass
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Stop bot first if running
    if bot.status == "running":
        try:
            # For Solana/CEX bots, stop via bot runner
            if bot.bot_type in ['volume', 'spread']:
                import asyncio
                from app.bot_runner import bot_runner
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, schedule it
                        asyncio.create_task(bot_runner.stop_bot(bot_id))
                    else:
                        asyncio.run(bot_runner.stop_bot(bot_id))
                except Exception as e:
                    logger.warning(f"Failed to stop bot before deletion: {e}")
            # hummingbot.stop_bot(bot.instance_name)  # For Hummingbot bots
        except Exception as e:
            logger.warning(f"Failed to stop bot before deletion: {e}")

    db.delete(bot)
    db.commit()
    
    logger.info(f"Bot {bot_id} deleted by client")

    return {"status": "deleted", "bot_id": bot_id}
