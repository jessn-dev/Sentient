import redis
import logging
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote
import sys

# FastAPI & SQLModel
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, delete
from qstash import Receiver  # For validating QStash webhooks

# Internal Modules
from .config import settings
from .schemas import StockRequest, PredictionResponse
from .providers import DataProvider
from .engine import PredictionEngine
from .database import create_db_and_tables, get_session
from .models import Prediction, SavePredictionRequest, NewsItem, QuoteResponse

# Initialize Logger
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title=settings.APP_NAME, version="1.5.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Cache Setup
try:
    cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
    logger.info("✅ Redis connected successfully.")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Caching is disabled.")
    cache = None

# Initialize DB on Startup
@app.on_event("startup")
def on_startup():
    # 1. Clear Console Banner
    print("\n" + "="*60)
    print(f"🚀  STARTING {settings.APP_NAME}")
    print(f"🌍  ENVIRONMENT:  {settings.ENVIRONMENT}")

    # 2. Database Check
    db_type = "POSTGRESQL (Production)" if "postgresql" in settings.DATABASE_URL else "SQLITE (Local)"
    print(f"💾  DATABASE: {db_type}")

    # 3. Cache Check
    if cache:
        print(f"⚡  REDIS: CONNECTED ({settings.REDIS_URL})")
    else:
        print(f"⚠️   REDIS: DISABLED (Not Configured)")

    print("="*60 + "\n")

    # 4. Initialize Tables
    create_db_and_tables()


# --- HELPERS ---

def derive_ticker(text: str, default: str) -> str:
    """Scans text for keywords to assign a relevant ticker."""
    text = text.upper()
    mappings = {
        "GOLD": "GLD", "SILVER": "SLV", "OIL": "USO",
        "BITCOIN": "BTC-USD", "CRYPTO": "BTC-USD", "ETHEREUM": "ETH-USD",
        "NVIDIA": "NVDA", "TESLA": "TSLA", "APPLE": "AAPL",
        "MICROSOFT": "MSFT", "AMAZON": "AMZN", "GOOGLE": "GOOGL",
        "META": "META", "NETFLIX": "NFLX", "AMD": "AMD",
        "INTEL": "INTC", "FED": "SPY", "POWELL": "SPY",
        "INFLATION": "SPY", "JOBS": "SPY"
    }
    for keyword, ticker in mappings.items():
        if keyword in text:
            return ticker
    return default


# --- PUBLIC DATA ROUTES ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.5.0"}


