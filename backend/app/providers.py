import os
import pandas as pd
import yfinance as yf
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta

class DataProvider:
    def __init__(self, alpaca_client=None):
        self.alpaca = alpaca_client

        if self.alpaca:
            print("✅ [PROVIDER] Alpaca Client Received")
        else:
            print("⚠️ [PROVIDER] No Alpaca Client Provided. History will rely on Yahoo.")

    def fetch_history(self, symbol: str, days: int = 730):
        """
        Fetches historical data for Prophet.
        Strategy: Alpaca (IEX Feed) -> Yahoo Fallback
        """
        symbol = symbol.upper()
        # Alpaca Format: BRK.B, Yahoo Format: BRK-B
        alpaca_symbol = symbol.replace('-', '.')

        # --- ATTEMPT 1: ALPACA (IEX FEED) ---
        if self.alpaca:
            print(f"🔌 [HISTORY] Connecting to Alpaca (IEX Feed) for {alpaca_symbol}...")
            try:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=days)

                bars = self.alpaca.get_bars(
                    alpaca_symbol,
                    "1Day",
                    start=start_dt.strftime('%Y-%m-%d'),
                    end=end_dt.strftime('%Y-%m-%d'),
                    adjustment='raw',
                    feed='iex'
                ).df

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

        # --- ATTEMPT 2: YAHOO FINANCE (BACKUP) ---
        try:
            print(f"⚠️ [HISTORY] Using Yahoo Fallback for {symbol}...")
            df = yf.download(symbol, period="2y", progress=False)

            if df.empty:
                raise ValueError("Yahoo returned empty data.")

            df = df.reset_index()
            if isinstance(df.columns, pd.MultiIndex):
                try: df.columns = df.columns.get_level_values(0)
                except: pass

            clean_df = pd.DataFrame({
                'ds': pd.to_datetime(df['Date']).dt.tz_localize(None),
                'y': df['Close']
            })
            return clean_df, "Yahoo"
        except Exception as e:
            raise ValueError(f"All data providers failed for {symbol}: {e}")