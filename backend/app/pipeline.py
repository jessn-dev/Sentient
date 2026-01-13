import pandas as pd
from typing import List
from .schemas import MarketRecord

class DataCleaner:
    @staticmethod
    def clean(records: List[MarketRecord]) -> pd.DataFrame:
        """
        Converts Pydantic models to a Prophet-ready DataFrame.
        1. Imputes missing weekends (ffill).
        2. Renames columns to 'ds' and 'y'.
        """
        if not records:
            raise ValueError("No historical data provided for cleaning")

        # 1. Convert to DataFrame
        data = [r.model_dump() for r in records]
        df = pd.DataFrame(data)

        # 2. Setup Index & Handle Timezones
        # Prophet requires naive datetimes (no UTC/-05:00 info)
        df['ds'] = pd.to_datetime(df['timestamp'])
        if df['ds'].dt.tz is not None:
            df['ds'] = df['ds'].dt.tz_localize(None)

        df = df.sort_values('ds').set_index('ds')

        # 3. Reindex to Daily Frequency (exposing gaps)
        full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
        df = df.reindex(full_idx)

        # 4. Impute Missing Data (Forward Fill)
        df['close'] = df['close'].ffill()

        # 5. Format for Prophet
        df = df.reset_index().rename(columns={'index': 'ds', 'close': 'y'})

        # Ensure numeric type strictly
        df['y'] = pd.to_numeric(df['y'])

        return df[['ds', 'y']].dropna()