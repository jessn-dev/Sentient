import logging
import sys
import os
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from qstash import Receiver

from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
import yfinance as yf
import pandas as pd

# ✅ UPDATED IMPORTS (Pointing to core/)
from app.core.database import create_db_and_tables, get_session
from app.core.auth import get_current_user, check_user_exists
from app.core.config import settings

from app.models import Prediction
from app.services.engine import PredictionEngine
from app.schemas import (
    StockRequest, PredictionResponse, MarketMoversResponse,
    WatchlistAddRequest, WatchlistPerformanceItem,
    RealTimeMarketData, UserCheckRequest
)
from app.services.intelligence import MarketIntelligence

# --- ALPACA IMPORTS ---
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest
from alpaca.trading.client import TradingClient

# ✅ CONFIGURE LOGGER
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PRICE_CACHE: Dict[str, Dict] = {}
CACHE_TTL = 300

ALPACA_KEY = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")

alpaca_data = None
alpaca_trading = None

# ✅ INITIALIZE INTELLIGENCE SERVICE
market_brain = MarketIntelligence()

if ALPACA_KEY and ALPACA_SECRET:
    try:
        alpaca_data = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        alpaca_trading = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
        logger.info("✅ [INIT] Alpaca Clients Connected")
    except Exception as e:
        logger.error(f"⚠️ [INIT] Alpaca Init Failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Sentient API...")
    create_db_and_tables()
    yield
    logger.info("🛑 Shutting down Sentient API...")


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])


def get_live_prices(symbols: List[str]) -> Dict[str, float]:
    current_time = time.time()
    prices = {}
    missing = []

    # Check Cache
    for sym in symbols:
        cached = PRICE_CACHE.get(sym)
        if cached and (current_time - cached['timestamp'] < CACHE_TTL):
            prices[sym] = cached['price']
        else:
            missing.append(sym)

    if not missing: return prices

    # Fetch from Alpaca
    if alpaca_data:
        try:
            alpaca_map = {sym.replace('-', '.'): sym for sym in missing}
            req = StockSnapshotRequest(symbol_or_symbols=list(alpaca_map.keys()), feed='iex')
            snapshots = alpaca_data.get_stock_snapshot(req)
            for alpaca_sym, snapshot in snapshots.items():
                if snapshot.latest_trade:
                    price = float(snapshot.latest_trade.price)
                    if price > 0:
                        orig = alpaca_map.get(alpaca_sym, alpaca_sym)
                        prices[orig] = price
                        PRICE_CACHE[orig] = {"price": price, "timestamp": current_time}
                        if orig in missing: missing.remove(orig)
        except Exception as e:
            logger.warning(f"Alpaca price fetch failed: {e}")

    # Fallback to YFinance
    if missing:
        try:
            logger.info(f"Fetching fallback prices for: {missing}")
            data = yf.download(missing, period="1d", progress=False)['Close']
            if not data.empty:
                if isinstance(data, pd.Series):
                    val = float(data.iloc[-1])
                    prices[missing[0]] = val
                    PRICE_CACHE[missing[0]] = {"price": val, "timestamp": current_time}
                else:
                    curr = data.iloc[-1]
                    for sym in missing:
                        try:
                            val = float(curr[sym])
                            prices[sym] = val
                            PRICE_CACHE[sym] = {"price": val, "timestamp": current_time}
                        except:
                            pass
        except Exception as e:
            logger.warning(f"YFinance fallback failed: {e}")

    return prices


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: StockRequest):
    logger.info(f"🔮 Prediction Request: {request.symbol}")
    try:
        engine = PredictionEngine(data_client=alpaca_data, trading_client=alpaca_trading)
        result = engine.predict(request)
        logger.info(f"✅ Prediction Success: {request.symbol} -> Target ${result.predicted_price}")
        return result
    except Exception as e:
        logger.error(f"❌ Prediction Failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/market/movers", response_model=MarketMoversResponse)
