from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Dict
import time
from datetime import datetime, timedelta, date
import yfinance as yf
import os
import alpaca_trade_api as tradeapi

from .database import create_db_and_tables, Prediction, get_session
from .engine import PredictionEngine
from .schemas import StockRequest, PredictionResponse, MarketMoversResponse, WatchlistAddRequest, WatchlistPerformanceItem
from contextlib import asynccontextmanager

# --- CACHE SETUP ---
PRICE_CACHE: Dict[str, Dict] = {}
CACHE_TTL = 300  # 5 Minutes

# --- ALPACA SETUP ---
ALPACA_KEY = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")
ALPACA_URL = "https://paper-api.alpaca.markets"

alpaca = None
if ALPACA_KEY and ALPACA_SECRET:
    try:
        alpaca = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, ALPACA_URL, api_version='v2')
        print("✅ [INIT] Alpaca API Connected in Main")
    except Exception as e:
        print(f"⚠️ [INIT] Alpaca Init Failed: {e}")
else:
    print("⚠️ [INIT] Missing Alpaca Keys in Environment")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- BULK PRICE FETCHER ---
def get_live_prices(symbols: List[str]) -> Dict[str, float]:
    current_time = time.time()
    prices = {}
    missing = []

    # 1. Check Cache
    for sym in symbols:
        cached = PRICE_CACHE.get(sym)
        if cached and (current_time - cached['timestamp'] < CACHE_TTL):
            prices[sym] = cached['price']
        else:
            missing.append(sym)

    if not missing:
        return prices

    # 2. Fetch from Alpaca (Primary)
    if alpaca:
        # Normalization: BRK-B -> BRK.B
        alpaca_map = {sym.replace('-', '.'): sym for sym in missing}
        alpaca_request_syms = list(alpaca_map.keys())

        print(f"🔌 [LIVE] Connecting to Alpaca for: {alpaca_request_syms}")
        try:
            snapshots = alpaca.get_snapshots(alpaca_request_syms)
            for alpaca_sym, snapshot in snapshots.items():
                if snapshot and snapshot.latest_trade:
                    price = float(snapshot.latest_trade.price)
                    if price > 0:
                        # Map back: BRK.B -> BRK-B
                        orig_sym = alpaca_map.get(alpaca_sym, alpaca_sym)
                        prices[orig_sym] = price
                        PRICE_CACHE[orig_sym] = {"price": price, "timestamp": current_time}
                        if orig_sym in missing: missing.remove(orig_sym)
        except Exception as e:
            print(f"   ❌ Alpaca Bulk Fetch Error: {e}")

    # 3. Fetch from Yahoo (Backup - Only if small batch)
    if missing:
        # Prevent hitting rate limit with large batches
        if len(missing) > 5:
            print("   ⚠️ Batch too large for Yahoo fallback. Skipping.")
            return prices

        try:
            print(f"⚠️ [LIVE] Yahoo Fallback for: {missing}")
            data = yf.download(missing, period="1d", progress=False)['Close']

            if data.empty: return prices

            if len(missing) == 1:
                val = float(data.iloc[-1])
                prices[missing[0]] = val
                PRICE_CACHE[missing[0]] = {"price": val, "timestamp": current_time}
            else:
                curr_vals = data.iloc[-1]
                for sym in missing:
                    try:
                        val = float(curr_vals[sym])
                        prices[sym] = val
                        PRICE_CACHE[sym] = {"price": val, "timestamp": current_time}
                    except: pass
        except Exception as e:
            print(f"   ❌ Yahoo Fallback Error: {e}")

    return prices

