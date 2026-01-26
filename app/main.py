"""
Trading Bridge - Main FastAPI Application
Connects Pipe Labs Dashboard to cryptocurrency exchanges via ccxt
"""
from fastapi import FastAPI
from app.jupiter_routes import router as jupiter_router
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import accounts, connectors, market, orders, portfolio
from app.bot_routes import router as bot_router, init_bot_manager
from app.services.exchange import exchange_manager
import os
import logging

logger = logging.getLogger(__name__)

# Validate production environment variables
def validate_production_config():
    """Validate required environment variables for production"""
    errors = []
    warnings = []
    
    # Check Hummingbot API URL
    hummingbot_url = os.getenv("HUMMINGBOT_API_URL", "")
    if not hummingbot_url:
        errors.append("HUMMINGBOT_API_URL is not set. Required for bot management.")
    elif "localhost" in hummingbot_url or "127.0.0.1" in hummingbot_url:
        warnings.append(
            f"HUMMINGBOT_API_URL is set to localhost ({hummingbot_url}). "
            "This will not work in Railway production. Use internal service name."
        )
    
    # Check authentication
    api_key = os.getenv("HUMMINGBOT_API_KEY", "")
    password = os.getenv("HUMMINGBOT_API_PASSWORD", "")
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
    return {
        "status": "ok",
        "service": "Trading Bridge"
    }


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    import os
    return {
        "HUMMINGBOT_API_URL": os.getenv("HUMMINGBOT_API_URL", "NOT SET"),
        "HUMMINGBOT_API_USERNAME": os.getenv("HUMMINGBOT_API_USERNAME", "NOT SET"),
        "has_password": bool(os.getenv("HUMMINGBOT_API_PASSWORD")),
        "all_env_keys": [k for k in os.environ.keys() if "HUMMINGBOT" in k]
    }
