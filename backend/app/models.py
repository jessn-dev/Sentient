from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

# --- DATABASE MODELS ---

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    symbol: str = Field(index=True)

    # Prices
    start_price: float
    predicted_price: float
    final_price: Optional[float] = None

    # Scores
    confidence_score: float
    accuracy_score: Optional[float] = None

    # Status & Meta
    status: str = Field(default="ACTIVE") # ACTIVE, VALIDATED
    explanation: Optional[str] = None

    # Dates
    # ⚠️ FIX: This was likely missing or named differently
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_date: datetime

# --- Pydantic Schemas (Request/Response Bodies) ---

class SavePredictionRequest(SQLModel):
    user_id: str
    symbol: str
    current_price: float
    predicted_price: float
    confidence_score: float
    target_date: datetime
    overwrite: bool = False

class NewsItem(SQLModel):
    title: str
    publisher: str
    link: str
    thumbnail: Optional[str] = None
    published: int
    related_ticker: str
    change_percent: float

class QuoteResponse(SQLModel):
    symbol: str
    price: float
    change_percent: float
    is_market_open: bool