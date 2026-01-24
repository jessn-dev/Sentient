from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, List

# Request Model
class StockRequest(BaseModel):
    symbol: str
    days: int = 7

# Sub-Models for Analysis
class TechnicalSignals(BaseModel):
    sma_50: float
    sma_200: float
    rsi: float
    bollinger_upper: float
    bollinger_lower: float
    rsi_signal: str       # "Overbought", "Oversold", "Neutral"
    trend_signal: str     # "Strong Uptrend", "Death Cross", etc.
    bollinger_signal: str # "High Volatility", "Normal"

class NewsItem(BaseModel):
    title: str
    link: str
    published: str
    sentiment: str        # "Positive", "Negative", "Neutral"

class SentimentAnalysis(BaseModel):
    score: float
    label: str            # "Bullish", "Bearish", "Neutral"
    news: List[NewsItem]

class LiquidityData(BaseModel):
    avg_volume: float
    market_cap: float
    bid_ask_spread: Optional[float]
    liquidity_rating: str # "High (Institutional)", "Low (Illiquid)"
    slippage_risk: str    # "Low", "High"

class MoverItem(BaseModel):
    symbol: str
    price: float
    change_pct: float
    volume: str

class MarketMoversResponse(BaseModel):
    gainers: List[MoverItem]
    losers: List[MoverItem]
    active: List[MoverItem]

# Main Response
class PredictionResponse(BaseModel):
    symbol: str
    company_name: str
    tv_symbol: str        # e.g., "NYSE:F"
    current_price: float
    predicted_price: float
    forecast_date: date
    confidence_score: float
    explanation: str
    technicals: Optional[TechnicalSignals] = None
    sentiment: Optional[SentimentAnalysis] = None
    liquidity: Optional[LiquidityData] = None

# --- Watchlist & Performance Models ---
class WatchlistAddRequest(BaseModel):
    symbol: str
    initial_price: float
    target_price: float
    end_date: date

class WatchlistPerformanceItem(BaseModel):
    id: int
    symbol: str
    initial_price: float
    target_price: float
    current_price: float
    final_price: Optional[float] = None
    end_date: date
    finalized_date: Optional[date] = None
    created_at: date
    accuracy_score: float
    status: str

class OptionStats(BaseModel):
    put_call_ratio: float
    total_call_vol: int
    total_put_vol: int
    implied_volatility: float
    nearest_expiry: str

class FundHolder(BaseModel):
    holder: str
    shares: int
    date_reported: str
    percent_out: float

class RealTimeMarketData(BaseModel):
    symbol: str
    market_cap: float
    short_float: float     # Short Interest %
    institutional_ownership: float
    options_sentiment: Optional[OptionStats] = None
    top_holders: List[FundHolder] = []

class UserCheckRequest(BaseModel):
    email: EmailStr