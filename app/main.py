"""
Trading Bridge - Main FastAPI Application
Connects Pipe Labs Dashboard to cryptocurrency exchanges via ccxt
"""
from fastapi import FastAPI
from app.jupiter_routes import router as jupiter_router
from app.bots_routes import router as bots_router
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import accounts, connectors, market, orders, portfolio
from app.bot_routes import router as bot_router, init_bot_manager
from app.services.exchange import exchange_manager

# Initialize bot manager
init_bot_manager(exchange_manager)

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
app.include_router(bots_router)

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
