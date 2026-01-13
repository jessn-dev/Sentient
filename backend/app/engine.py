import logging
from prophet import Prophet
from .schemas import StockRequest, PredictionResponse
from .pipeline import DataCleaner

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self):
        # Prophet 1.2 Configuration
        self.model = Prophet(
            daily_seasonality=True,
            yearly_seasonality=True,
            scaling='minmax' # New v1.2 feature
        )

    def predict(self, request: StockRequest, history: list) -> PredictionResponse:
        # 1. Clean Data
        df_train = DataCleaner.clean(history)

        # 2. Fit Model
        # Using the optimized CmdStan backend implicit in Prophet 1.2
        self.model.fit(df_train)

        # 3. Future Frame (7 Days)
        future = self.model.make_future_dataframe(periods=7)

        # 4. Predict
        forecast = self.model.predict(future)

        # 5. Extract Results
        latest_actual = df_train.iloc[-1]['y']
        prediction_row = forecast.iloc[-1]

        return PredictionResponse(
            symbol=request.symbol,
            current_price=float(latest_actual),
            predicted_price_7d=float(prediction_row['yhat']),
            confidence_score=0.85, # Placeholder for backtest score
            forecast_date=prediction_row['ds'].date()
        )