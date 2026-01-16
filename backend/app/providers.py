import yfinance as yf
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from .config import settings

class DataProvider:
    def __init__(self):
        # 1. Handle API Keys (Fix for 'get_secret_value' error)
        # We check if the key is a string or a SecretStr object to be safe
        self.api_key = settings.ALPACA_API_KEY
        self.secret_key = settings.ALPACA_SECRET_KEY

        if hasattr(self.api_key, "get_secret_value"):
            self.api_key = self.api_key.get_secret_value()

        if hasattr(self.secret_key, "get_secret_value"):
            self.secret_key = self.secret_key.get_secret_value()

        # 2. Initialize Alpaca Client
        if self.api_key and self.secret_key:
            self.client = StockHistoricalDataClient(self.api_key, self.secret_key)
        else:
            self.client = None

    def fetch_data(self, symbol: str):
        """
        Fetches:
        1. Info from Yahoo Finance (free)
        2. History from Alpaca (fast/reliable) or fallback to Yahoo
        """
        data = {"history": [], "info": {}}

        # A. Fetch Basic Info (Yahoo)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            data["info"] = {
                "current_price": info.get("currentPrice") or info.get("regularMarketPreviousClose", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "sector": info.get("sector", "Unknown"),
                "summary": info.get("longBusinessSummary", "No summary available.")
            }
        except Exception as e:
            print(f"⚠️ Yahoo Info Failed: {e}")
            data["info"] = {"current_price": 0, "summary": "Data unavailable"}

        # B. Fetch History (Alpaca with Yahoo Fallback)
        if self.client:
            try:
                # Alpaca Logic
                end_dt = datetime.utcnow()
                start_dt = end_dt - timedelta(days=365*2) # 2 Years

                req = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
                    start=start_dt,
                    end=end_dt
                )
                bars = self.client.get_stock_bars(req)

                if symbol in bars:
                    df = bars[symbol].df
                    # Reset index so 'timestamp' is a column, not the index
                    df = df.reset_index()

                    for _, row in df.iterrows():
                        data["history"].append({
                            "date": row["timestamp"].strftime("%Y-%m-%d"),
                            "close": float(row["close"]),
                            "volume": int(row["volume"])
                        })
                    return data
            except Exception as e:
                print(f"⚠️ Alpaca Failed ({e}), falling back to Yahoo...")

        # C. Yahoo Fallback
        try:
            yf_hist = ticker.history(period="2y")
            yf_hist = yf_hist.reset_index()
            for _, row in yf_hist.iterrows():
                data["history"].append({
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
        except Exception as e:
            print(f"❌ All Data Sources Failed: {e}")

        return data