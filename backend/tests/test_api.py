import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.models import Prediction

# --- TEST 1: HEALTH CHECK ---
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

