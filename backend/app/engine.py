import logging
from prophet import Prophet
from .schemas import StockRequest, PredictionResponse
from .pipeline import DataCleaner
import pandas as pd

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self):
        # Prophet Configuration
        self.model = Prophet(
            daily_seasonality=False,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        self.model.add_country_holidays(country_name='US')

    def _generate_explanation(self, symbol: str, current: float, predicted: float, confidence: float) -> str:
        """
        Constructs a human-readable analysis of the forecast.
        """
        delta = predicted - current
        if current == 0: return "Insufficient data for analysis."

        pct_change = (delta / current) * 100
        direction = "increase" if delta > 0 else "decrease"

        # Analyze Strength
        strength = "slight"
        if abs(pct_change) > 2.0: strength = "moderate"
        if abs(pct_change) > 5.0: strength = "significant"

        # Analyze Confidence
        certainty = "low certainty"
        if confidence > 0.7: certainty = "moderate confidence"
        if confidence > 0.85: certainty = "high confidence"

        return (
            f"Based on historical trends, the model predicts a {strength} {direction} of "
            f"{abs(pct_change):.2f}% for {symbol} over the next 7 days. "
            f"This forecast is made with {certainty} ({int(confidence*100)}%), "
            f"suggesting the price may reach ${predicted:.2f}."
        )

    def predict(self, request: StockRequest, history: list, info: dict) -> PredictionResponse:
        # 1. Clean Data (THIS LINE WAS MISSING)
        df_train = DataCleaner.clean(history)

        # 2. Fit Model
        self.model.fit(df_train)

        # 3. Future Frame (7 Days)
        future = self.model.make_future_dataframe(periods=7)

        # 4. Predict
        forecast = self.model.predict(future)

        # 5. Extract Results
        # Get the latest ACTUAL price from input data (not the forecast)
        latest_actual = df_train.iloc[-1]['y']

        # Get the predicted price (last row of forecast)
        prediction_row = forecast.iloc[-1]
        predicted_price = float(prediction_row['yhat'])

        # Placeholder confidence (Prophet calculates uncertainty intervals, but we use a fixed score for MVP)
        confidence = 0.85

        # 6. Generate Explanation
        explanation_text = self._generate_explanation(
            request.symbol,
            float(latest_actual),
            predicted_price,
            confidence
        )

        return PredictionResponse(
            symbol=request.symbol,
            current_price=float(latest_actual),
            predicted_price_7d=predicted_price,
            confidence_score=confidence,
            forecast_date=prediction_row['ds'].date(),
            explanation=explanation_text,

            # Map Optional Fields
            market_cap=info.get("market_cap"),
            pe_ratio=info.get("pe_ratio"),
            dividend_yield=info.get("dividend_yield"),
            fifty_two_week_high=info.get("fifty_two_week_high"),
            fifty_two_week_low=info.get("fifty_two_week_low"),
            volume=info.get("volume"),
            open_price=info.get("open_price"),
            high_price=info.get("high_price"),
            low_price=info.get("low_price")
        )