@app.get("/quotes", response_model=Dict[str, QuoteResponse])
async def get_batch_quotes(symbols: str = Query(..., description="Comma-separated symbols")):
    """Fetches live snapshots for multiple symbols efficiently."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list: return {}

    try:
        provider = DataProvider()
        from alpaca.data.requests import StockSnapshotRequest

        req = StockSnapshotRequest(symbol_or_symbols=symbol_list)
        snapshots = provider.client.get_stock_snapshot(req)

        results = {}
        for sym, snap in snapshots.items():
            # Robust Price Logic (Live -> Today -> Prev)
            price = 0.0
            if snap.latest_trade and snap.latest_trade.price > 0:
                price = snap.latest_trade.price
            elif snap.daily_bar and snap.daily_bar.close > 0:
                price = snap.daily_bar.close
            elif snap.previous_daily_bar and snap.previous_daily_bar.close > 0:
                price = snap.previous_daily_bar.close

            prev_close = snap.previous_daily_bar.close if snap.previous_daily_bar else 0.0
            change = 0.0
            if prev_close > 0 and price > 0:
                change = ((price - prev_close) / prev_close) * 100

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
    """Fetches news from Google RSS and attaches live ticker context."""
    try:
        sources = "site:reuters.com OR site:cnbc.com OR site:marketwatch.com"
        if symbol.upper() == "MARKET":
            raw_query = f"stock market ({sources})"
        else:
            raw_query = f"{symbol} stock ({sources})"

        rss_url = f"https://news.google.com/rss/search?q={quote(raw_query)}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)

        # Batch Fetch Prices logic
        news_entries = feed.entries[:12]
        unique_tickers = set()
        for entry in news_entries:
            if symbol.upper() == "MARKET":
                ticker = derive_ticker(entry.title, "SPY")
            else:
                ticker = symbol.upper()
            unique_tickers.add(ticker)

        ticker_map = {}
        if unique_tickers:
            try:
                provider = DataProvider()
                from alpaca.data.requests import StockSnapshotRequest
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

        results = []
        for entry in news_entries:
            title_parts = entry.title.rsplit(' - ', 1)
            clean_title = title_parts[0]
            publisher = title_parts[1] if len(title_parts) > 1 else "Unknown"

            if symbol.upper() == "MARKET":
                ticker = derive_ticker(entry.title, "SPY")
            else:
                ticker = symbol.upper()

            pub_time = int(datetime(*entry.published_parsed[:6]).timestamp()) if entry.published_parsed else int(datetime.utcnow().timestamp())

            results.append(NewsItem(
                title=clean_title,
                publisher=publisher,
                link=entry.link,
                thumbnail=None,
                published=pub_time,
                related_ticker=ticker,
                change_percent=round(ticker_map.get(ticker, 0.0), 2)
            ))
        return results

    except Exception as e:
        logger.error(f"News Error: {e}")
        return []


@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: StockRequest):
    """Deep Learning Forecast"""
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
        # Strict 1 hour expiration.
        # Even if you have heavy traffic, keys older than 1hr automatically vanish.
        if cache: cache.set(cache_key, result.model_dump_json(), ex=3600)
        return result
    except Exception as e:
        logger.error(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- PREDICTION SAVING ROUTES ---

@app.post("/predict/save")
async def save_prediction(
        req: SavePredictionRequest,
        db: Session = Depends(get_session)
):
    """
    Saves an AI prediction.
    If overwrite=False and active prediction exists -> 409 Conflict.
    If overwrite=True -> Deletes old and saves new.
    """
    # 1. Check for Existing Active Prediction
    statement = select(Prediction).where(
        Prediction.user_id == req.user_id,
        Prediction.symbol == req.symbol.upper(),
        Prediction.status == "ACTIVE"
    )
    existing_bet = db.exec(statement).first()

    # 2. Handle Conflict
    if existing_bet:
        if not req.overwrite:
            raise HTTPException(
                status_code=409,
                detail="You already have an active forecast for this stock."
            )
        else:
            db.delete(existing_bet)
            db.commit()

    # 3. Check Global Limit (Max 3 Active across all stocks)
    count_stmt = select(Prediction).where(
        Prediction.user_id == req.user_id,
        Prediction.status == "ACTIVE"
    )
    active_count = len(db.exec(count_stmt).all())

    if active_count >= 3:
        raise HTTPException(status_code=400, detail="You can only track 3 active predictions at a time.")

    # 4. Save New Prediction
    new_pred = Prediction(
        user_id=req.user_id,
        symbol=req.symbol.upper(),
        start_price=req.current_price,
        predicted_price=req.predicted_price,
        confidence_score=req.confidence_score,
        saved_at=datetime.utcnow(),
        target_date=req.target_date
    )
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)
    return {"status": "saved", "id": new_pred.id}


@app.get("/predict/user/{user_id}")
async def get_user_predictions(
        user_id: str,
        db: Session = Depends(get_session),
        limit: int = 20 # <--- Default limit
):
    """Fetch recent history (Limited to save Bandwidth)"""
    statement = (
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(Prediction.saved_at.desc())
        .limit(limit) # <--- Enforce limit
    )
    results = db.exec(statement).all()
    return results


# --- SCHEDULER (QSTASH) ---

@app.post("/scheduler/validate")
async def validate_predictions(
        request: Request,
        db: Session = Depends(get_session)
):
    """
    Called by QStash once a day to validate expired predictions.
    """
    # 1. SECURITY: Verify the request comes from QStash
    if settings.QSTASH_CURRENT_SIGNING_KEY and settings.QSTASH_NEXT_SIGNING_KEY:
        try:
            receiver = Receiver(
                current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
                next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY
            )
            body = await request.body()
            signature = request.headers.get("Upstash-Signature")
            receiver.verify(body.decode(), signature)
        except Exception as e:
            logger.error(f"⚠️ QStash Verification Failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid QStash Signature")

    # 2. FIND PENDING PREDICTIONS
    now = datetime.utcnow()
    statement = select(Prediction).where(
        Prediction.status == "ACTIVE",
        Prediction.target_date <= now
    )
    pending_bets = db.exec(statement).all()

    if not pending_bets:
        return {"message": "No predictions to validate today."}

    results = []

    # 3. PROCESS VALIDATION
    try:
        provider = DataProvider()
        unique_symbols = list(set(p.symbol for p in pending_bets))

        # Batch Fetch Final Prices
        from alpaca.data.requests import StockSnapshotRequest
        req = StockSnapshotRequest(symbol_or_symbols=unique_symbols)
        snapshots = provider.client.get_stock_snapshot(req)

        for bet in pending_bets:
            snap = snapshots.get(bet.symbol)
            if not snap: continue

            # Get Final Price
            final_price = snap.latest_trade.price if snap.latest_trade else snap.daily_bar.close

            # Calculate Accuracy
            diff = abs(bet.predicted_price - final_price)
            error_pct = (diff / final_price)
            accuracy = max(0, (1 - error_pct)) * 100

            # Update DB
            bet.final_price = final_price
            bet.accuracy_score = accuracy
            bet.status = "VALIDATED"
            db.add(bet)

            results.append(f"{bet.symbol}: Final ${final_price} (Acc: {accuracy:.1f}%)")

        db.commit()
        return {"validated_count": len(results), "details": results}

    except Exception as e:
        logger.error(f"Validation Job Error: {e}")
        return {"error": str(e)}

@app.post("/scheduler/cleanup")
async def cleanup_old_data(
        request: Request,
        db: Session = Depends(get_session)
):
    """
    Weekly Job: Deletes old validated predictions to save DB space.
    """
    # 1. SECURITY: Verify QStash
    if settings.QSTASH_CURRENT_SIGNING_KEY and settings.QSTASH_NEXT_SIGNING_KEY:
        try:
            receiver = Receiver(
                current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
                next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY
            )
            body = await request.body()
            signature = request.headers.get("Upstash-Signature")
            receiver.verify(body.decode(), signature)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid Signature")

    # 2. DEFINE RETENTION POLICY (e.g., 30 Days)
    # We only delete records that are 'VALIDATED' (completed) and older than 30 days
    cutoff_date = datetime.utcnow() - timedelta(days=30)

    statement = delete(Prediction).where(
        Prediction.status == "VALIDATED",
        Prediction.target_date < cutoff_date
    )

    result = db.exec(statement)
    db.commit()

    deleted_count = result.rowcount if hasattr(result, "rowcount") else "Unknown"

    # 3. OPTIONAL: FLUSH REDIS IF MEMORY IS HIGH
    # (Redis usually handles this with TTL, but we can force a clear if needed)
    # if cache:
    #     cache.flushdb()

    return {"status": "cleanup_complete", "deleted_rows": deleted_count}