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
# Also check for Railway service reference format: ${{Postgres.DATABASE_URL}}
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    # Remove Railway reference wrapper if present
    DATABASE_URL = DATABASE_URL.strip().strip("${{}}").strip()
    # Convert postgres:// to postgresql+psycopg2:// (explicit sync driver)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
        # Ensure we use psycopg2 (sync driver) not asyncpg
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Create engine with connection pooling
engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        # Force sync driver - ensure psycopg2 is used, not asyncpg
        if "+psycopg2" not in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
            if DATABASE_URL.startswith("postgresql://"):
                DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        # Remove asyncpg if somehow present
        DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")
        
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 10}  # Add timeout
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info(f"Database engine created successfully with URL: {DATABASE_URL[:50]}...")
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
    chain = Column(String, nullable=False)  # 'evm' or 'solana'
    address = Column(String, nullable=False, index=True)  # Indexed for fast lookup
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    client = relationship("Client", back_populates="wallets")
    
    # Index for wallet address lookups
    __table_args__ = (
        Index('idx_wallet_address', 'address'),
    )


class Connector(Base):
    """Connector model - stores exchange connector configurations"""
    __tablename__ = "connectors"
    
    id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # 'bitmart', 'jupiter', etc.
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
    account = Column(String, nullable=False, index=True)  # Matches client.account_identifier
    instance_name = Column(String, unique=True, nullable=False)  # Used by Hummingbot
    name = Column(String, nullable=False)
    connector = Column(String, nullable=False)
    pair = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    status = Column(String, default="stopped")  # 'running', 'stopped', 'error'
    config = Column(JSON, nullable=False, default={})
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    client = relationship("Client", back_populates="bots")
    
    # Indexes for common queries
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
            "status": self.status or "stopped",
            "config": self.config or {},
            "error": self.error,
            "chain": chain,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def init_db():
    """Initialize database - creates all tables if they don't exist"""
    if not engine:
        logger.warning("Database engine not available - skipping table creation")
        return
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


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
