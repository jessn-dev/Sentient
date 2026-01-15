import redis
import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf # Keep for backups if needed

from .config import settings
from .schemas import StockRequest, PredictionResponse
from .providers import DataProvider
from .engine import PredictionEngine

logger = logging.getLogger(__name__)
app = FastAPI(title=settings.APP_NAME, version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis
try:
    cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
except:
    cache = None

# --- MODELS ---

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    change_percent: float
    is_market_open: bool

class NewsItem(BaseModel):
    title: str
    publisher: str
    link: str
    thumbnail: Optional[str] = None
    published: int
    related_ticker: str
    change_percent: float

# --- HELPERS ---

def derive_ticker(text: str, default: str) -> str:
    """
    Scans text for keywords to assign a relevant ticker.
    Useful for 'General Market' news.
    """
    text = text.upper()
    mappings = {
        "GOLD": "GLD",
        "SILVER": "SLV",
        "OIL": "USO",
        "BITCOIN": "BTC-USD",
        "CRYPTO": "BTC-USD",
        "ETHEREUM": "ETH-USD",
        "NVIDIA": "NVDA",
        "TESLA": "TSLA",
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "AMAZON": "AMZN",
        "GOOGLE": "GOOGL",
        "META": "META",
        "NETFLIX": "NFLX",
        "AMD": "AMD",
        "INTEL": "INTC",
        "FED": "SPY",     # Fed news affects whole market
        "POWELL": "SPY",
        "INFLATION": "SPY",
        "JOBS": "SPY"
    }

    for keyword, ticker in mappings.items():
        if keyword in text:
            return ticker

    return default

# --- ROUTES ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/quotes", response_model=Dict[str, QuoteResponse])
async def get_batch_quotes(symbols: str = Query(..., description="Comma-separated symbols")):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list: return {}

    try:
        provider = DataProvider()
        from alpaca.data.requests import StockSnapshotRequest

        req = StockSnapshotRequest(symbol_or_symbols=symbol_list)
        snapshots = provider.client.get_stock_snapshot(req)

        results = {}
        for sym, snap in snapshots.items():
            price = 0.0
            if snap.latest_trade and snap.latest_trade.price > 0:
                price = snap.latest_trade.price
            elif snap.daily_bar and snap.daily_bar.close > 0:
                price = snap.daily_bar.close
            elif snap.previous_daily_bar and snap.previous_daily_bar.close > 0:
                price = snap.previous_daily_bar.close

            prev_close = snap.previous_daily_bar.close if snap.previous_daily_bar else 0.0
            change = ((price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0

            results[sym] = QuoteResponse(
                symbol=sym,
                price=price,
                change_percent=round(change, 2),
                is_market_open=True
            )
        return results
    except Exception as e:
        logger.error(f"Batch Quote Error: {e}")
        return {s: QuoteResponse(symbol=s, price=0.0, change_percent=0.0, is_market_open=False) for s in symbol_list}

@app.get("/news/{symbol}", response_model=List[NewsItem])
async def get_stock_news(symbol: str):
    try:
        # 1. Fetch RSS Feed
        # Relaxed 'when' filter to 2d to capture Reuters/others that might be slightly older
        sources = "site:reuters.com OR site:cnbc.com OR site:marketwatch.com"

        if symbol.upper() == "MARKET":
            raw_query = f"stock market ({sources})" # Removed strict 'when:1d' to broaden sources
        else:
            raw_query = f"{symbol} stock ({sources})"

        rss_url = f"https://news.google.com/rss/search?q={quote(raw_query)}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)

        # 2. Identify Unique Tickers needed for this batch
        news_entries = feed.entries[:12]
        unique_tickers = set()

        for entry in news_entries:
            # If we are in "MARKET" mode, try to detect ticker from title
            # If searching specific stock (e.g. AAPL), always use that stock
            if symbol.upper() == "MARKET":
                ticker = derive_ticker(entry.title, "SPY")
            else:
                ticker = symbol.upper()
            unique_tickers.add(ticker)

        # 3. Batch Fetch Live Prices (Optimization)
        # We call our own /quotes logic internally or reuse provider
        # Reuse provider for speed:
        provider = DataProvider()
        from alpaca.data.requests import StockSnapshotRequest

        # Safe fetch
        ticker_map = {}
        if unique_tickers:
            try:
                snap_req = StockSnapshotRequest(symbol_or_symbols=list(unique_tickers))
                snapshots = provider.client.get_stock_snapshot(snap_req)
                for sym, snap in snapshots.items():
                    price = snap.latest_trade.price if snap.latest_trade else (snap.daily_bar.close if snap.daily_bar else 0.0)
                    if price == 0 and snap.previous_daily_bar: price = snap.previous_daily_bar.close

                    prev = snap.previous_daily_bar.close if snap.previous_daily_bar else 0.0
                    change = ((price - prev) / prev) * 100 if prev > 0 else 0.0
                    ticker_map[sym] = change
            except Exception as e:
                logger.error(f"News Price Fetch Error: {e}")

        # 4. Build Response
        results = []
        for entry in news_entries:
            title_parts = entry.title.rsplit(' - ', 1)
            clean_title = title_parts[0]
            publisher = title_parts[1] if len(title_parts) > 1 else "Unknown"

            # Determine ticker again to grab from map
            if symbol.upper() == "MARKET":
                ticker = derive_ticker(entry.title, "SPY")
            else:
                ticker = symbol.upper()

            results.append(NewsItem(
                title=clean_title,
                publisher=publisher,
                link=entry.link,
                thumbnail=None,
                published=int(datetime(*entry.published_parsed[:6]).timestamp()),
                related_ticker=ticker,
                change_percent=round(ticker_map.get(ticker, 0.0), 2)
            ))

        return results

    except Exception as e:
        logger.error(f"News Error: {e}")
        return []

@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: StockRequest):
    # ... (Keep existing Predict logic) ...
    symbol = request.symbol.upper()
    cache_key = f"prediction_v2:{symbol}"

    if cache:
        try:
            cached = cache.get(cache_key)
            if cached: return PredictionResponse.model_validate_json(cached)
        except: pass

    try:
        provider = DataProvider()
        data = provider.fetch_data(symbol)
        engine = PredictionEngine()
        result = engine.predict(request, data["history"], data["info"])

        if cache: cache.set(cache_key, result.model_dump_json(), ex=3600)
        return result
    except Exception as e:
        logger.error(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))