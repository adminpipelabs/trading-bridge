"""
Trading Bridge - Main FastAPI Application
Connects Pipe Labs Dashboard to cryptocurrency exchanges via ccxt
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import asyncio
import requests
from app.jupiter_routes import router as jupiter_router
from app.solana_routes import router as solana_router

from app.core.config import settings
from app.api import accounts, connectors, market, orders, portfolio, client_data
from app.bot_routes import router as bot_router
from app.clients_routes import router as client_router
from app.auth_routes import router as auth_router
from app.exchange_routes import router as exchange_router
from app.health_routes import router as health_router
from app.client_setup_routes import router as client_setup_router
from app.admin_routes import router as admin_router
from app.cex_credential_routes import router as cex_credential_router
from app.database import init_db
from app.services.exchange import exchange_manager
from app.cex_volume_bot import extract_proxy_url_from_quotaguard_info
import os
import logging
import json
from datetime import datetime
import asyncpg
import hashlib
import hmac
import math
import time
import requests
from cryptography.fernet import Fernet


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'bot_id'):
            log_obj['bot_id'] = record.bot_id
        if hasattr(record, 'trade_id'):
            log_obj['trade_id'] = record.trade_id
        if hasattr(record, 'amount'):
            log_obj['amount'] = record.amount
        if hasattr(record, 'side'):
            log_obj['side'] = record.side
        if hasattr(record, 'signature'):
            log_obj['signature'] = record.signature
        if hasattr(record, 'error'):
            log_obj['error'] = record.error
            
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logging():
    """Configure structured JSON logging."""
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add JSON handler
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Store Railway IP at startup for easy access via /railway-ip endpoint
_railway_ip = None


# Store Railway IP globally so it can be accessed via health endpoint
railway_outbound_ip = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup - FAIL FAST if database init fails."""
    global railway_outbound_ip
    
    logger.info("=" * 80)
    logger.info("STARTING DATABASE INITIALIZATION")
    logger.info("=" * 80)
    
    # Set HTTP_PROXY and HTTPS_PROXY from QUOTAGUARDSTATIC_URL for aiohttp (ccxt async)
    # This ensures aiohttp automatically uses the proxy for all requests
    quotaguard_url = os.getenv("QUOTAGUARDSTATIC_URL")
    if quotaguard_url:
        # Extract proxy URL if it's in QuotaGuard connection info format
        proxy_url = extract_proxy_url_from_quotaguard_info(quotaguard_url) or quotaguard_url
        
        # Normalize proxy URL: HTTP proxies should use http:// even for HTTPS targets
        # This fixes 407 Proxy Authentication Required errors
        if proxy_url.startswith('https://'):
            proxy_url = 'http://' + proxy_url[8:]  # Replace https:// with http://
            logger.debug("Normalized proxy URL: changed https:// to http://")
        
        # Set environment variables for aiohttp to pick up automatically
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        logger.info("=" * 80)
        logger.info("✅ Set HTTP_PROXY and HTTPS_PROXY for aiohttp (ccxt async)")
        logger.info(f"   Proxy URL: {proxy_url.split('@')[0] if '@' in proxy_url else proxy_url[:30]}...")
        logger.info("=" * 80)
        print("=" * 80)
        print("✅ Set HTTP_PROXY and HTTPS_PROXY for aiohttp (ccxt async)")
        print(f"   Proxy URL: {proxy_url.split('@')[0] if '@' in proxy_url else proxy_url[:30]}...")
        print("=" * 80)
    else:
        logger.warning("⚠️  QUOTAGUARDSTATIC_URL not set - proxy will not be used by aiohttp")
    
    # Log Railway outbound IP for BitMart whitelisting - MUST BE FIRST THING
    # Use print() so it's visible in Railway logs immediately
    print("=" * 80)
    print("FETCHING RAILWAY OUTBOUND IP FOR BITMART WHITELISTING...")
    print("=" * 80)
    global _railway_ip
    try:
        railway_outbound_ip = requests.get('https://api.ipify.org', timeout=5).text
        _railway_ip = railway_outbound_ip  # Store globally for /railway-ip endpoint
        print("=" * 80)
        print(f"🌐 Railway outbound IP: {railway_outbound_ip}")
        print("=" * 80)
        print("⚠️  IMPORTANT: Add this IP to BitMart API key whitelist!")
        print(f"📡 Or visit: https://trading-bridge-production.up.railway.app/railway-ip")
        print("=" * 80)
        logger.info("=" * 80)
        logger.info(f"🌐 RAILWAY OUTBOUND IP: {railway_outbound_ip}")
        logger.info("=" * 80)
        logger.info("⚠️  IMPORTANT: Add this IP to BitMart API key whitelist!")
        logger.info(f"📡 Or visit: https://trading-bridge-production.up.railway.app/railway-ip")
        logger.info("=" * 80)
    except Exception as e:
        print(f"❌ Could not fetch Railway IP: {e}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        logger.warning(f"Could not fetch Railway IP: {e}", exc_info=True)
    
    # CRITICAL: Database must be initialized before app starts serving requests
    # If init fails, we should fail fast rather than serve broken endpoints
    try:
        init_db()
        logger.info("=" * 80)
        logger.info("✅ DATABASE INITIALIZATION COMPLETE - APP READY")
        logger.info("=" * 80)
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ CRITICAL: DATABASE INITIALIZATION FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        logger.error("APP WILL CONTINUE BUT DATABASE ENDPOINTS WILL FAIL")
        logger.error("Check Railway logs above for detailed error messages")
        logger.error("=" * 80)
        # Don't raise - allow app to start so /health endpoint works
        # But database endpoints will return 503 errors
    
    # Create asyncpg connection pool for health monitor
    db_pool = None
    health_monitor = None
    try:
        database_url = os.getenv("DATABASE_URL", "")
        if database_url:
            # Convert to asyncpg-compatible URL (remove +psycopg2, ensure postgresql://)
            async_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
            async_url = async_url.replace("postgres://", "postgresql://")
            logger.info("Creating asyncpg connection pool for health monitor...")
            db_pool = await asyncpg.create_pool(
                async_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            app.state.db_pool = db_pool
            logger.info("✅ Asyncpg connection pool created")
            
            # Start bot health monitor
            from app.bot_health import BotHealthMonitor
            health_monitor = BotHealthMonitor(db_pool)
            await health_monitor.start()
            app.state.health_monitor = health_monitor
            logger.info("✅ Bot health monitor started")
        else:
            logger.warning("DATABASE_URL not set - health monitor will not start")
    except Exception as e:
        logger.error(f"Failed to start health monitor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Don't fail app startup if health monitor fails
    
    # Start CEX bot runner (in background)
    cex_runner = None
    cex_runner_task = None
    if db_pool:
        try:
            from app.cex_bot_runner import CEXBotRunner
            logger.info("Starting CEX bot runner...")
            cex_runner = CEXBotRunner(db_pool)
            cex_runner_task = asyncio.create_task(cex_runner.start())
            logger.info("✅ CEX bot runner started")
        except Exception as e:
            logger.error(f"Failed to start CEX bot runner: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Start bot runner service (in background)
    bot_runner_startup_error = None
    bot_runner_task = None
    
    async def start_bot_runner():
        nonlocal bot_runner_startup_error
        try:
            logger.info("=" * 80)
            logger.info("ATTEMPTING TO START BOT RUNNER")
            logger.info("=" * 80)
            from app.bot_runner import bot_runner
            logger.info("✅ Bot runner module imported successfully")
            await bot_runner.start()
            logger.info("✅ Bot runner started successfully")
            bot_runner_startup_error = None
        except ImportError as e:
            error_msg = f"BOT RUNNER IMPORT FAILED: {e}"
            logger.error("=" * 80)
            logger.error(f"❌ {error_msg}")
            logger.error("Check if app/bot_runner.py exists")
            logger.error("=" * 80)
            bot_runner_startup_error = error_msg
        except Exception as e:
            error_msg = f"BOT RUNNER STARTUP FAILED: {e}"
            logger.error("=" * 80)
            logger.error(f"❌ {error_msg}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
            bot_runner_startup_error = error_msg
    
    # Start bot runner in background - use create_task to run concurrently
    logger.info("Creating bot runner task...")
    try:
        # Create task and let it run in background
        bot_runner_task = asyncio.create_task(start_bot_runner())
        app.state.bot_runner_task = bot_runner_task
        app.state.bot_runner_startup_error = bot_runner_startup_error
        logger.info("✅ Bot runner task created")
        logger.info("Bot runner service starting...")
        # Give it a moment to start
        await asyncio.sleep(0.1)
    except Exception as e:
        error_msg = f"FAILED TO CREATE BOT RUNNER TASK: {e}"
        logger.error("=" * 80)
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        bot_runner_startup_error = error_msg
        app.state.bot_runner_startup_error = bot_runner_startup_error
        # Don't fail app startup if bot runner fails
    
    yield
    
    # Shutdown health monitor
    if health_monitor:
        try:
            await health_monitor.stop()
            logger.info("Bot health monitor stopped")
        except Exception as e:
            logger.warning(f"Error stopping health monitor: {e}")
    
    # Close asyncpg pool
    if db_pool:
        try:
            await db_pool.close()
            logger.info("Asyncpg connection pool closed")
        except Exception as e:
            logger.warning(f"Error closing db pool: {e}")
    
    # Shutdown CEX bot runner
    if cex_runner:
        try:
            await cex_runner.stop()
            logger.info("CEX bot runner stopped")
        except Exception as e:
            logger.warning(f"Error stopping CEX bot runner: {e}")
    
    # Shutdown bot runner
    try:
        from app.bot_runner import bot_runner
        bot_runner.shutdown_event.set()
        logger.info("Bot runner service stopped")
    except Exception as e:
        logger.warning(f"Error stopping bot runner: {e}")
    
    logger.info("Shutting down...")


# Validate production environment variables
def validate_production_config():
    """Validate required environment variables for production"""
    errors = []
    warnings = []
    
    # Check Hummingbot API URL
    # Handle Railway issue where variable names may have leading/trailing spaces
    hummingbot_url = os.getenv("HUMMINGBOT_API_URL", "") or os.getenv(" HUMMINGBOT_API_URL", "")
    if not hummingbot_url:
        errors.append("HUMMINGBOT_API_URL is not set. Required for bot management.")
    elif "localhost" in hummingbot_url or "127.0.0.1" in hummingbot_url:
        warnings.append(
            f"HUMMINGBOT_API_URL is set to localhost ({hummingbot_url}). "
            "This will not work in Railway production. Use internal service name."
        )
    
    # Check authentication
    # Handle Railway issue where variable names may have leading/trailing spaces
    api_key = os.getenv("HUMMINGBOT_API_KEY", "") or os.getenv(" HUMMINGBOT_API_KEY", "")
    password = os.getenv("HUMMINGBOT_API_PASSWORD", "") or os.getenv(" HUMMINGBOT_API_PASSWORD", "")
    if not api_key and not password:
        errors.append(
            "Hummingbot API authentication not configured. "
            "Set either HUMMINGBOT_API_KEY or HUMMINGBOT_API_PASSWORD."
        )
    
    # Log errors and warnings
    if errors:
        for error in errors:
            logger.error(f"Configuration Error: {error}")
        raise ValueError("Production configuration validation failed. See logs for details.")
    
    if warnings:
        for warning in warnings:
            logger.warning(f"Configuration Warning: {warning}")

# Validate configuration at startup
try:
    validate_production_config()
except ValueError as e:
    logger.error(f"Startup validation failed: {e}")
    # In production, fail fast. In development, allow to continue.
    if os.getenv("ENVIRONMENT") == "production":
        raise

# Bot manager initialization removed - using database persistence instead

app = FastAPI(
    title="Trading Bridge API",
    description="Bridge service connecting Pipe Labs Dashboard to cryptocurrency exchanges",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Restricted to specific origins for security
ALLOWED_ORIGINS = [
    "https://app.pipelabs.xyz",
    "https://pipelabs.xyz",
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handler to ensure CORS headers are always included
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure HTTPException responses include CORS headers"""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    # Get origin from request
    origin = request.headers.get("origin")
    if origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Rate limiting - Initialize limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(accounts.router, tags=["Accounts"])
app.include_router(connectors.router, tags=["Connectors"])
app.include_router(market.router, tags=["Market"])
app.include_router(orders.router, tags=["Orders"])
app.include_router(portfolio.router, tags=["Portfolio"])
app.include_router(client_data.router, tags=["Client Data"])
app.include_router(exchange_router, tags=["Exchange Data"])
app.include_router(jupiter_router)
app.include_router(solana_router, tags=["Solana"])
app.include_router(bot_router, tags=["Bots"])
app.include_router(client_router, tags=["Clients"])
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(client_setup_router)
app.include_router(admin_router)
app.include_router(cex_credential_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Trading Bridge",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
@limiter.limit("1000/minute")  # Health checks need frequent access
async def health_check(request: Request):
    """Main health check endpoint."""
    import os
    from app.database import engine, SessionLocal
    from datetime import datetime
    
    # Check bot runner status
    bot_runner_status = "unknown"
    bot_runner_running = False
    active_bots = 0
    try:
        from app.bot_runner import bot_runner
        active_bots = len(bot_runner.running_bots) if bot_runner else 0
        bot_runner_running = active_bots > 0
        bot_runner_status = "running" if bot_runner_running else "idle"
    except Exception as e:
        bot_runner_status = f"error: {str(e)[:50]}"
    
    database_status = "postgresql" if (os.getenv("DATABASE_URL") and engine and SessionLocal) else "unavailable"
    
    response = {
        "status": "healthy",
        "service": "Trading Bridge",
        "database": database_status,
        "bot_runner": {
            "status": bot_runner_status,
            "active_bots": active_bots,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Include Railway IP if available (for BitMart whitelisting)
    if railway_outbound_ip:
        response["railway_outbound_ip"] = railway_outbound_ip
        response["bitmart_whitelist_note"] = "Add this IP to BitMart API key whitelist"
    
    return response


@app.get("/railway-ip")
@limiter.limit("10/minute")
async def get_railway_ip(request: Request):
    """Get Railway's outbound IP address for BitMart whitelisting."""
    global _railway_ip
    if _railway_ip:
        return {
            "railway_ip": _railway_ip,
            "message": "Add this IP to BitMart API key whitelist",
            "status": "success"
        }
    else:
        # Try to fetch it now if not stored
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
            _railway_ip = ip
            return {
                "railway_ip": ip,
                "message": "Add this IP to BitMart API key whitelist",
                "status": "success"
            }
        except Exception as e:
            return {
                "railway_ip": None,
                "error": str(e),
                "status": "error",
                "message": "Could not fetch Railway IP"
            }


@app.get("/health/bot-runner")
@limiter.limit("1000/minute")  # Health checks need frequent access
async def bot_runner_health(request: Request):
    """Health check specifically for bot runner service."""
    from datetime import datetime
    from app.database import get_db_session, Bot
    
    try:
        from app.bot_runner import bot_runner
        
        if not bot_runner:
            return {
                "status": "not_initialized",
                "running_bots": 0,
                "bots": [],
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Get bot details from database
        db = get_db_session()
        bots_info = []
        try:
            for bot_id in bot_runner.running_bots.keys():
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot:
                    bots_info.append({
                        "id": str(bot_id),
                        "name": bot.name or "Unknown",
                        "status": "running",
                        "bot_type": bot.bot_type or "unknown",
                        "last_check": datetime.utcnow().isoformat(),  # Could track actual last check if we add it
                    })
        finally:
            db.close()
        
        return {
            "status": "healthy",
            "running_bots": len(bot_runner.running_bots),
            "bots": bots_info,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "running_bots": 0,
            "bots": [],
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.post("/init-db")
def initialize_database():
    """Manually create database tables - useful for fixing missing tables."""
    from app.database import Base, engine, init_db
    try:
        if not engine:
            return {
                "status": "error",
                "message": "Database engine not available. Check DATABASE_URL configuration."
            }
        
        # Use the robust init_db function
        init_db()
        return {
            "status": "success",
            "message": "Database tables created/verified successfully"
        }
    except Exception as e:
        logger.error(f"Manual database initialization failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    import os
    import base64
    # Check both with and without leading space (Railway issue)
    url_with_space = os.getenv(" HUMMINGBOT_API_URL", "")
    url_without_space = os.getenv("HUMMINGBOT_API_URL", "")
    
    username = (os.getenv("HUMMINGBOT_API_USERNAME", "") or os.getenv(" HUMMINGBOT_API_USERNAME", "") or "NOT SET").strip()
    password_raw = os.getenv("HUMMINGBOT_API_PASSWORD", "") or os.getenv(" HUMMINGBOT_API_PASSWORD", "")
    password = password_raw.strip() if password_raw else ""
    
    # Test auth header construction
    if password:
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded[:20]}..."
    else:
        auth_header = "NOT SET"
    
    # Check DATABASE_URL (mask password)
    db_url_raw = os.getenv("DATABASE_URL", "")
    if db_url_raw:
        # Mask password in URL for security
        if "@" in db_url_raw:
            parts = db_url_raw.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split("://")[-1] if "://" in parts[0] else parts[0]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    db_url_masked = db_url_raw.replace(user_pass, f"{user}:***MASKED***")
                else:
                    db_url_masked = db_url_raw
            else:
                db_url_masked = db_url_raw
        else:
            db_url_masked = db_url_raw
    else:
        db_url_masked = "NOT SET"
    
    return {
        "HUMMINGBOT_API_URL": url_without_space or url_with_space or "NOT SET",
        "HUMMINGBOT_API_USERNAME": username,
        "username_length": len(username),
        "has_password": bool(password),
        "password_length": len(password) if password else 0,
        "password_first_char": password[0] if password else "N/A",
        "auth_header_preview": auth_header,
        "all_env_keys": sorted([k for k in os.environ.keys() if "HUMMINGBOT" in k]),
        "url_with_space": url_with_space or "NOT SET",
        "url_without_space": url_without_space or "NOT SET",
        "DATABASE_URL": db_url_masked,
        "DATABASE_URL_length": len(db_url_raw),
        "DATABASE_URL_starts_with": db_url_raw[:30] if db_url_raw else "NOT SET"
    }

@app.get("/test/coinstore")
async def test_coinstore_official():
    """Test Coinstore API using official documentation example."""
    from sqlalchemy import create_engine, text
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    
    if not DATABASE_URL or not ENCRYPTION_KEY:
        return {"error": "DATABASE_URL or ENCRYPTION_KEY not set"}
    
    try:
        # Initialize Fernet
        fernet = Fernet(ENCRYPTION_KEY.encode())
        
        # Connect to database
        engine = create_engine(DATABASE_URL)
        
        # Get API credentials from database - use the specific Coinstore bot
        # Look for bot with name containing "Coinstore" or connector = 'coinstore'
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT ec.api_key_encrypted, ec.api_secret_encrypted, b.name, b.id
                FROM exchange_credentials ec
                JOIN clients cl ON cl.id = ec.client_id
                JOIN bots b ON b.account = cl.account_identifier
                WHERE ec.exchange = 'coinstore' 
                  AND b.connector = 'coinstore'
                  AND b.status = 'running'
                ORDER BY b.name LIKE '%Coinstore%' DESC, b.created_at DESC
                LIMIT 1
            """))
            
            row = result.fetchone()
            if not row:
                return {"error": "No Coinstore credentials found in database"}
            
            api_key_encrypted = row[0]
            api_secret_encrypted = row[1]
            bot_name = row[2] if len(row) > 2 else "unknown"
            bot_id = row[3] if len(row) > 3 else "unknown"
            
            # Decrypt
            api_key = fernet.decrypt(api_key_encrypted.encode()).decode()
            api_secret = fernet.decrypt(api_secret_encrypted.encode()).decode()
        
        # Official Coinstore example (exact from docs)
        url = "https://api.coinstore.com/api/spot/accountList"
        api_key_bytes = api_key.encode('utf-8')
        secret_key_bytes = api_secret.encode('utf-8')
        
        expires = int(time.time() * 1000)
        expires_key = str(math.floor(expires / 30000))
        expires_key_bytes = expires_key.encode("utf-8")
        
        # Step 1: HMAC(secret, expires_key)
        key = hmac.new(secret_key_bytes, expires_key_bytes, hashlib.sha256).hexdigest()
        key_bytes = key.encode("utf-8")
        
        # Step 2: HMAC(key, payload)
        payload_dict = {}
        payload_json = json.dumps(payload_dict)
        payload_bytes = payload_json.encode("utf-8")
        
        signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()
        
        # Headers (exact from official docs)
        headers = {
            'X-CS-APIKEY': api_key,
            'X-CS-SIGN': signature,
            'X-CS-EXPIRES': str(expires),
            'exch-language': 'en_US',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        # Make request WITHOUT proxy (test if Coinstore needs proxy)
        # Temporarily unset proxy env vars for this test
        import copy
        original_env = copy.deepcopy(os.environ)
        if 'HTTP_PROXY' in os.environ:
            del os.environ['HTTP_PROXY']
        if 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload_bytes, timeout=30)
        finally:
            # Restore original env
            os.environ.clear()
            os.environ.update(original_env)
        
        # Also test proxy status - use QuotaGuard's own test endpoint
        proxy_url = os.getenv("QUOTAGUARDSTATIC_URL", "")
        proxy_test_result = None
        if proxy_url:
            try:
                # Test proxy with QuotaGuard's own test endpoint (as shown in their dashboard)
                # Their dashboard shows: curl -x https://... -L ip.quotaguard.com
                proxy_test = requests.get("https://ip.quotaguard.com", proxies={
                    "http": proxy_url,
                    "https": proxy_url
                }, timeout=10, allow_redirects=True)
                proxy_test_result = {
                    "status": "success",
                    "ip": proxy_test.text.strip(),
                    "status_code": proxy_test.status_code,
                    "test_endpoint": "ip.quotaguard.com"
                }
            except Exception as proxy_err:
                proxy_test_result = {
                    "status": "failed",
                    "error": str(proxy_err),
                    "test_endpoint": "ip.quotaguard.com"
                }
        
        return {
            "status_code": response.status_code,
            "response_text": response.text,
            "success": response.status_code == 200,
            "error_1401": response.status_code == 1401,
            "api_key_preview": f"{api_key[:10]}...{api_key[-5:]}",
            "api_key_full": api_key,  # Include full key to verify it's correct
            "signature_preview": f"{signature[:20]}...{signature[-10:]}",
            "bot_name": bot_name,
            "bot_id": bot_id,
            "tested_without_proxy": True,
            "proxy_test": proxy_test_result,
            "quotaguard_url_set": bool(proxy_url),
            "quotaguard_url_preview": proxy_url.split('@')[0] if proxy_url and '@' in proxy_url else proxy_url[:30] if proxy_url else None
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
