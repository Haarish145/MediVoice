from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_session_creation():
    response = client.post("/api/sessions", json={"language": "ta"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"].startswith("MV-")
    assert data["language"] == "ta"

def test_get_session_details():
    res_create = client.post("/api/sessions", json={"language": "hi"})
    sid = res_create.json()["session_id"]
    
    res_get = client.get(f"/api/sessions/{sid}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["session_id"] == sid
    assert data["language"] == "hi"

def test_nurse_login():
    res_login = client.post("/api/auth/nurse/login", json={
        "username": "nurse_admin",
        "password": "medivoice_nurse_2026"
    })
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
