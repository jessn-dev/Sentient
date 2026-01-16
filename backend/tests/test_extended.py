from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from app.main import derive_ticker
from app.models import Prediction
from sqlmodel import select

# We rely on 'client' and 'session' from conftest.py

def test_derive_ticker_logic():
    """Verify that keywords correctly map to tickers."""
    assert derive_ticker("Gold prices are rising", "DEFAULT") == "GLD"
    assert derive_ticker("Jerome Powell speaks today", "DEFAULT") == "SPY"

@patch("app.main.feedparser.parse")
def test_news_parsing(mock_parse, client):
    """Test that RSS entries are converted to NewsItem schema."""
    mock_entry = MagicMock()
    mock_entry.title = "NVIDIA stocks surge - Reuters"
    mock_entry.link = "http://test.com"
    # Valid time tuple
    mock_entry.published_parsed = (2024, 1, 1, 12, 0, 0, 0, 0, 0)

    mock_parse.return_value.entries = [mock_entry]

    response = client.get("/news/NVDA")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["related_ticker"] == "NVDA"

@patch("app.main.DataProvider")
def test_quote_fallback_logic(MockProvider, client):
    """Test that $0.00 live price falls back to Previous Close."""
    mock_snap = MagicMock()
    mock_snap.latest_trade.price = 0.0
    mock_snap.daily_bar.close = 0.0
    mock_snap.previous_daily_bar.close = 150.0

    MockProvider.return_value.client.get_stock_snapshot.return_value = {"AAPL": mock_snap}

    response = client.get("/quotes?symbols=AAPL")
    assert response.status_code == 200
    assert response.json()["AAPL"]["price"] == 150.0

@patch("app.main.Receiver")
def test_cleanup_logic(MockReceiver, client, session):
    """Ensure we delete OLD records but KEEP new ones."""
    MockReceiver.return_value.verify.return_value = True

    now = datetime.now(timezone.utc)

    # Create Data using session fixture
    old_bet = Prediction(
        user_id="u1", symbol="OLD", start_price=100, predicted_price=110, confidence_score=0.9,
        saved_at=now - timedelta(days=60),
        target_date=now - timedelta(days=50),
        status="VALIDATED"
    )
    recent_bet = Prediction(
        user_id="u1", symbol="NEW", start_price=100, predicted_price=110, confidence_score=0.9,
        saved_at=now,
        target_date=now - timedelta(days=5),
        status="VALIDATED"
    )

    session.add(old_bet)
    session.add(recent_bet)
    session.commit()

    headers = {"Upstash-Signature": "fake"}
    client.post("/scheduler/cleanup", headers=headers)

    # Check DB
    remaining = session.exec(select(Prediction)).all()
    symbols = [p.symbol for p in remaining]

    assert "OLD" not in symbols
    assert "NEW" in symbols