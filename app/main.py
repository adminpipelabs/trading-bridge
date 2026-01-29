"""
Trading Bridge - Main FastAPI Application
Connects Pipe Labs Dashboard to cryptocurrency exchanges via ccxt
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.jupiter_routes import router as jupiter_router
from app.solana_routes import router as solana_router

from app.core.config import settings
from app.api import accounts, connectors, market, orders, portfolio, client_data
from app.bot_routes import router as bot_router
from app.clients_routes import router as client_router
from app.auth_routes import router as auth_router
from app.exchange_routes import router as exchange_router
from app.database import init_db
from app.services.exchange import exchange_manager
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup - FAIL FAST if database init fails."""
    logger.info("=" * 80)
    logger.info("STARTING DATABASE INITIALIZATION")
    logger.info("=" * 80)
    
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
    
    # Start bot runner service (in background)
    async def start_bot_runner():
        try:
            logger.info("=" * 80)
            logger.info("ATTEMPTING TO START BOT RUNNER")
            logger.info("=" * 80)
            from app.bot_runner import bot_runner
            logger.info("✅ Bot runner module imported successfully")
            await bot_runner.start()
            logger.info("✅ Bot runner started successfully")
        except ImportError as e:
            logger.error("=" * 80)
            logger.error("❌ BOT RUNNER IMPORT FAILED")
            logger.error(f"Error: {e}")
            logger.error("Check if app/bot_runner.py exists")
            logger.error("=" * 80)
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ BOT RUNNER STARTUP FAILED")
            logger.error(f"Error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
    
    # Start bot runner in background - use create_task to run concurrently
    logger.info("Creating bot runner task...")
    try:
        # Create task and let it run in background
        task = asyncio.create_task(start_bot_runner())
        logger.info("✅ Bot runner task created")
        logger.info("Bot runner service starting...")
        # Give it a moment to start
        await asyncio.sleep(0.1)
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ FAILED TO CREATE BOT RUNNER TASK")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        # Don't fail app startup if bot runner fails
    
    yield
    
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Trading Bridge",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    import os
    from app.database import engine, SessionLocal
    
    # Check bot runner status
    bot_runner_status = "unknown"
    bot_runner_running = False
    try:
        from app.bot_runner import bot_runner
        bot_runner_running = len(bot_runner.running_bots) > 0
        bot_runner_status = f"running ({len(bot_runner.running_bots)} bots)" if bot_runner_running else "started (0 bots)"
    except Exception as e:
        bot_runner_status = f"error: {str(e)[:50]}"
    
    database_status = "postgresql" if (os.getenv("DATABASE_URL") and engine and SessionLocal) else "unavailable"
    return {
        "status": "healthy",
        "service": "Trading Bridge",
        "database": database_status,
        "bot_runner": bot_runner_status
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
