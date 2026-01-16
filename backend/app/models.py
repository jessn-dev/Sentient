from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional

# --- DATABASE TABLE ---
class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    symbol: str

    # AI Data to Save
    start_price: float           # Price at the moment of saving
    predicted_price: float       # The AI's 7-day target
    confidence_score: float      # The AI's confidence

    # Dates
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_date: datetime        # When we validate this (7 days later)

    # Status
    status: str = Field(default="ACTIVE") # ACTIVE, VALIDATED
    final_price: Optional[float] = None   # Filled after 7 days
    accuracy_score: Optional[float] = None # How close was it?

# --- API SCHEMAS ---

class SavePredictionRequest(SQLModel):
    user_id: str
    symbol: str
    current_price: float
    predicted_price: float
    confidence_score: float
    target_date: datetime # Passed from the AI response
    overwrite: bool = False # Flag to force replacement

class QuoteResponse(SQLModel):
    symbol: str
    price: float
    change_percent: float
    is_market_open: bool

class NewsItem(SQLModel):
    title: str
    publisher: str
    link: str
    thumbnail: Optional[str] = None
    published: int
    related_ticker: str
    change_percent: float