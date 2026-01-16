import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from .config import settings

# Initialize Logger
logger = logging.getLogger("uvicorn")

class DataProvider:
    def __init__(self):
        self.api_key = settings.ALPACA_API_KEY
        self.secret_key = settings.ALPACA_SECRET_KEY
        self.client = StockHistoricalDataClient(self.api_key, self.secret_key)

    def fetch_data(self, symbol: str, days: int = 365 * 2):
        """
        Waterfall Strategy:
        1. Try Alpaca SIP (Best Data, requires paid sub).
        2. If 403/Forbidden, Try Alpaca IEX (Good Data, Free).
        3. If all Alpaca fails, Fallback to Yahoo Finance (Slower, rate limits).
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # --- ATTEMPT 1 & 2: ALPACA (SIP -> IEX) ---
        try:
            # Step 1: Default to SIP (Best for paid users)
            # Note: We use a nested try/except to handle the specific "Forbidden" error
            try:
                request_params = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    limit=1000,
                    feed=DataFeed.SIP # Explicitly request SIP first
                )
                bars = self.client.get_stock_bars(request_params)

            except Exception as e:
                # Check if it's a subscription error
                if "subscription does not permit" in str(e) or "Forbidden" in str(e):
                    logger.warning(f"⚠️ Alpaca SIP feed forbidden for {symbol}. Falling back to IEX.")

                    # Step 2: Fallback to IEX (Free Tier)
                    request_params = StockBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=TimeFrame.Day,
                        start=start_date,
                        limit=1000,
                        feed=DataFeed.IEX # Fallback to IEX
                    )
                    bars = self.client.get_stock_bars(request_params)
                else:
                    raise e # Re-raise if it's a different error (like network down)

            # Process Alpaca Data
            if not bars.data:
                raise ValueError("Alpaca returned empty data.")

            df = bars.df.loc[symbol]
            df = df.reset_index()

            # Rename columns to match our engine's expectations
            df = df.rename(columns={
                "timestamp": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            })

            # Ensure Date is timezone-naive for Prophet
            if df['Date'].dt.tz is not None:
                df['Date'] = df['Date'].dt.tz_localize(None)

            # Fetch basic info (Sector/Industry) - Yahoo is best for this metadata even if we use Alpaca for price
            info = self.fetch_info_yahoo(symbol)

            return {"history": df, "info": info}

        except Exception as e:
            logger.error(f"❌ Alpaca Failed ({str(e)}), falling back to Yahoo...")
            return self.fetch_with_yahoo(symbol, start_date, end_date)

    def fetch_with_yahoo(self, symbol: str, start_date, end_date):
        """Last Resort: Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)

            # Fetch History
            df = ticker.history(start=start_date, end=end_date)
            if df.empty:
                raise ValueError("Yahoo Finance returned no data.")

            df = df.reset_index()

            # Ensure Date is timezone-naive
            if 'Date' in df.columns and df['Date'].dt.tz is not None:
                df['Date'] = df['Date'].dt.tz_localize(None)

            # Fetch Info
            info = {
                "sector": ticker.info.get("sector", "Unknown"),
                "industry": ticker.info.get("industry", "Unknown")
            }

            return {"history": df, "info": info}

        except Exception as e:
            logger.error(f"❌ All Data Sources Failed: {e}")
            raise RuntimeError(f"Could not fetch data for {symbol} from any source.")

    def fetch_info_yahoo(self, symbol: str):
        """Helper to get just metadata from Yahoo"""
        try:
            t = yf.Ticker(symbol)
            return {
                "sector": t.info.get("sector", "Unknown"),
                "industry": t.info.get("industry", "Unknown")
            }
        except:
            return {"sector": "Unknown", "industry": "Unknown"}