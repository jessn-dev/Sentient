import random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .providers import DataProvider

from .schemas import StockRequest, PredictionResponse, MarketRecord
from .engine import PredictionEngine
from .config import settings

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# CORS Setup (Allow Next.js Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCK DATA GENERATOR (For Testing) ---
# def generate_mock_history(symbol: str) -> list[MarketRecord]:
#     """Generates 2 years of fake stock data for testing."""
#     records = []
#     price = 150.0
#     start_date = datetime.now() - timedelta(days=730)
#
#     for i in range(730):
#         current_date = start_date + timedelta(days=i)
#         # Random walk
#         change = random.uniform(-2.0, 2.5)
#         price += change
#         price = max(1.0, price) # Ensure no negative prices
#
#         records.append(MarketRecord(
#             timestamp=current_date,
#             open=price,
#             high=price + 1.0,
#             low=price - 1.0,
#             close=price,
#             volume=random.randint(1000, 50000)
#         ))
#     return records

@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: StockRequest):
    """
    Real Data Pipeline:
    1. Validation (Pydantic)
    2. Ingestion (Yahoo Finance)
    3. Cleaning (Pandas)
    4. Forecasting (Prophet 1.2)
    """
    try:
        # 1. Fetch REAL Data
        # We assume NASDAQ/NYSE are covered by default ticker symbols in Yahoo
        history = DataProvider.fetch_history(request.symbol)

        # 2. Run Engine (Prophet)
        engine = PredictionEngine()
        result = engine.predict(request, history)

        return result

    except ValueError as e:
        # Handle "Symbol not found" gracefully
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log the actual error for debugging
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Prediction Error")

# --- ROUTES ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: StockRequest):
    """
    Ingests a stock symbol, fetches (mock) history, and runs Prophet forecast.
    """
    try:
        # 1. Fetch Data (Mocked for now)
        # In production, call your external API here
        history = generate_mock_history(request.symbol)

        # 2. Run Engine
        engine = PredictionEngine()
        result = engine.predict(request, history)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))