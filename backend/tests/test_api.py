from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from app.models import Prediction

# Note: We do NOT import TestClient or create engines here anymore.
# We rely on the 'client' and 'session' arguments provided by conftest.py

# --- TEST 1: HEALTH CHECK ---
def test_health_check(client):
    """Ensure the API is actually running."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# --- TEST 2: PREDICTION ENGINE (MOCKED) ---
@patch("app.main.cache")             # Injects MockRedis
@patch("app.main.DataProvider")      # Injects MockProvider
@patch("app.main.PredictionEngine")  # Injects MockEngine
def test_predict_endpoint(MockEngine, MockProvider, MockRedis, client): # <--- ADD client HERE
    """Test that /predict calls the engine and returns formatted JSON."""

    # 1. Setup Redis Mock (Cache Miss)
    MockRedis.get.return_value = None

    # 2. Setup Prediction Engine Mock
    mock_engine_instance = MockEngine.return_value
    mock_engine_instance.predict.return_value = MagicMock(
        symbol="AAPL",
        predicted_price=150.0,
        confidence_score=0.85,
        explanation="Bullish trend.",
        forecast_date=datetime.now(timezone.utc).date(),
        model_dump_json=lambda: '{"symbol": "AAPL"}'
    )

    # 3. Call the API using the 'client' fixture
    response = client.post("/predict", json={"symbol": "AAPL", "days": 7})

    # 4. Verify
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["predicted_price"] == 150.0

# --- TEST 3: SAVE PREDICTION & CONFLICT LOGIC ---
def test_save_prediction_flow(client, session):
    """Test saving a bet, hitting a conflict, and forcing overwrite."""

    payload = {
        "user_id": "test_user_1",
        "symbol": "TSLA",
        "current_price": 200.0,
        "predicted_price": 220.0,
        "confidence_score": 0.9,
        "target_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "overwrite": False
    }

    # 1. First Save (Should Succeed)
    response = client.post("/predict/save", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # 2. Second Save (Should Fail - Conflict)
    response = client.post("/predict/save", json=payload)
    assert response.status_code == 409

    # 3. Third Save (With Overwrite=True - Should Succeed)
    payload["overwrite"] = True
    response = client.post("/predict/save", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # Verify DB only has 1 active bet for TSLA
    from app.models import Prediction
    from sqlmodel import select  # <--- Ensure 'select' is imported

    # Use select(Prediction) instead of just Prediction
    bets = session.exec(select(Prediction)).all()

    assert len(bets) == 1
    assert bets[0].symbol == "TSLA"

# --- TEST 4: QSTASH VALIDATION ---
@patch("app.main.Receiver")
@patch("app.main.DataProvider")
def test_scheduler_validation(MockProvider, MockReceiver, client, session):
    """Test validation updates status."""

    MockReceiver.return_value.verify.return_value = True

    mock_snap = MagicMock()
    mock_snap.latest_trade.price = 220.0
    # Fallback to daily_bar if logic requires it
    mock_snap.daily_bar.close = 220.0
    MockProvider.return_value.client.get_stock_snapshot.return_value = {"TSLA": mock_snap}

    # Seed DB with an "Expired" Prediction
    expired_date = datetime.now(timezone.utc) - timedelta(days=1)
    bet = Prediction(
        user_id="test_user_1",
        symbol="TSLA",
        start_price=200.0,
        predicted_price=210.0,
        confidence_score=0.9,
        target_date=expired_date,
        status="ACTIVE"
    )
    session.add(bet)
    session.commit()

    headers = {"Upstash-Signature": "fake_sig"}
    response = client.post("/scheduler/validate", headers=headers)

    assert response.status_code == 200
    assert response.json()["validated_count"] == 1