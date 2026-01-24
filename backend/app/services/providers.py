import pandas as pd
import yfinance as yf
import logging
import time
from datetime import datetime, timedelta
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment

logger = logging.getLogger(__name__)


class DataProvider:
    # Cache Configuration
    _HISTORY_CACHE = {}
    _CACHE_TTL = 3600  # 1 Hour

    def __init__(self, alpaca_client=None):
        self.alpaca = alpaca_client
        if self.alpaca:
            logger.info("✅ [PROVIDER] Alpaca Client Initialized")
        else:
            logger.warning("⚠️ [PROVIDER] No Alpaca Client. Running in Fallback Mode (Yahoo Only).")

    def fetch_history(self, symbol: str, days: int = 730):
        symbol = symbol.upper()
        alpaca_symbol = symbol.replace('-', '.')

        # 1. CACHE CHECK
        current_time = time.time()
        cache_key = f"{symbol}_{days}"
        cached_entry = DataProvider._HISTORY_CACHE.get(cache_key)

        if cached_entry:
            data, source, timestamp = cached_entry
            if current_time - timestamp < DataProvider._CACHE_TTL:
                logger.info(f"⚡ [HISTORY] Using Cached Data for {symbol} ({source})")
                return data.copy(), source

        # 2. ATTEMPT 1: ALPACA (With Retry Logic)
        if self.alpaca:
            logger.info(f"🔌 [HISTORY] Fetching Alpaca data for {alpaca_symbol}...")

            # ✅ RETRY LOGIC: Try 3 times before failing
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    end_dt = datetime.now()
                    start_dt = end_dt - timedelta(days=days)

                    req = StockBarsRequest(
                        symbol_or_symbols=alpaca_symbol,
                        timeframe=TimeFrame.Day,
                        start=start_dt,
                        end=end_dt,
                        adjustment=Adjustment.RAW,
                        feed='iex'
                    )

                    # This is the call that might fail
                    bars = self.alpaca.get_stock_bars(req).df

                    if not bars.empty:
                        logger.info(f"   ✅ [HISTORY] Alpaca returned {len(bars)} rows")
                        bars = bars.reset_index()
                        df = pd.DataFrame({
                            'ds': bars['timestamp'].dt.tz_localize(None),
                            'y': bars['close']
                        })

                        # Save to Cache & Return
                        DataProvider._HISTORY_CACHE[cache_key] = (df, "Alpaca (IEX)", current_time)
                        return df, "Alpaca (IEX)"

                    # If empty, break loop to try fallback logic (no error, just no data)
                    break

                except Exception as e:
                    logger.warning(f"   ⚠️ [HISTORY] Alpaca Attempt {attempt}/{max_retries} Failed: {e}")
                    if attempt < max_retries:
                        time.sleep(1)  # Wait 1s before retrying
                    else:
                        logger.error(f"   ❌ [HISTORY] Alpaca Failed after {max_retries} attempts.")

        # 3. ATTEMPT 2: YAHOO (Fallback)
        try:
            logger.info(f"⚠️ [HISTORY] Fallback: Fetching Yahoo data for {symbol}...")
            df = yf.download(symbol, period="2y", progress=False, threads=False)

            if df.empty:
                raise ValueError("Yahoo returned empty data.")

            df = df.reset_index()
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    df.columns = df.columns.get_level_values(0)
                except:
                    pass

            clean_df = pd.DataFrame({
                'ds': pd.to_datetime(df['Date']).dt.tz_localize(None),
                'y': df['Close']
            })
            logger.info(f"   ✅ [HISTORY] Yahoo returned {len(clean_df)} rows")

            DataProvider._HISTORY_CACHE[cache_key] = (clean_df, "Yahoo", current_time)
            return clean_df, "Yahoo"

        except Exception as e:
            logger.critical(f"❌ [FATAL] All data providers failed for {symbol}: {e}")
            raise ValueError(f"All data providers failed for {symbol}: {e}")