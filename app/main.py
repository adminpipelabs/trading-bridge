"""
Trading Bridge - Main FastAPI Application
Connects Pipe Labs Dashboard to cryptocurrency exchanges via ccxt
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.jupiter_routes import router as jupiter_router

from app.core.config import settings
from app.api import accounts, connectors, market, orders, portfolio
from app.bot_routes import router as bot_router, init_bot_manager
from app.clients_routes import router as clients_router
from app.database import init_db
from app.services.exchange import exchange_manager
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue anyway - database features will be unavailable
    yield
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

# Initialize bot manager
try:
    init_bot_manager(exchange_manager)
except Exception as e:
    logger.error(f"Failed to initialize bot manager: {e}")
    # Continue without bot manager if initialization fails
    logger.warning("Bot management features will be unavailable")

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
app.include_router(jupiter_router)
app.include_router(bot_router, tags=["Bots"])
app.include_router(clients_router, tags=["Clients"])

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
    database_status = "postgresql" if os.getenv("DATABASE_URL") else "unavailable"
    return {
        "status": "healthy",
        "service": "Trading Bridge",
        "database": database_status
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
        "url_without_space": url_without_space or "NOT SET"
    }
