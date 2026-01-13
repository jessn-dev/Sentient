from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # App Config
    APP_NAME: str = "StockPredictor v1"
    DEBUG_MODE: bool = False

    # Redis Config
    REDIS_URL: str = "redis://redis:6379/0"

    # API Keys (Simulated for this demo)
    # Using SecretStr prevents them from being logged in plain text
    MARKET_API_KEY: SecretStr = Field(default="mock_key")

settings = Settings()