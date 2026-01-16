import redis
import logging
import feedparser
import ssl
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from urllib.parse import quote
from contextlib import asynccontextmanager

# FastAPI & SQLModel
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, delete
from qstash import Receiver

# Internal Modules
from .config import settings
from .schemas import StockRequest, PredictionResponse
from .providers import DataProvider
from .engine import PredictionEngine
from .database import create_db_and_tables, get_session
from .models import Prediction, SavePredictionRequest, NewsItem, QuoteResponse

# Initialize Logger
logger = logging.getLogger("uvicorn")

# --- LIFESPAN MANAGER (Replaces on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup Logic
    print("\n" + "="*60)
    print(f"🚀  STARTING {settings.APP_NAME}")
    print(f"🌍  ENVIRONMENT:  {settings.ENVIRONMENT}")

    db_type = "POSTGRESQL (Production)" if "postgresql" in settings.DATABASE_URL else "SQLITE (Local)"
    print(f"💾  DATABASE:     {db_type}")

    # Check Redis Connection
    redis_status = "DISABLED (Not Configured)"
    if settings.REDIS_URL:
        try:
            test_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            if test_redis.ping():
                redis_status = f"CONNECTED ({settings.REDIS_URL})"
        except Exception as e:
            redis_status = f"ERROR: {e}"

    print(f"⚡  REDIS:        {redis_status}")
    print("="*60 + "\n")

    create_db_and_tables()

    yield # Application runs here

    # 2. Shutdown Logic (Clean up resources if needed)
    pass

# --- FASTAPI SETUP ---
app = FastAPI(
    title=settings.APP_NAME,
    version="1.6.0",
    lifespan=lifespan # New method
)

# CORS Setup
origins = [
    "http://localhost:3000",                  # Local Dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use specific list in Prod
    # ALLOW REGEX (Optional but helpful for Vercel Previews):
    # This allows ANY app on vercel.app to talk to your backend
    allow_origin_regex="https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Cache Client (Global)
try:
    cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    cache = None


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
    return {"status": "ok", "version": "1.6.0"}


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

            # Fix datetime warning
            pub_time = int(datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).timestamp()) if entry.published_parsed else int(datetime.now(timezone.utc).timestamp())

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

        # Strict 1-hour TTL for memory management
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
        saved_at=datetime.now(timezone.utc), # Fix datetime warning
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
        limit: int = 20
):
    """Fetch history of saved forecasts (Limit 20 for bandwidth)"""
    statement = (
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(Prediction.saved_at.desc())
        .limit(limit)
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
    Called by QStash daily to validate expired predictions.
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

            # ⚠️ FIX: Use Keyword Arguments (body=..., signature=...)
            receiver.verify(
                body=body.decode(),
                signature=signature
            )
        except Exception as e:
            logger.error(f"⚠️ QStash Verification Failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid QStash Signature")

    # 2. FIND PENDING PREDICTIONS
    now = datetime.now(timezone.utc) # Fix datetime warning
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
    Weekly Job: Deletes validated predictions older than 30 days.
    """
    # 1. SECURITY
    if settings.QSTASH_CURRENT_SIGNING_KEY and settings.QSTASH_NEXT_SIGNING_KEY:
        try:
            receiver = Receiver(
                current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
                next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY
            )
            body = await request.body()
            signature = request.headers.get("Upstash-Signature")

            # ⚠️ FIX: Use Keyword Arguments here too
            receiver.verify(
                body=body.decode(),
                signature=signature
            )
        except Exception as e:
            logger.error(f"⚠️ QStash Verification Failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid Signature")

    # 2. RETENTION POLICY (30 Days)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30) # Fix datetime warning

    statement = delete(Prediction).where(
        Prediction.status == "VALIDATED",
        Prediction.target_date < cutoff_date
    )

    result = db.exec(statement)
    db.commit()

    deleted_count = result.rowcount if hasattr(result, "rowcount") else "Unknown"

    return {"status": "cleanup_complete", "deleted_rows": deleted_count}

# --- HELPER: SMART REDIS CONNECTION ---
def get_redis_client():
    """
    Connects to Redis with logic for both Local (plain) and Cloud (SSL).
    """
    if not settings.REDIS_URL:
        return None

    try:
        # 1. Handle Upstash/Cloud SSL quirks
        # If we are using a secure connection (rediss://) or a cloud provider,
        # we need to disable strict SSL checking to avoid "certificate verify failed"
        # errors in minimal Docker containers.
        ssl_context = None
        url = settings.REDIS_URL

        # Auto-upgrade to rediss:// if we detect an Upstash URL but user forgot 's'
        if "upstash" in url and url.startswith("redis://"):
            url = url.replace("redis://", "rediss://", 1)

        # Configure connection args
        connection_kwargs = {
            "decode_responses": True,
            "socket_timeout": 5  # Don't hang forever if Redis is down
        }

        # If secure, relax SSL requirements
        if url.startswith("rediss://"):
            connection_kwargs["ssl_cert_reqs"] = None

        return redis.from_url(url, **connection_kwargs)

    except Exception as e:
        logger.warning(f"⚠️ Redis config invalid: {e}")
        return None

# Initialize Global Cache
cache = get_redis_client()

# --- LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global cache
    # 1. Startup Logic
    print("\n" + "="*60)
    print(f"🚀  STARTING {settings.APP_NAME}")
    print(f"🌍  ENVIRONMENT:  {settings.ENVIRONMENT}")

    db_type = "POSTGRESQL (Production)" if "postgresql" in settings.DATABASE_URL else "SQLITE (Local)"
    print(f"💾  DATABASE:     {db_type}")

    # 2. Test Redis Connection
    redis_status = "DISABLED (Not Configured)"
    if cache:
        try:
            if cache.ping():
                # Hide the password in logs
                safe_url = settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL
                redis_status = f"CONNECTED ({safe_url})"
        except Exception as e:
            redis_status = f"ERROR: {e}"
            # If ping fails, disable cache to prevent runtime errors
            cache = None

    print(f"⚡  REDIS:        {redis_status}")
    print("="*60 + "\n")

    create_db_and_tables()

    yield # Application runs here

    # 3. Shutdown Logic
    if cache:
        try:
            cache.close()
        except: pass