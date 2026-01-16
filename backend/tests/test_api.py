import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.models import Prediction

# --- TEST 1: HEALTH CHECK ---
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# --- TEST 2: AI PREDICTION (MOCKED) ---
# We mock DataProvider and PredictionEngine so we don't call real APIs
@patch("app.main.DataProvider")
@patch("app.main.PredictionEngine")
def test_predict_endpoint(MockEngine, MockProvider, client):
    # Setup Mocks
    mock_engine_instance = MockEngine.return_value
    mock_engine_instance.predict.return_value = MagicMock(
        symbol="AAPL",
        predicted_price_7d=150.0,
        confidence_score=0.9,
        explanation="Bullish trend"
    )

    payload = {"symbol": "AAPL", "period": "2y"}
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["predicted_price_7d"] == 150.0

# --- TEST 3: DATABASE SAVE & OVERWRITE LOGIC ---
def test_save_prediction_workflow(client):
    # Data for a prediction
    payload = {
        "user_id": "test_user",
        "symbol": "TSLA",
        "current_price": 100.0,
        "predicted_price": 120.0,
        "confidence_score": 0.85,
        "target_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "overwrite": False
    }

    # A. First Save (Should Succeed)
    res1 = client.post("/predict/save", json=payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "saved"

    # B. Second Save (Should Fail - Conflict)
    res2 = client.post("/predict/save", json=payload)
    assert res2.status_code == 409  # Conflict!
    assert "active forecast" in res2.json()["detail"]

    # C. Third Save (With Overwrite=True - Should Succeed)
    payload["overwrite"] = True
    res3 = client.post("/predict/save", json=payload)
    assert res3.status_code == 200
    assert res3.json()["status"] == "saved"

