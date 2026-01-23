from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Dict
from qstash import Receiver
from datetime import datetime, timedelta, date
import time
import yfinance as yf
import os
import pandas as pd
from app.database import create_db_and_tables, Prediction, get_session
from app.engine import PredictionEngine
from app.schemas import StockRequest, PredictionResponse, MarketMoversResponse, WatchlistAddRequest, WatchlistPerformanceItem
from app.auth import get_current_user
from app.config import settings
from contextlib import asynccontextmanager

# --- ALPACA IMPORTS ---
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest
from alpaca.trading.client import TradingClient

PRICE_CACHE: Dict[str, Dict] = {}
CACHE_TTL = 300

ALPACA_KEY = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")

alpaca_data = None
alpaca_trading = None

if ALPACA_KEY and ALPACA_SECRET:
    try:
        alpaca_data = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        # Initialize Trading Client for Asset Details (Company Names)
        alpaca_trading = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
        print("✅ [INIT] Alpaca Clients Connected")
    except Exception as e:
        print(f"⚠️ [INIT] Alpaca Init Failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_live_prices(symbols: List[str]) -> Dict[str, float]:
    current_time = time.time()
    prices = {}
    missing = []
    for sym in symbols:
        cached = PRICE_CACHE.get(sym)
        if cached and (current_time - cached['timestamp'] < CACHE_TTL):
            prices[sym] = cached['price']
        else: missing.append(sym)
    if not missing: return prices

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
        except: pass

    if missing:
        try:
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
                        except: pass
        except: pass
    return prices

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: StockRequest):
    try:
        # Pass BOTH clients
        engine = PredictionEngine(data_client=alpaca_data, trading_client=alpaca_trading)
        return engine.predict(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/market/movers", response_model=MarketMoversResponse)
async def get_movers():
    return PredictionEngine(data_client=alpaca_data, trading_client=alpaca_trading).get_market_movers()

@app.post("/watchlist")
async def add_to_watchlist(item: WatchlistAddRequest, session: Session = Depends(get_session),
                           user_id: str = Depends(get_current_user)):
    statement = select(Prediction).where(Prediction.symbol == item.symbol, Prediction.user_id == user_id)
    existing = session.exec(statement).first()

    if existing:
        existing.target_price = item.target_price
        existing.end_date = item.end_date
        existing.initial_price = item.initial_price
        existing.final_price = 0.0  # Reset final price
        existing.created_at = datetime.utcnow()
        session.add(existing)
    else:
        pred = Prediction(
            user_id=user_id,
            symbol=item.symbol,
            initial_price=item.initial_price,
            target_price=item.target_price,
            end_date=item.end_date,
            confidence_score=0.0
        )
        session.add(pred)

    session.commit()
    return {"status": "success"}


@app.get("/watchlist/performance", response_model=List[WatchlistPerformanceItem])
async def get_watchlist_performance(session: Session = Depends(get_session), user_id: str = Depends(get_current_user)):
    predictions = session.exec(select(Prediction).where(Prediction.user_id == user_id)).all()
    if not predictions: return []
    today_dt = date.today()
    active_symbols = []

    def get_next_market_day(d: date) -> date:
        while d.weekday() > 4: d += timedelta(days=1)
        return d

    for p in predictions:
        final_price = p.final_price if p.final_price is not None else 0.0
        check_date = get_next_market_day(p.end_date)
        if final_price == 0.0 and today_dt <= check_date: active_symbols.append(p.symbol)

    live_prices = get_live_prices(list(set(active_symbols))) if active_symbols else {}
    results = []

    for p in predictions:
        final_price = p.final_price if p.final_price is not None else 0.0
        current_val = 0.0
        is_finalized = False
        target_final_date = get_next_market_day(p.end_date)

        if final_price > 0.0:
            current_val = final_price
            is_finalized = True
        elif today_dt >= target_final_date:
            try:
                hist = yf.download(p.symbol, start=target_final_date, end=target_final_date + timedelta(days=2),
                                   progress=False)
                if not hist.empty:
                    val = float(hist['Close'].iloc[0])
                    p.final_price = val
                    p.finalized_date = target_final_date
                    current_val = val
                    session.add(p);
                    session.commit();
                    session.refresh(p)
                    is_finalized = True
                else:
                    current_val = p.target_price
            except:
                current_val = p.target_price
        else:
            current_val = live_prices.get(p.symbol, p.initial_price)
            if current_val == 0.0: current_val = p.initial_price

        diff = abs(p.target_price - current_val)
        accuracy = max(0, 100 * (1 - (diff / p.target_price))) if p.target_price else 0
        status = "In Progress"
        if is_finalized:
            if current_val >= p.target_price:
                status = "✅ SUCCESS"
            elif accuracy > 95:
                status = "⏱️ EXPIRED (Close)"
            else:
                status = "❌ FAILED"
        else:
            if current_val >= p.target_price:
                status = "Target Hit 🎯"
            elif accuracy > 95:
                status = "Very Close 🔥"
            elif accuracy < 80:
                status = "Off Track ⚠️"

        results.append(WatchlistPerformanceItem(
            id=p.id, symbol=p.symbol, initial_price=p.initial_price, target_price=p.target_price,
            current_price=current_val, final_price=final_price if final_price > 0 else None,
            end_date=p.end_date, finalized_date=p.finalized_date, created_at=p.created_at,
            accuracy_score=round(accuracy, 1), status=status
        ))
    return results


@app.post("/scheduler/validate")
async def validate_predictions(request: Request, signature: str = Header(None, alias="Upstash-Signature"),
                               session: Session = Depends(get_session)):
    if settings.QSTASH_CURRENT_SIGNING_KEY:
        try:
            receiver = Receiver(current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
                                next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY)
            body = await request.body()
            receiver.verify(body.decode("utf-8"), signature)
        except:
            raise HTTPException(status_code=401, detail="Invalid QStash Signature")
    predictions = session.exec(select(Prediction).where(Prediction.final_price == 0.0)).all()
    if not predictions: return {"status": "success"}
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
    return {"status": "success", "updated": updates, "finalized": finalized}


@app.post("/scheduler/cleanup")
async def cleanup_predictions(request: Request, signature: str = Header(None, alias="Upstash-Signature"),
                              session: Session = Depends(get_session)):
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
    return {"status": "success", "deleted_zombies": count}


@app.get("/history/{symbol}")
async def get_history(symbol: str, start: str, end: str):
    # (Same as above)
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
    except:
        return []


@app.post("/watchlist")
async def add_to_watchlist(item: WatchlistAddRequest, session: Session = Depends(get_session),
                           user_id: str = Depends(get_current_user)):
    # (Same as above)
    statement = select(Prediction).where(Prediction.symbol == item.symbol, Prediction.user_id == user_id)
    existing = session.exec(statement).first()
    if existing:
        existing.target_price = item.target_price
        existing.end_date = item.end_date
        existing.initial_price = item.initial_price
        existing.final_price = 0.0
        session.add(existing)
    else:
        pred = Prediction(user_id=user_id, symbol=item.symbol, initial_price=item.initial_price,
                          target_price=item.target_price, end_date=item.end_date, confidence_score=0.0)
        session.add(pred)
    session.commit()
    return {"status": "success"}