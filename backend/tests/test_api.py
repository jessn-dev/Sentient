from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import date
from app.schemas import PredictionResponse, MarketMoversResponse, MoverItem


# ✅ HELPER: Create a Pydantic Object for Mocking
# This ensures main.py can access attributes like obj.predicted_price
def create_mock_prediction():
    return PredictionResponse(
        symbol="AAPL",
        company_name="Apple Inc.",
        tv_symbol="NASDAQ:AAPL",
        current_price=150.0,
        predicted_price=155.0,
        forecast_date=date.today(),
        confidence_score=85.0,
        explanation="Test explanation",
        technicals=None,
        sentiment=None,
        liquidity=None
    )


def test_predict_endpoint(client: TestClient):
    # ✅ FIX 2: Mock return_value must be an Object, not a Dict
    mock_response = create_mock_prediction()

    with patch("app.services.engine.PredictionEngine.predict", return_value=mock_response):
        response = client.post("/predict", json={"symbol": "AAPL", "days": 7})

        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["predicted_price"] == 155.0


def test_watchlist_add(client: TestClient):
    # This will now PASS because conftest.py creates the 'prediction' table
    payload = {
        "symbol": "TSLA",
        "initial_price": 200.0,
        "target_price": 250.0,
        "end_date": "2025-12-31"
    }
    response = client.post("/watchlist", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "created"


def test_market_movers(client: TestClient):
    # ✅ FIX 3: Mock Market Movers to avoid IndexError/Scraping issues
    mock_movers = MarketMoversResponse(
        gainers=[MoverItem(symbol="AMD", price=100, change_pct=5.0, volume="High")],
        losers=[MoverItem(symbol="INTC", price=30, change_pct=-5.0, volume="High")],
        active=[MoverItem(symbol="NVDA", price=400, change_pct=1.0, volume="High")]
    )

    with patch("app.services.engine.PredictionEngine.get_market_movers", return_value=mock_movers):
        response = client.get("/market/movers")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert len(data["gainers"]) > 0
        assert data["gainers"][0]["symbol"] == "AMD"