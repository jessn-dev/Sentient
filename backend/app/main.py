import json
import redis
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import StockRequest, PredictionResponse
from .providers import DataProvider
from .engine import PredictionEngine

# 1. Initialize FastAPI App (MUST come before routes)
app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# 2. CORS Setup (Allow Next.js Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Initialize Redis
# We use decode_responses=True so we get Strings instead of Bytes
try:
    cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logging.warning(f"Redis connection failed: {e}. Caching will be disabled.")
    cache = None

# --- ROUTES ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/predict", response_model=PredictionResponse)
async def predict_stock(request: StockRequest):
    """
    Real Data Pipeline:
    1. Check Redis Cache
    2. Ingestion (Alpaca API)
    3. Forecasting (Prophet 1.2)
    4. Save to Cache
    """
    symbol = request.symbol.upper()
    cache_key = f"prediction_v1:{symbol}"

    # 1. CHECK CACHE (If Redis is available)
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                print(f"✅ Cache Hit for {symbol}")
                return PredictionResponse.model_validate_json(cached_data)
        except Exception as e:
            print(f"Redis Error: {e}")

    print(f"⚡ Cache Miss for {symbol}. Fetching new data...")

    try:
        # 2. FETCH & PREDICT
        provider = DataProvider()
        data_packet = provider.fetch_data(symbol)

        engine = PredictionEngine()
        result = engine.predict(request, data_packet["history"], data_packet["info"])

        # 3. SAVE TO CACHE (Expire in 1 hour = 3600 seconds)
        if cache:
            cache.set(cache_key, result.model_dump_json(), ex=3600)

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Prediction Error")