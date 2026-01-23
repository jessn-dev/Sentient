from app.main import app
from app.auth import get_current_user


def test_unauthenticated_access_is_blocked(client):
    """
    Test that a protected endpoint returns 401 when no user is logged in.
    """
    # 1. ARRANGE: Forcefully remove the 'get_current_user' override for this specific test.
    # This undoes the auto-login setup from conftest.py, simulating a logged-out user.
    app.dependency_overrides.pop(get_current_user, None)

    # 2. ACT: Try to access a protected endpoint (e.g., POST /watchlist)
    payload = {
        "symbol": "AAPL",
        "initial_price": 150.0,
        "target_price": 200.0,
        "end_date": "2025-12-31"
    }
    response = client.post("/watchlist", json=payload)

    # 3. ASSERT: The API should reject the request
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_authenticated_access_is_allowed(client):
    """
    Test that the fixture correctly mocks a logged-in user.
    """
    # 1. ARRANGE: We use the 'client' fixture as-is, which has the override from conftest.py

    # 2. ACT: Hit the same protected endpoint
    payload = {
        "symbol": "TSLA",
        "initial_price": 200.0,
        "target_price": 250.0,
        "end_date": "2025-12-31"
    }
    response = client.post("/watchlist", json=payload)

    # 3. ASSERT: The request should succeed (200 OK)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}