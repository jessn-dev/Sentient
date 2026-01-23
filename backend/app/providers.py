import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment


class DataProvider:
    def __init__(self, alpaca_client=None):
        self.alpaca = alpaca_client

        if self.alpaca:
            print("✅ [PROVIDER] Alpaca Client Received")
        else:
            print("⚠️ [PROVIDER] No Alpaca Client Provided.")

    def fetch_history(self, symbol: str, days: int = 730):
        symbol = symbol.upper()
        alpaca_symbol = symbol.replace('-', '.')

        # --- ATTEMPT 1: ALPACA ---
        if self.alpaca:
            print(f"🔌 [HISTORY] Connecting to Alpaca for {alpaca_symbol}...")
            try:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=days)

                # NEW SYNTAX
                req = StockBarsRequest(
                    symbol_or_symbols=alpaca_symbol,
                    timeframe=TimeFrame.Day,
                    start=start_dt,
                    end=end_dt,
                    adjustment=Adjustment.RAW,
                    feed='iex'
                )

                # Get DataFrame directly
                bars = self.alpaca.get_stock_bars(req).df

                if not bars.empty:
                    print(f"   ✅ [HISTORY] Alpaca returned {len(bars)} rows")
                    bars = bars.reset_index()
                    df = pd.DataFrame({
                        'ds': bars['timestamp'].dt.tz_localize(None),
                        'y': bars['close']
                    })
                    return df, "Alpaca (IEX)"
            except Exception as e:
                print(f"   ❌ [HISTORY] Alpaca Failed: {e}")

        # --- ATTEMPT 2: YAHOO ---
        try:
            print(f"⚠️ [HISTORY] Using Yahoo Fallback for {symbol}...")
            df = yf.download(symbol, period="2y", progress=False)
            if df.empty: raise ValueError("Yahoo returned empty data.")
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
            return clean_df, "Yahoo"
        except Exception as e:
            raise ValueError(f"All data providers failed for {symbol}: {e}")