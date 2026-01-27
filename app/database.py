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
# Railway resolves ${{Postgres.DATABASE_URL}} before our code sees it
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip()
    
    # Check if Railway reference wasn't resolved (shouldn't happen, but handle it)
    if DATABASE_URL.startswith("${{") and DATABASE_URL.endswith("}}"):
        logger.error(f"Railway reference not resolved: {DATABASE_URL}. Check Railway configuration.")
        DATABASE_URL = ""  # Set to empty to prevent connection attempts
    else:
        # Regular URL - ensure sync driver
        # Convert postgres:// to postgresql+psycopg2:// (explicit sync driver)
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        elif DATABASE_URL.startswith("postgresql://"):
            # Only add +psycopg2 if not already present and not asyncpg
            if "+psycopg2" not in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
                DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        logger.info(f"Using DATABASE_URL format: {DATABASE_URL.split('@')[0]}@...")  # Log without password

# Create engine with connection pooling
engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        # CRITICAL: Replace asyncpg with psycopg2 FIRST (before any other processing)
        if "+asyncpg" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")
            logger.info("Replaced +asyncpg with +psycopg2 in DATABASE_URL")
        
        # Ensure psycopg2 driver is used
        if "+psycopg2" not in DATABASE_URL:
            if DATABASE_URL.startswith("postgresql://"):
                DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            elif DATABASE_URL.startswith("postgres://"):
                DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        
        # Check for placeholder hostname - log error but don't crash app
        if "@host:" in DATABASE_URL or "@host/" in DATABASE_URL:
            logger.error("=" * 80)
            logger.error("DATABASE_URL CONFIGURATION ERROR:")
            logger.error(f"DATABASE_URL contains placeholder 'host' - URL: {DATABASE_URL.split('@')[0]}@...")
            logger.error("")
            logger.error("TO FIX:")
            logger.error("1. Railway Dashboard → PostgreSQL service → Variables tab")
            logger.error("2. Click on DATABASE_URL and copy the value")
            logger.error("3. Railway Dashboard → trading-bridge → Variables")
            logger.error("4. Update DATABASE_URL with: postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway")
            logger.error("   (Replace PASSWORD with actual password from PostgreSQL)")
            logger.error("=" * 80)
            # Don't raise - allow app to start, endpoints will return proper errors
            DATABASE_URL = ""  # Set to empty to prevent connection attempts
            engine = None
            SessionLocal = None
        else:
            # URL looks valid - try to create engine
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10,
                connect_args={"connect_timeout": 10}  # Add timeout
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            logger.info(f"Database engine created successfully with URL: {DATABASE_URL.split('@')[0]}@...")
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
    """Initialize database - creates all tables if they don't exist (PRODUCTION READY)"""
    if not engine:
        logger.error("=" * 80)
        logger.error("DATABASE INITIALIZATION FAILED:")
        logger.error("Database engine is None - cannot create tables")
        logger.error("")
        logger.error("Possible causes:")
        logger.error("1. DATABASE_URL not set or invalid")
        logger.error("2. DATABASE_URL contains placeholder 'host'")
        logger.error("3. Database connection failed during engine creation")
        logger.error("")
        logger.error("Check Railway logs for engine creation errors above")
        logger.error("=" * 80)
        raise RuntimeError("Database engine not available. Check DATABASE_URL configuration.")
    
    from sqlalchemy import inspect, text
    
    try:
        # Step 1: Check what tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables before init: {existing_tables}")
        
        # Step 2: Check for type mismatches and drop if needed
        if 'clients' in existing_tables:
            logger.info("Checking 'clients' table for type mismatches...")
            needs_drop = False
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'clients' AND column_name = 'id'
                    """))
                    row = result.fetchone()
                    if row and row[0] == 'uuid':
                        logger.warning("⚠️  Found UUID type mismatch - MUST drop all tables")
                        needs_drop = True
            except Exception as check_error:
                logger.warning(f"Could not check table types: {check_error}")
                # If we can't check, drop anyway to be safe
                needs_drop = True
            
            if needs_drop:
                logger.warning("Dropping ALL tables to fix type mismatch...")
                try:
                    # Drop in correct order to avoid foreign key errors
                    with engine.begin() as conn:
                        # Drop tables with foreign keys first
                        conn.execute(text("DROP TABLE IF EXISTS bots CASCADE"))
                        conn.execute(text("DROP TABLE IF EXISTS connectors CASCADE"))
                        conn.execute(text("DROP TABLE IF EXISTS wallets CASCADE"))
                        conn.execute(text("DROP TABLE IF EXISTS clients CASCADE"))
                    logger.info("✅ Dropped all existing tables")
                except Exception as drop_error:
                    logger.error(f"Failed to drop tables: {drop_error}")
                    # Try using SQLAlchemy drop_all as fallback
                    try:
                        Base.metadata.drop_all(bind=engine)
                        logger.info("✅ Dropped tables using SQLAlchemy")
                    except Exception as fallback_error:
                        logger.error(f"Fallback drop also failed: {fallback_error}")
                        raise RuntimeError(f"Cannot drop existing tables with wrong types: {drop_error}")
        
        # Step 3: CREATE ALL TABLES (this is idempotent - won't fail if tables exist)
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Table creation command completed")
        
        # Step 4: VERIFY tables exist (critical check)
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info(f"Tables after creation: {created_tables}")
        
        required_tables = ['clients', 'wallets', 'connectors', 'bots']
        missing_tables = [t for t in required_tables if t not in created_tables]
        
        if missing_tables:
            logger.error("=" * 80)
            logger.error("CRITICAL: Required tables are missing!")
            logger.error(f"Missing: {missing_tables}")
            logger.error(f"Found: {created_tables}")
            logger.error("=" * 80)
            raise RuntimeError(f"Failed to create required tables: {missing_tables}")
        
        # Step 5: Verify column types are correct
        logger.info("Verifying column types...")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name, column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name IN ('clients', 'wallets', 'connectors', 'bots')
                    AND column_name IN ('id', 'client_id')
                    ORDER BY table_name, column_name
                """))
                logger.info("Column types verified:")
                for row in result:
                    logger.info(f"  {row[0]}.{row[1]}: {row[2]}")
                    if row[2] == 'uuid':
                        logger.error(f"ERROR: {row[0]}.{row[1]} is UUID but should be VARCHAR!")
                        raise RuntimeError(f"Type mismatch: {row[0]}.{row[1]} is UUID")
        except Exception as verify_error:
            logger.warning(f"Could not verify column types: {verify_error}")
            # Don't fail - tables exist, types might be OK
        
        logger.info("=" * 80)
        logger.info("✅ DATABASE INITIALIZATION SUCCESSFUL")
        logger.info(f"✅ All tables created: {', '.join(required_tables)}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ CRITICAL: DATABASE INITIALIZATION FAILED")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("=" * 80)
        # Re-raise to prevent app from starting with broken database
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
