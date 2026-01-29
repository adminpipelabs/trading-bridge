"""
Database models and connection for Trading Bridge.
PostgreSQL persistence for clients, wallets, connectors, and bots.
"""
import os
from sqlalchemy import create_engine, Column, String, ForeignKey, JSON, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Handle Railway's postgres:// vs postgresql:// URL format
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip()
    
    if DATABASE_URL.startswith("${{") and DATABASE_URL.endswith("}}"):
        logger.error(f"Railway reference not resolved: {DATABASE_URL}. Check Railway configuration.")
        DATABASE_URL = ""
    else:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        elif DATABASE_URL.startswith("postgresql://"):
            if "+psycopg2" not in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
                DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        logger.info(f"Using DATABASE_URL format: {DATABASE_URL.split('@')[0]}@...")

# Create engine with connection pooling
engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        if "+asyncpg" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")
            logger.info("Replaced +asyncpg with +psycopg2 in DATABASE_URL")
        
        if "+psycopg2" not in DATABASE_URL:
            if DATABASE_URL.startswith("postgresql://"):
                DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            elif DATABASE_URL.startswith("postgres://"):
                DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        
        if "@host:" in DATABASE_URL or "@host/" in DATABASE_URL:
            logger.error("DATABASE_URL contains placeholder 'host' - check Railway configuration")
            DATABASE_URL = ""
            engine = None
            SessionLocal = None
        else:
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={"connect_timeout": 10}
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            logger.info(f"Database engine created successfully")
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        engine = None
        SessionLocal = None
else:
    logger.warning("DATABASE_URL not set - database features will be unavailable")


class Client(Base):
    """Client model - stores client information and account identifier"""
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    account_identifier = Column(String, unique=True, nullable=False, index=True)
    
    # Frontend-compatible fields (legacy support)
    wallet_address = Column(String, nullable=True, index=True)
    wallet_type = Column(String, nullable=True)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    status = Column(String, default='active')
    tier = Column(String, nullable=True)
    role = Column(String, default='client')
    settings = Column(JSON, nullable=True, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wallets = relationship("Wallet", back_populates="client", cascade="all, delete-orphan")
    connectors = relationship("Connector", back_populates="client", cascade="all, delete-orphan")
    bots = relationship("Bot", back_populates="client", cascade="all, delete-orphan")


class Wallet(Base):
    """Wallet model - stores wallet addresses for clients"""
    __tablename__ = "wallets"
    
    id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    chain = Column(String, nullable=False)
    address = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    client = relationship("Client", back_populates="wallets")
    
    __table_args__ = (
        Index('idx_wallet_address', 'address'),
    )


class Connector(Base):
    """Connector model - stores exchange connector configurations"""
    __tablename__ = "connectors"
    
    id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    api_key = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)
    memo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    client = relationship("Client", back_populates="connectors")


class Bot(Base):
    """Bot model - stores bot definitions and status"""
    __tablename__ = "bots"
    
    id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    account = Column(String, nullable=False, index=True)
    instance_name = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    connector = Column(String, nullable=False)
    pair = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    bot_type = Column(String, nullable=True)  # 'volume' or 'spread' for Solana bots
    status = Column(String, default="stopped")
    config = Column(JSON, nullable=False, default={})
    stats = Column(JSON, nullable=True, default={})  # Track daily volume, trades, etc.
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    client = relationship("Client", back_populates="bots")
    
    __table_args__ = (
        Index('idx_bots_account', 'account'),
        Index('idx_bots_status', 'status'),
    )
    
    def to_dict(self):
        """Convert bot to dictionary for API responses"""
        chain = "solana" if "jupiter" in self.connector.lower() else "evm"
        return {
            "id": self.id,
            "client_id": self.client_id,
            "account": self.account,
            "instance_name": self.instance_name,
            "name": self.name,
            "connector": self.connector,
            "pair": self.pair,
            "strategy": self.strategy,
            "bot_type": self.bot_type,
            "status": self.status or "stopped",
            "config": self.config or {},
            "stats": self.stats or {},
            "error": self.error,
            "chain": chain,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BotWallet(Base):
    """Bot wallet model - stores encrypted private keys for bot trading wallets"""
    __tablename__ = "bot_wallets"
    
    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    wallet_address = Column(String, nullable=False, index=True)
    encrypted_private_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_bot_wallets_bot', 'bot_id'),
    )


class BotTrade(Base):
    """Bot trade model - stores trade history"""
    __tablename__ = "bot_trades"
    
    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    wallet_address = Column(String, nullable=True)
    side = Column(String, nullable=True)  # 'buy' or 'sell'
    amount = Column(String, nullable=True)
    price = Column(String, nullable=True)
    value_usd = Column(String, nullable=True)
    gas_cost = Column(String, nullable=True)
    tx_signature = Column(String, nullable=True)
    status = Column(String, nullable=True)  # 'success', 'failed', 'pending'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_bot_trades_bot', 'bot_id'),
        Index('idx_bot_trades_created', 'created_at'),
    )


def init_db():
    """Initialize database - creates all tables if they don't exist"""
    if not engine:
        logger.error("Database engine not available. Check DATABASE_URL configuration.")
        raise RuntimeError("Database engine not available. Check DATABASE_URL configuration.")
    
    from sqlalchemy import inspect, text
    
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables: {existing_tables}")
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Table creation completed")
        
        # Verify tables exist
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info(f"Tables after creation: {created_tables}")
        
        required_tables = ['clients', 'wallets', 'connectors', 'bots', 'bot_wallets', 'bot_trades']
        missing_tables = [t for t in required_tables if t not in created_tables]
        
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            raise RuntimeError(f"Failed to create required tables: {missing_tables}")
        
        logger.info("✅ DATABASE INITIALIZATION SUCCESSFUL")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise RuntimeError(f"Database initialization failed: {e}") from e


def get_db_session():
    """Get a new database session (for use in sync routes)"""
    if not SessionLocal:
        raise RuntimeError("Database not available. Set DATABASE_URL environment variable.")
    return SessionLocal()


def get_db():
    """Get database session - use as dependency in FastAPI routes"""
    if not SessionLocal:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not available. Set DATABASE_URL environment variable.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
