from fastapi.testclient import TestClient

from apps.api.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES
from apps.api.main import create_app


def test_health() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.text == '{"status":"ok"}'
        assert response.headers["content-language"] == DEFAULT_LOCALE


def test_health_honors_accept_language() -> None:
    preferred = SUPPORTED_LOCALES[0]
    with TestClient(create_app()) as client:
        response = client.get("/api/health", headers={"Accept-Language": preferred})
        assert response.status_code == 200
        assert response.headers["content-language"] == preferred


def test_method_not_allowed_keeps_allow_header() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/health")
        assert response.status_code == 405
        assert "GET" in response.headers.get("allow", "")
        assert response.headers["content-language"] == DEFAULT_LOCALE
