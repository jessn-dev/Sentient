import pytest
from unittest.mock import MagicMock, patch
from datetime import date
import pandas as pd
from app.models import Prediction


# --- TEST 1: PREDICTION ENDPOINT ---
@patch("app.main.PredictionEngine")
def test_predict_endpoint(MockEngine, client):
    """
    Test POST /predict with full schema compliance.
    """
    # 1. Setup Mock
    mock_instance = MockEngine.return_value
    mock_instance.predict.return_value = {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corp",  # <--- Added
        "tv_symbol": "NASDAQ:NVDA",  # <--- Added
        "current_price": 500.0,
        "predicted_price": 550.0,
        "confidence_score": 0.85,
        "explanation": "Bullish momentum detected.",
        "forecast_date": "2025-12-31"
    }

    # 2. Call API
    payload = {"symbol": "NVDA", "days": 7}
    response = client.post("/predict", json=payload)

    # 3. Verify
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert data["company_name"] == "NVIDIA Corp"


# --- TEST 2: WATCHLIST (Database Logic) ---
def test_watchlist_add(client, session):
    """
    Test POST /watchlist saves to the DB with user_id.
    """
    payload = {
        "user_id": "user_123",  # Required by DB
        "symbol": "TSLA",
        "initial_price": 200.0,
        "target_price": 250.0,
        "end_date": str(date.today())
    }

    response = client.post("/watchlist", json=payload)
    assert response.status_code == 200, response.text

    # Verify DB persistence
    from sqlmodel import select
    # Check that we saved it with the correct user_id
    prediction = session.exec(
        select(Prediction).where(Prediction.symbol == "TSLA")
    ).first()

    assert prediction is not None
    assert prediction.target_price == 250.0
    assert str(prediction.user_id) == "user_123"


# --- TEST 3: HISTORY (Yahoo Mock) ---
@patch("app.main.yf.download")
def test_history_endpoint(mock_download, client):
    """
    Test GET /history with Pandas mocking.
    """
    # 1. Create Fake DataFrame
    dates = pd.date_range(start="2024-01-01", periods=2)
    mock_df = pd.DataFrame({"Close": [100.0, 105.0]}, index=dates)
    mock_download.return_value = mock_df

    # 2. Call API
    response = client.get("/history/AAPL?start=2024-01-01&end=2024-01-03")

    # 3. Verify
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["price"] == 100.0


# --- TEST 4: MARKET MOVERS ---
@patch("app.main.PredictionEngine")
def test_market_movers(MockEngine, client):
    """Test GET /market/movers with full schema fields."""
    mock_instance = MockEngine.return_value
    mock_instance.get_market_movers.return_value = {
        "gainers": [{
            "symbol": "AMD",
            "price": 100.0,
            "change_pct": 5.2,
            "volume": "1500000"
        }],
        "losers": [],
        "active": []
    }

    response = client.get("/market/movers")
    assert response.status_code == 200, response.text
    assert response.json()["gainers"][0]["change_pct"] == 5.2