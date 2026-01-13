from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App Config
    APP_NAME: str = "StockPredictor"
    DEBUG_MODE: bool = False

    # Alpaca Keys (New)
    ALPACA_API_KEY: str = Field(..., description="Public Key ID")
    ALPACA_SECRET_KEY: SecretStr = Field(..., description="Secret Key")

    # We use 'paper-api.alpaca.markets' for the free tier
    ALPACA_ENDPOINT: str = "https://paper-api.alpaca.markets/v2"

    # Redis Config
    REDIS_URL: str = "redis://redis:6379/0"

    # API Keys (Simulated for this demo)
    # Using SecretStr prevents them from being logged in plain text
    MARKET_API_KEY: SecretStr = Field(default="mock_key")

settings = Settings()