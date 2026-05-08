from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "processed_compressed_bytes" in data
    assert "cache_hit_rate" in data
    assert data["version"] == "0.3.0"

def test_processed_bytes_increment():
    # Initial stats
    initial_stats = client.get("/stats").json()
    initial_bytes = initial_stats["processed_compressed_bytes"]

    # Trigger a compression with valid KVTC data
    test_text = "Fehler: P0300\nStatus: Aktiv"
    response = client.post("/compress", json={"text": test_text})
    assert response.status_code == 200
    frame = response.json()["frame"]
    assert len(frame) > 0

    # New stats
    new_stats = client.get("/stats").json()
    assert new_stats["processed_compressed_bytes"] > initial_bytes