async def get_movers():
    logger.info("📊 Fetching Market Movers...")
    try:
        movers = PredictionEngine(data_client=alpaca_data, trading_client=alpaca_trading).get_market_movers()
        logger.info(f"✅ Movers fetched: {len(movers.gainers)} gainers, {len(movers.losers)} losers")
        return movers
    except Exception as e:
        logger.error(f"❌ Failed to fetch movers: {e}")
        return {"gainers": [], "losers": [], "active": []}


@app.get("/watchlist/performance", response_model=List[WatchlistPerformanceItem])
async def get_watchlist_performance(session: Session = Depends(get_session), user_id: str = Depends(get_current_user)):
    predictions = session.exec(select(Prediction).where(Prediction.user_id == user_id)).all()

    if not predictions:
        return []

    today_dt = date.today()
    active_symbols = []

    # Helper to check if a date is a market day (Mon-Fri)
    def get_next_market_day(d: date) -> date:
        while d.weekday() > 4: d += timedelta(days=1)
        return d

    # Identify active symbols to fetch live prices
    for p in predictions:
        final_price = p.final_price if p.final_price is not None else 0.0
        # Only fetch live price if NOT finalized and NOT expired
        if final_price == 0.0:
            active_symbols.append(p.symbol)

    live_prices = get_live_prices(list(set(active_symbols))) if active_symbols else {}
    results = []

    for p in predictions:
        final_price = p.final_price if p.final_price is not None else 0.0
        target_final_date = get_next_market_day(p.end_date)
        is_matured = today_dt >= target_final_date

        # 1. Determine "Final" or "Current" price
        if final_price > 0.0:
            current_val = final_price  # It's finalized
        elif is_matured:
            # Try to finalize it now
            try:
                hist = yf.download(p.symbol, start=target_final_date, end=target_final_date + timedelta(days=2),
                                   progress=False)
                if not hist.empty:
                    val = float(hist['Close'].iloc[0])
                    p.final_price = val
                    p.finalized_date = target_final_date
                    current_val = val
                    session.add(p)
                    session.commit()
                    session.refresh(p)
                    final_price = val
                else:
                    # Market might be closed or data delayed
                    current_val = live_prices.get(p.symbol, p.initial_price)
            except:
                current_val = live_prices.get(p.symbol, p.initial_price)
        else:
            # Active tracking
            current_val = live_prices.get(p.symbol, p.initial_price)
            if current_val == 0.0: current_val = p.initial_price

        # 2. Calculate Accuracy (ONLY if Finalized/Matured)
        if final_price > 0.0 or is_matured:
            diff = abs(p.target_price - current_val)
            accuracy = max(0, 100 * (1 - (diff / p.target_price))) if p.target_price else 0

            if current_val >= p.target_price:
                status = "✅ SUCCESS"
            elif accuracy > 95:
                status = "⏱️ CLOSE"
            else:
                status = "❌ FAILED"
        else:
            accuracy = 0  # Pending
            status = "⏳ PENDING"

        results.append(WatchlistPerformanceItem(
            id=p.id,
            symbol=p.symbol,
            initial_price=p.initial_price,
            target_price=p.target_price,
            current_price=current_val,
            final_price=final_price if final_price > 0 else None,
            end_date=p.end_date,
            finalized_date=p.finalized_date,
            created_at=p.created_at,
            accuracy_score=round(accuracy, 1),
            status=status
        ))
    return results


