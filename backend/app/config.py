import os
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger("uvicorn")

class Settings(BaseSettings):
    # Core
    APP_NAME: str = "MarketMind AI API"
    ENVIRONMENT: str = "DEVELOPMENT" # Default to DEV

    # API Keys
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    # OPENAI_API_KEY: str = ""

    # Database
    # We leave this empty default to force logic below
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://redis:6379/0"

    # QStash
    QSTASH_CURRENT_SIGNING_KEY: str = ""
    QSTASH_NEXT_SIGNING_KEY: str = ""

    # Validation Logic
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 1. Determine Environment
        self.ENVIRONMENT = self.ENVIRONMENT.upper()

        # 2. Database Logic
        if not self.DATABASE_URL:
            if self.ENVIRONMENT == "PRODUCTION":
                # Prod MUST have a real URL (Postgres)
                raise ValueError("❌ FATAL: PRODUCTION environment requires DATABASE_URL to be set!")
            else:
                # Dev falls back to local SQLite
                self.DATABASE_URL = "sqlite:///./data/predictions.db"
                logger.warning("⚠️  Running in DEVELOPMENT mode. Using local SQLite.")

        # 3. Fix Postgres URL for SQLAlchemy
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

    class Config:
        env_file = ".env"
        # This allows you to override .env with real System Env Vars (important for Render)
        env_file_encoding = "utf-8"
        # Ignore dev env vars that don't exist':
        extra = "ignore"

settings = Settings()