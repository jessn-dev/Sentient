import pandas as pd
import logging
from typing import List
from app.schemas import MarketRecord

logger = logging.getLogger(__name__)


class DataCleaner:
    @staticmethod
    def clean(records: List[MarketRecord]) -> pd.DataFrame:
        if not records:
            logger.error("❌ DataCleaner received empty records list")
            raise ValueError("No historical data provided for cleaning")

        logger.info(f"🧹 Cleaning {len(records)} raw market records...")

        # 1. Convert to DataFrame
        data = [r.model_dump() for r in records]
        df = pd.DataFrame(data)

        # 2. Setup Index & Handle Timezones
        df['ds'] = pd.to_datetime(df['timestamp'])
        if df['ds'].dt.tz is not None:
            df['ds'] = df['ds'].dt.tz_localize(None)

        df = df.sort_values('ds').set_index('ds')

        # 3. Reindex to Daily Frequency
        old_len = len(df)
        full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
        df = df.reindex(full_idx)

        # 4. Impute Missing Data
        df['close'] = df['close'].ffill()

        # 5. Format for Prophet
        df = df.reset_index().rename(columns={'index': 'ds', 'close': 'y'})
        df['y'] = pd.to_numeric(df['y'])

        final_df = df[['ds', 'y']].dropna()
        logger.info(f"✅ Data Cleaned: {old_len} -> {len(final_df)} rows (gaps filled)")

        return final_df