@app.post("/scheduler/validate")
async def validate_predictions(request: Request, signature: str = Header(None, alias="Upstash-Signature"),
                               session: Session = Depends(get_session)):
    logger.info("⏰ Scheduler: Starting Validation Job")
    if settings.QSTASH_CURRENT_SIGNING_KEY:
        try:
            receiver = Receiver(current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
                                next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY)
            body = await request.body()
            receiver.verify(body.decode("utf-8"), signature)
        except:
            logger.warning("⚠️ Scheduler: Invalid QStash Signature")
            raise HTTPException(status_code=401, detail="Invalid QStash Signature")

    predictions = session.exec(select(Prediction).where(Prediction.final_price == 0.0)).all()
    if not predictions:
        logger.info("⏰ Scheduler: No pending predictions to validate.")
        return {"status": "success"}

    logger.info(f"⏰ Scheduler: Validating {len(predictions)} pending predictions...")
    live_prices = get_live_prices(list(set([p.symbol for p in predictions])))
    today = date.today()
    updates = 0
    finalized = 0

    for p in predictions:
        if p.symbol in live_prices:
            p.current_price = live_prices[p.symbol]
            if p.target_price > 0:
                diff = abs(p.target_price - p.current_price)
                p.accuracy_score = max(0.0, 100 * (1 - (diff / p.target_price)))
        check_date = p.end_date
        while check_date.weekday() > 4: check_date += timedelta(days=1)
        if today >= check_date:
            try:
                history = yf.download(p.symbol, start=check_date, end=check_date + timedelta(days=2), progress=False)
                if not history.empty:
                    val = float(history['Close'].iloc[0])
                    p.final_price = val
                    p.finalized_date = check_date
                    p.current_price = val
                    p.status = "VALIDATED"
                    finalized += 1
            except:
                pass
        updates += 1
        session.add(p)
    session.commit()
    logger.info(f"✅ Scheduler: Job Complete. Updated: {updates}, Finalized: {finalized}")
    return {"status": "success", "updated": updates, "finalized": finalized}


@app.post("/scheduler/cleanup")
async def cleanup_predictions(request: Request, signature: str = Header(None, alias="Upstash-Signature"),
                              session: Session = Depends(get_session)):
    logger.info("🧹 Scheduler: Starting Cleanup Job")
    if settings.QSTASH_CURRENT_SIGNING_KEY:
        try:
            receiver = Receiver(current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
                                next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY)
            body = await request.body()
            receiver.verify(body.decode("utf-8"), signature)
        except:
            raise HTTPException(status_code=401, detail="Invalid Signature")

    cutoff = date.today() - timedelta(days=30)
    zombies = session.exec(select(Prediction).where(Prediction.final_price == 0.0, Prediction.end_date < cutoff)).all()
    count = len(zombies)
    for z in zombies: session.delete(z)
    session.commit()
    logger.info(f"✅ Scheduler: Cleanup Complete. Deleted {count} stale records.")
    return {"status": "success", "deleted_zombies": count}


@app.get("/history/{symbol}")
async def get_history(symbol: str, start: str, end: str):
    logger.info(f"📜 History Request: {symbol} ({start} to {end})")
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        today = date.today()
        if start_date >= today: return [{"date": start, "price": 0, "message": "New prediction."}]
        df = yf.download(symbol, start=start, end=end, progress=False)
        if df.empty: return []
        history = []
        for index, row in df.iterrows():
            price = row['Close']
            if pd.isna(price): continue
            history.append({"date": index.strftime("%Y-%m-%d"), "price": float(price)})
        return history
    except Exception as e:
        logger.error(f"❌ History fetch failed for {symbol}: {e}")
        return []


@app.post("/watchlist")
async def add_to_watchlist(
        item: WatchlistAddRequest,
        force: bool = False,
        session: Session = Depends(get_session),
        user_id: str = Depends(get_current_user)
):
    normalized_symbol = item.symbol.strip().upper()
    logger.info(f"📝 Watchlist Add Request: User={user_id} | Symbol={normalized_symbol} | Force={force}")

    statement = select(Prediction).where(
        Prediction.symbol == normalized_symbol,
        Prediction.user_id == user_id
    )
    existing = session.exec(statement).first()

    if existing:
        if not force:
            logger.warning(f"⚠️ Duplicate blocked: {normalized_symbol} already exists for user.")
            raise HTTPException(
                status_code=409,
                detail="Prediction already exists. Confirmation required."
            )

        logger.info(f"🔄 Overwriting prediction for {normalized_symbol}")
        existing.target_price = item.target_price
        existing.end_date = item.end_date
        existing.initial_price = item.initial_price
        existing.created_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"status": "updated", "message": "Prediction overwritten"}

    else:
        logger.info(f"✨ Creating new prediction for {normalized_symbol}")
        pred = Prediction(
            user_id=user_id,
            symbol=normalized_symbol,
            initial_price=item.initial_price,
            target_price=item.target_price,
            end_date=item.end_date,
            confidence_score=0.0
        )
        session.add(pred)
        session.commit()
        return {"status": "created", "message": "Added to watchlist"}


