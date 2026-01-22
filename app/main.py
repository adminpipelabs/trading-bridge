"""
Trading Bridge Service
Connects Pipe Labs Dashboard to crypto exchanges via ccxt
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import accounts, connectors, portfolio, orders, market
from app.services.exchange import exchange_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Trading Bridge starting up...")
    yield
    logger.info("Trading Bridge shutting down...")
    await exchange_manager.close_all()


app = FastAPI(
    title="Trading Bridge API",
    description="Bridge service connecting Pipe Labs to crypto exchanges",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow all for now, tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router, tags=["Accounts"])
app.include_router(connectors.router, tags=["Connectors"])
app.include_router(portfolio.router, tags=["Portfolio"])
app.include_router(orders.router, tags=["Orders"])
app.include_router(market.router, tags=["Market Data"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "trading-bridge",
        "accounts": len(exchange_manager.accounts)
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Trading Bridge",
        "version": "1.0.0",
        "docs": "/docs"
    }
