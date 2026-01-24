from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.core.auth import get_current_user


def test_no_token_returns_401(client: TestClient):
    """
    Negative Test: Ensure accessing a protected endpoint without a header returns 401.
    """
    # 1. Remove the override to test the real auth logic
    app.dependency_overrides.pop(get_current_user, None)

    # 2. Mock supabase client so we don't hit the 503 "Service Unavailable" error
    # (The real code checks 'if not supabase' first)
    with patch("app.core.auth.supabase", MagicMock()):
        response = client.post("/watchlist", json={
            "symbol": "AAPL",
            "initial_price": 100,
            "target_price": 110,
            "end_date": "2025-01-01"
        })

        # 3. Expect 401 Not Authenticated (missing token)
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}


def test_invalid_token_returns_401(client: TestClient):
    """
    Negative Test: Ensure providing a garbage/expired token returns 401.
    """
    app.dependency_overrides.pop(get_current_user, None)

    # 1. Mock Supabase to throw an error when checking the token
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.side_effect = Exception("Invalid JWT signature")

    with patch("app.core.auth.supabase", mock_supabase):
        response = client.post(
            "/watchlist",
            json={"symbol": "AAPL", "initial_price": 100, "target_price": 110, "end_date": "2025-01-01"},
            headers={"Authorization": "Bearer invalid-token-123"}
        )

        # 2. Expect 401 (Validation Failed)
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}


def test_missing_config_returns_503(client: TestClient):
    """
    Negative Test: Ensure that if the server has no Supabase credentials, it fails safely with 503.
    """
    app.dependency_overrides.pop(get_current_user, None)

    # 1. Force supabase client to be None (Simulating missing .env vars)
    with patch("app.core.auth.supabase", None):
        response = client.post(
            "/watchlist",
            json={"symbol": "AAPL", "initial_price": 100, "target_price": 110, "end_date": "2025-01-01"},
            headers={"Authorization": "Bearer valid-token"}
        )

        # 2. Expect 503 Service Unavailable
        assert response.status_code == 503
        assert "Authentication service not configured" in response.json()["detail"]


def test_authenticated_access_is_allowed(client: TestClient):
    """
    Positive Test: Ensure that the fixture correctly mocks a logged-in user.
    """
    # Note: 'client' fixture in conftest.py applies the override automatically.

    response = client.post("/watchlist", json={
        "symbol": "MSFT",
        "initial_price": 200.0,
        "target_price": 250.0,
        "end_date": "2025-12-31"
    })

    # Handle case where item might already exist from previous tests
    if response.status_code == 409:
        assert response.json()["detail"] == "Prediction already exists. Confirmation required."
    else:
        assert response.status_code == 200
        assert response.json()["status"] == "created"