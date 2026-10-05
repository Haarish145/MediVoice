import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_patient_and_nurse_websocket():
    res = client.post("/api/sessions", json={"language": "ta"})
    assert res.status_code == 200
    sid = res.json()["session_id"]

    # Test patient websocket connection
    with client.websocket_connect(f"/ws/patient/{sid}") as p_ws:
        init_p = p_ws.receive_json()
        assert init_p["event"] == "connection"
        assert init_p["session_id"] == sid

    # Test nurse websocket connection
    with client.websocket_connect(f"/ws/nurse/{sid}") as n_ws:
        init_n = n_ws.receive_json()
        assert init_n["event"] == "connection"
        assert init_n["session_id"] == sid
