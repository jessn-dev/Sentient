from enum import Enum
from datetime import date, datetime
from typing import Annotated, List, Optional
from pydantic import (
    BaseModel, Field, ConfigDict, StrictFloat, StrictInt,
    field_validator, computed_field
)

# --- Enums & Types ---
class StockExchange(str, Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    SSE = "SSE"

# Reusable Validator: Upper case string, 1-5 chars
TickerSymbol = Annotated[str, Field(min_length=1, max_length=5, pattern=r"^[A-Z]+$")]

# --- Input Models ---
class StockRequest(BaseModel):
    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    symbol: TickerSymbol
    exchange: StockExchange = StockExchange.NASDAQ

# --- Internal Data Structures ---
class MarketRecord(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)

    timestamp: datetime
    open: StrictFloat
    high: StrictFloat
    low: StrictFloat
    close: StrictFloat
    volume: StrictInt

# --- Output Models ---
class PredictionResponse(BaseModel):
    symbol: str
    current_price: float
    predicted_price_7d: float
    confidence_score: float
    forecast_date: date

    @computed_field
    @property
    def price_movement(self) -> str:
        if self.predicted_price_7d > self.current_price:
            return "BULLISH"
        elif self.predicted_price_7d < self.current_price:
            return "BEARISH"
        return "NEUTRAL"

    @computed_field
    @property
    def growth_percentage(self) -> float:
        if self.current_price == 0: return 0.0
        delta = self.predicted_price_7d - self.current_price
        return round((delta / self.current_price) * 100, 2)