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
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with connection pooling
engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine created successfully")
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