@app.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    logger.info(f"🧠 Deep Sentiment Analysis for: {symbol}")

    # 1. Fetch Dynamic Data (Google News RSS)
    rss_news = market_brain.get_company_rss(symbol)
    logger.info(f"   📰 Source: Google News (RSS) | Found: {len(rss_news)} articles")

    # 2. Fetch Social Sentiment (Reddit)
    reddit_news = market_brain.analyze_reddit(symbol)
    logger.info(f"   🤖 Source: Reddit | Found: {len(reddit_news)} threads")

    # 3. Fetch Macro Economic Data (FRED)
    macro_data = market_brain.get_macro_data()
    logger.info(f"   🇺🇸 Source: FRED (Macro) | Status: {'✅ Loaded' if macro_data else '❌ Unavailable'}")

    # --- 3.5 CONVERT MACRO DATA TO FEED ITEMS ---
    macro_messages = []
    if macro_data:
        ts = datetime.now().isoformat()

        # Inflation Card
        if "inflation_rate" in macro_data and not pd.isna(macro_data["inflation_rate"]):
            val = macro_data['inflation_rate']
            sent = "negative" if val > 3.0 else "neutral"
            macro_messages.append({
                "id": "fred-inflation",
                "text": f"US Inflation Rate (CPI) is currently {val:.2f}% (YoY).",
                "sentiment": sent,
                "type": "informative",
                "source": "Federal Reserve (FRED)",
                "url": "https://fred.stlouisfed.org/series/CPIAUCSL",
                "timestamp": ts,
                "is_lawsuit": False
            })

        # Fed Funds Card
        if "fed_funds_rate" in macro_data and not pd.isna(macro_data["fed_funds_rate"]):
            val = macro_data['fed_funds_rate']
            macro_messages.append({
                "id": "fred-rates",
                "text": f"Federal Funds Interest Rate is currently {val:.2f}%.",
                "sentiment": "neutral",
                "type": "informative",
                "source": "Federal Reserve (FRED)",
                "url": "https://fred.stlouisfed.org/series/FEDFUNDS",
                "timestamp": ts,
                "is_lawsuit": False
            })

        # GDP Card
        if "gdp_growth" in macro_data and not pd.isna(macro_data["gdp_growth"]):
            val = macro_data['gdp_growth']
            macro_messages.append({
                "id": "fred-gdp",
                "text": f"Latest US GDP figure stands at ${val:,.0f} Billions.",
                "sentiment": "positive",
                "type": "informative",
                "source": "Federal Reserve (FRED)",
                "url": "https://fred.stlouisfed.org/series/GDP",
                "timestamp": ts,
                "is_lawsuit": False
            })

    # 4. Merge News for Frontend Compatibility
    all_messages = rss_news + reddit_news + macro_messages

    return {
        "symbol": symbol,
        "messages": all_messages,
        "economic_context": macro_data
    }

@app.get("/market/data/{symbol}", response_model=RealTimeMarketData)
async def get_market_data(symbol: str):
    logger.info(f"🪙 Market Data Request: {symbol}")
    try:
        engine = PredictionEngine(data_client=alpaca_data, trading_client=alpaca_trading)
        data = engine.fetch_real_time_data(symbol)
        return data
    except Exception as e:
        logger.error(f"❌ Market Data Endpoint Failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@app.post("/auth/check")
async def validate_user_email(request: UserCheckRequest):
    logger.info(f"🛡️ Auth: Checking existence for {request.email}")

    # 1. Check if user exists in Supabase Admin
    exists = check_user_exists(request.email)

    if exists:
        logger.warning(f"🚫 Auth: Signup blocked. Email {request.email} already exists.")
        return {"exists": True, "message": "User already exists"}

    logger.info(f"✅ Auth: Email {request.email} is available.")
    return {"exists": False, "message": "Email available"}


@app.get("/health")
def health_check():
    return {"status": "running", "service": "Sentient API"}


@app.get("/debug-log")
def debug_log_test():
    logger.info("ℹ️ LOGGER CHECK: If you see this, logging is working correctly.")
    return {"message": "Check your terminal now"}