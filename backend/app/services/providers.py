import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment

logger = logging.getLogger(__name__)


class DataProvider:
    def __init__(self, alpaca_client=None):
        self.alpaca = alpaca_client
        if self.alpaca:
            logger.info("✅ [PROVIDER] Alpaca Client Initialized")
        else:
            logger.warning("⚠️ [PROVIDER] No Alpaca Client. Running in Fallback Mode (Yahoo Only).")

    def fetch_history(self, symbol: str, days: int = 730):
        symbol = symbol.upper()
        alpaca_symbol = symbol.replace('-', '.')

        # --- ATTEMPT 1: ALPACA ---
        if self.alpaca:
            logger.info(f"🔌 [HISTORY] Fetching Alpaca data for {alpaca_symbol}...")
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

                bars = self.alpaca.get_stock_bars(req).df

                if not bars.empty:
                    logger.info(f"   ✅ [HISTORY] Alpaca returned {len(bars)} rows")
                    bars = bars.reset_index()
                    df = pd.DataFrame({
                        'ds': bars['timestamp'].dt.tz_localize(None),
                        'y': bars['close']
                    })
                    return df, "Alpaca (IEX)"
            except Exception as e:
                logger.error(f"   ❌ [HISTORY] Alpaca Failed: {e}")

        # --- ATTEMPT 2: YAHOO ---
        try:
            logger.info(f"⚠️ [HISTORY] Fallback: Fetching Yahoo data for {symbol}...")
            df = yf.download(symbol, period="2y", progress=False)

            if df.empty:
                raise ValueError("Yahoo returned empty data.")

            df = df.reset_index()
            # Handle MultiIndex columns (common in new yfinance versions)
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
            return clean_df, "Yahoo"

        except Exception as e:
            logger.critical(f"❌ [FATAL] All data providers failed for {symbol}: {e}")
            raise ValueError(f"All data providers failed for {symbol}: {e}")