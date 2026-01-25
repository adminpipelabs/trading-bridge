import os
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine) if engine else None
Base = declarative_base()

class ConnectorDB(Base):
    __tablename__ = "connectors"
    id = Column(String, primary_key=True)
    account_name = Column(String, index=True)
    connector_name = Column(String)
    credentials = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class BotDB(Base):
    __tablename__ = "bots"
    id = Column(String, primary_key=True)
    name = Column(String)
    client = Column(String, index=True)
    exchange = Column(String)
    pair = Column(String)
    bot_type = Column(String)
    config = Column(JSON)
    status = Column(String, default="stopped")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    if engine:
        Base.metadata.create_all(bind=engine)

def get_db():
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