# --- ENDPOINTS ---
@app.get("/history/{symbol}")
async def get_history(symbol: str, start: str, end: str):
    """
    Fetches daily closing prices between start and end date.
    """
    try:
        # 1. Validation: If start date is today or future, return empty immediately
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        today = date.today()

        if start_date >= today:
            return [{"date": start, "price": 0, "message": "New prediction: Chart data updates after market close."}]

        # 2. Fetch from Yahoo
        # We wrap this in a broad try/except because yfinance raises different errors
        # (YFPricesMissingError, ValueError, etc.) depending on the version.
        try:
            df = yf.download(symbol, start=start, end=end, progress=False)
        except Exception:
            return []

        if df.empty:
            return []

        history = []
        for index, row in df.iterrows():
            # Handle cases where 'Close' might be NaN
            price = row['Close']
            if pd.isna(price): continue

            history.append({
                "date": index.strftime("%Y-%m-%d"),
                "price": float(price)
            })

        return history

    except Exception as e:
        print(f"History Fetch Error for {symbol}: {e}")
        return []

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: StockRequest):
    try:
        # Inject Alpaca Client
        engine = PredictionEngine(alpaca_client=alpaca)
        return engine.predict(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/market/movers", response_model=MarketMoversResponse)
async def get_movers():
    # FIX: Inject Alpaca Client here too!
    return PredictionEngine(alpaca_client=alpaca).get_market_movers()

@app.post("/watchlist")
async def add_to_watchlist(item: WatchlistAddRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(Prediction).where(Prediction.symbol == item.symbol)).first()
    if existing:
        existing.target_price = item.target_price
        existing.end_date = item.end_date
        existing.initial_price = item.initial_price
        session.add(existing)
    else:
        pred = Prediction(symbol=item.symbol, initial_price=item.initial_price, target_price=item.target_price, end_date=item.end_date)
        session.add(pred)
    session.commit()
    return {"status": "success"}

@app.get("/watchlist/performance", response_model=List[WatchlistPerformanceItem])
async def get_watchlist_performance(session: Session = Depends(get_session)):
    predictions = session.exec(select(Prediction)).all()
    if not predictions: return []

    today_dt = date.today()
    active_symbols = []

    # Helper: Find next valid market day (skip weekends)
    def get_next_market_day(d: date) -> date:
        # 5=Saturday, 6=Sunday
        while d.weekday() > 4:
            d += timedelta(days=1)
        return d

    for p in predictions:
        # Determine the actual "Check Date"
        # If end_date is Sunday, check_date becomes Monday
        check_date = get_next_market_day(p.end_date)

        # If we haven't finalized yet, and today is NOT past the check date, it's active
        if p.final_price == 0.0 and today_dt <= check_date:
            active_symbols.append(p.symbol)

    live_prices = get_live_prices(list(set(active_symbols))) if active_symbols else {}

    results = []
    for p in predictions:
        current_val = 0.0
        is_finalized = False

        # Calculate the adjusted "Finalization Date" (Monday if weekend)
        target_final_date = get_next_market_day(p.end_date)

        # A. Already Finalized in DB
        if p.final_price > 0.0:
            current_val = p.final_price
            is_finalized = True

        # B. Needs Finalizing (Expired)
        # We only finalize if today is ON or AFTER the adjusted Monday date
        elif today_dt >= target_final_date:
            print(f"🔒 Finalizing {p.symbol} on {target_final_date} (Original End: {p.end_date})")
            try:
                # Fetch price for that specific adjusted date
                # We add a small buffer to 'end=' to ensure yfinance captures the day
                hist = yf.download(p.symbol, start=target_final_date, end=target_final_date + timedelta(days=2), progress=False)

                if not hist.empty:
                    p.final_price = float(hist['Close'].iloc[0])
                    p.finalized_date = target_final_date  # Save the actual date used
                    current_val = p.final_price
                    session.add(p); session.commit()
                    is_finalized = True
                else:
                    # Data might not be available yet (e.g. Monday morning pre-market)
                    # Use live price as temporary placeholder or fallback
                    current_val = p.target_price
            except Exception as e:
                print(f"Error finalizing: {e}")
                current_val = p.target_price

        # C. Active
        else:
            current_val = live_prices.get(p.symbol, p.initial_price)
            if current_val == 0.0: current_val = p.initial_price

        # --- STATUS LOGIC ---
        diff = abs(p.target_price - current_val)
        accuracy = max(0, 100 * (1 - (diff / p.target_price))) if p.target_price else 0

        status = "In Progress"
        if is_finalized:
            if current_val >= p.target_price: status = "✅ SUCCESS"
            elif accuracy > 95: status = "⏱️ EXPIRED (Close)"
            else: status = "❌ FAILED"
        else:
            if current_val >= p.target_price: status = "Target Hit 🎯"
            elif accuracy > 95: status = "Very Close 🔥"
            elif accuracy < 80: status = "Off Track ⚠️"

        results.append(WatchlistPerformanceItem(
            id=p.id,
            symbol=p.symbol,
            initial_price=p.initial_price,
            target_price=p.target_price,
            current_price=current_val,
            final_price=p.final_price if p.final_price > 0 else None,
            end_date=p.end_date,
            finalized_date=p.finalized_date, # Pass the adjusted date to frontend
            created_at=p.created_at,
            accuracy_score=round(accuracy, 1),
            status=status
        ))
    return results