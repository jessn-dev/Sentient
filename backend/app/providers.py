from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest # Added SnapshotRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from typing import Dict, Any

from .config import settings
from .schemas import MarketRecord

class DataProvider:
    def __init__(self):
        self.client = StockHistoricalDataClient(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY.get_secret_value()
        )

    def fetch_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches 2 years of daily bars + Snapshot info from Alpaca.
        """
        # 1. Fetch History (Bars)
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=730)
        )

        try:
            bars = self.client.get_stock_bars(request_params)
            df = bars.df

            if df.empty:
                raise ValueError(f"No data found for {symbol}")

            df = df.reset_index()
        except Exception as e:
            raise ValueError(f"Alpaca Error: {str(e)}")

        # 2. Map History
        records = []
        for _, row in df.iterrows():
            records.append(
                MarketRecord(
                    timestamp=row['timestamp'].to_pydatetime(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                )
            )

        # 3. Fetch Snapshot (Metadata)
        try:
            # FIX: Use correct attributes (.open instead of .o)
            snapshot_req = StockSnapshotRequest(symbol_or_symbols=symbol)
            snapshot = self.client.get_stock_snapshot(snapshot_req)[symbol]

            # Check if daily_bar exists to avoid crashes on new/inactive stocks
            if snapshot.daily_bar:
                info = {
                    "open_price": snapshot.daily_bar.open,   # <--- FIX: .open
                    "high_price": snapshot.daily_bar.high,   # <--- FIX: .high
                    "low_price": snapshot.daily_bar.low,     # <--- FIX: .low
                    "volume": snapshot.daily_bar.volume,     # <--- FIX: .volume
                    "market_cap": None,
                    "pe_ratio": None,
                    "fifty_two_week_high": None,
                    "fifty_two_week_low": None
                }
            else:
                info = {}

        except Exception as e:
            print(f"Snapshot Error (Non-fatal): {str(e)}")
            info = {}

        return {"history": records, "info": info}