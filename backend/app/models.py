from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from datetime import date
from typing import Optional

# --- DATABASE MODELS ---

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    symbol: str = Field(index=True)

    # Prices
    initial_price: float
    target_price: float
    final_price: Optional[float] = None

    # Scores
    confidence_score: float
    accuracy_score: Optional[float] = None

    # Status & Meta
    status: str = Field(default="ACTIVE") # ACTIVE, VALIDATED
    explanation: Optional[str] = None

    # Dates
    end_date: date
    finalized_date: Optional[date] = Field(default=None) # <--- NEW COLUMN
    created_at: date = Field(default_factory=date.today)


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