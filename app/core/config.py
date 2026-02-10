"""
Trading Bridge Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "Trading Bridge"
    DEBUG: bool = False
    
    # Security
    API_KEY: str = ""  # Optional API key for securing the bridge
    
    # Database
    DATABASE_URL: str = ""  # PostgreSQL connection string
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Exchange defaults
    DEFAULT_TIMEOUT: int = 30000  # ms
    ENABLE_RATE_LIMIT: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields like DATABASE_URL from .env
        extra = "allow"  # Allow extra fields like DATABASE_URL


settings = Settings()
