from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "MediVoice"

def test_languages_endpoint():
    response = client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert "supported_languages" in data
    assert data["total_languages"] == 12
    # Verify Tamil and Hindi are present
    codes = [l["language_code"] for l in data["supported_languages"]]
    assert "ta" in codes
    assert "hi" in codes
