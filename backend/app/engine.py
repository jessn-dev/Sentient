import pandas as pd
from prophet import Prophet
from datetime import datetime, timezone
from sklearn.metrics import mean_absolute_error
from .schemas import StockRequest, PredictionResponse

class PredictionEngine:
    def predict(self, request: StockRequest, historical_data: pd.DataFrame, info: dict) -> PredictionResponse:

        # --- FIX 1: Robust Empty Check ---
        # We use .empty instead of "if historical_data:" to avoid the Ambiguous Truth error
        if historical_data is None or historical_data.empty:
            raise ValueError("Prediction Error: No historical data provided for analysis.")

        # --- FIX 2: Data Cleaning ---
        # Prophet requires specific column names: 'ds' (Date) and 'y' (Target Value)
        df = historical_data.copy()

        # Ensure we have the right columns from our Provider
        # We expect: Date, Open, High, Low, Close, Volume
        if 'Date' not in df.columns or 'Close' not in df.columns:
            raise ValueError(f"Invalid Data Format. Columns found: {df.columns}")

        # Rename for Prophet
        df = df.rename(columns={'Date': 'ds', 'Close': 'y'})

        # Ensure 'ds' is timezone-naive (Prophet crashes with timezones)
        if df['ds'].dt.tz is not None:
            df['ds'] = df['ds'].dt.tz_localize(None)

        # --- FIX 3: Minimum Data Requirement ---
        # We need at least 20-30 data points to make a decent forecast
        if len(df) < 30:
            raise ValueError(f"Insufficient data points ({len(df)}) for forecasting. Need at least 30.")

        # --- MODEL TRAINING ---
        try:
            model = Prophet(daily_seasonality=True)
            model.fit(df)

            # Create Future DataFrame
            future = model.make_future_dataframe(periods=request.days)
            forecast = model.predict(future)

            # Extract Results
            # Get the last row (Target Date)
            future_prediction = forecast.iloc[-1]['yhat']

            # Get Today's Price (Last known real data point)
            current_price = df.iloc[-1]['y']

            # --- SCORING LOGIC ---
            # Calculate simple confidence based on historical fit
            # (In a real app, you'd use Cross-Validation here)
            historical_pred = forecast.iloc[:len(df)]['yhat']
            mae = mean_absolute_error(df['y'], historical_pred)

            # Normalize score (0.0 to 1.0). Lower MAE = Higher Confidence.
            # If error is > 10% of price, confidence drops significantly.
            error_ratio = mae / current_price
            confidence = max(0.0, 1.0 - (error_ratio * 5)) # Aggressive penalty

            # Trend Explanation
            trend = "Bullish" if future_prediction > current_price else "Bearish"
            pct_change = ((future_prediction - current_price) / current_price) * 100

            explanation = (
                f"{info.get('sector', 'Stock')} sector analysis suggests a {trend} trend. "
                f"Model predicts a move from ${current_price:.2f} to ${future_prediction:.2f} "
                f"({pct_change:+.2f}%) over the next {request.days} days."
            )

            return PredictionResponse(
                symbol=request.symbol.upper(),
                current_price=round(current_price, 2),
                predicted_price_7d=round(future_prediction, 2),
                forecast_date=forecast.iloc[-1]['ds'].date(),
                confidence_score=round(confidence, 2),
                explanation=explanation
            )

        except Exception as e:
            raise ValueError(f"Model Training Failed: {str(e)}")
