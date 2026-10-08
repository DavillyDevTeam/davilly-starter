from fastapi.testclient import TestClient

from apps.api.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.text == '{"status":"ok"}'
