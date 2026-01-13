import yfinance as yf
from datetime import datetime
from typing import List
import pandas as pd
from .schemas import MarketRecord

class DataProvider:
    @staticmethod
    def fetch_history(symbol: str, period: str = "2y") -> List[MarketRecord]:
        """
        Fetches historical data from Yahoo Finance and maps it to our strict Pydantic model.
        """
        # 1. Fetch from Yahoo
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df.empty:
            raise ValueError(f"No data found for symbol '{symbol}'. It may be delisted or invalid.")

        records = []

        # 2. Iterate and Map (Pandas iterrows is slow for millions of rows, but fine for 700 days)
        for date_idx, row in df.iterrows():
            # Yahoo returns the Index as Timestamp/Datetime

            # 3. Handle potential NaN values (Yahoo sometimes has bad data days)
            if any(pd.isna(row[col]) for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
                continue

            records.append(
                MarketRecord(
                    timestamp=date_idx.to_pydatetime(), # Convert Pandas Timestamp to Python datetime
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
            )

        return records