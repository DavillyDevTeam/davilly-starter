import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app

ALLOWED_ORIGIN = "https://app.example.com"


def test_health_has_no_cors_headers_without_origins() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/health", headers={"Origin": ALLOWED_ORIGIN})
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_allows_listed_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", f"{ALLOWED_ORIGIN}, https://other.pages.dev/")
    with TestClient(create_app()) as client:
        response = client.options(
            "/api/health",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
        allow_headers = response.headers["access-control-allow-headers"].lower()
        assert "authorization" in allow_headers
        assert "content-type" in allow_headers
        allow_methods = response.headers["access-control-allow-methods"].upper()
        assert "POST" in allow_methods
        assert "GET" in allow_methods
        assert "access-control-allow-credentials" not in response.headers


def test_cors_get_echoes_listed_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", ALLOWED_ORIGIN)
    with TestClient(create_app()) as client:
        response = client.get("/api/health", headers={"Origin": ALLOWED_ORIGIN})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
        assert response.headers["access-control-allow-origin"] != "*"


def test_cors_preflight_rejects_unknown_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", ALLOWED_ORIGIN)
    with TestClient(create_app()) as client:
        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers


def test_cors_origin_regex_allows_pages_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGIN_REGEX", r"https://[a-z0-9-]+\.example\.pages\.dev")
    preview = "https://ab12cd.example.pages.dev"
    with TestClient(create_app()) as client:
        response = client.get("/api/health", headers={"Origin": preview})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == preview
