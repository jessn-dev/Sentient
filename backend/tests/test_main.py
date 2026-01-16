from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Verifies the API is running"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_prophet_import():
    """Verifies our heavy AI libraries are installed correctly"""
    from app.engine import PredictionEngine
    engine = PredictionEngine()
    assert engine is not None