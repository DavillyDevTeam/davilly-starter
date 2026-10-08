import json
from collections.abc import Iterator
from typing import Protocol

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app, create_app


class TextResponse(Protocol):
    @property
    def text(self) -> str: ...


def json_body(response: TextResponse) -> object:
    # json.loads is typed as returning Any.
    value: object = json.loads(response.text)  # pyright: ignore[reportAny]
    return value


def field(body: object, key: str) -> object:
    if not isinstance(body, dict) or key not in body:
        message = f"Missing {key}."
        raise AssertionError(message)
    # isinstance(dict) narrows values to Unknown.
    return body[key]  # pyright: ignore[reportUnknownVariableType]


def text_field(body: object, key: str) -> str:
    found = field(body, key)
    if not isinstance(found, str) or found == "":
        message = f"{key} is not text."
        raise AssertionError(message)
    return found


def bool_field(body: object, key: str) -> bool:
    found = field(body, key)
    if not isinstance(found, bool):
        message = f"{key} is not a flag."
        raise AssertionError(message)
    return found


def assert_absent(body: object, key: str) -> None:
    if not isinstance(body, dict) or key in body:
        message = f"{key} leaked into the response."
        raise AssertionError(message)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_register_login_and_logout_keeps_the_jwt(client: TestClient) -> None:
    created = client.post(
        "/auth/register",
        json={
            "email": "ada@example.com",
            "password": "correct-horse",
            "is_superuser": True,
        },
    )
    assert created.status_code == 201
    body = json_body(created)
    assert text_field(body, "email") == "ada@example.com"
    assert bool_field(body, "is_active") is True
    assert bool_field(body, "is_superuser") is False
    assert_absent(body, "hashed_password")
    assert_absent(body, "oauth_accounts")

    logged_in = client.post(
        "/auth/jwt/login",
        data={"username": "ada@example.com", "password": "correct-horse"},
    )
    assert logged_in.status_code == 200
    token_body = json_body(logged_in)
    token = text_field(token_body, "access_token")
    assert text_field(token_body, "token_type") == "bearer"
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200
    me_body = json_body(me)
    assert text_field(me_body, "email") == "ada@example.com"

    logged_out = client.post("/auth/jwt/logout", headers=headers)
    assert logged_out.status_code == 204
    still_valid = client.get("/users/me", headers=headers)
    assert still_valid.status_code == 200


def test_login_rejects_a_wrong_password(client: TestClient) -> None:
    created = client.post(
        "/auth/register",
        json={"email": "grace@example.com", "password": "correct-horse"},
    )
    assert created.status_code == 201
    rejected = client.post(
        "/auth/jwt/login",
        data={"username": "grace@example.com", "password": "wrong-password"},
    )
    assert rejected.status_code == 400


def test_missing_and_garbage_tokens_are_rejected(client: TestClient) -> None:
    assert client.get("/users/me").status_code == 401
    garbage = client.get("/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert garbage.status_code == 401
    assert client.post("/auth/jwt/logout").status_code == 401


def test_short_password_and_duplicate_email_are_rejected(client: TestClient) -> None:
    short = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "tiny"},
    )
    assert short.status_code == 400
    first = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "correct-horse"},
    )
    assert first.status_code == 201
    second = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "correct-horse"},
    )
    assert second.status_code == 400


def test_oauth_routes_are_absent_until_configured(client: TestClient) -> None:
    providers = client.get("/auth/providers")
    assert providers.status_code == 200
    body = json_body(providers)
    assert bool_field(body, "google") is False
    assert bool_field(body, "github") is False
    assert client.get("/auth/google/authorize").status_code == 404
    assert client.get("/auth/github/authorize").status_code == 404


def test_oauth_routes_mount_when_both_secrets_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client")
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
    partial = create_app()
    with TestClient(partial) as partial_client:
        assert partial_client.get("/auth/google/authorize").status_code == 404
        assert partial_client.get("/auth/github/authorize").status_code == 404
        listed = json_body(partial_client.get("/auth/providers"))
    assert bool_field(listed, "google") is False
    assert bool_field(listed, "github") is False

    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-secret")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "github-client")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "github-secret")
    configured = create_app()
    with TestClient(configured) as oauth_client:
        listed = json_body(oauth_client.get("/auth/providers"))
        google = oauth_client.get("/auth/google/authorize", follow_redirects=False)
        github = oauth_client.get("/auth/github/authorize", follow_redirects=False)
    assert bool_field(listed, "google") is True
    assert bool_field(listed, "github") is True
    assert google.status_code == 302
    assert google.headers["location"].startswith("https://accounts.google.com/")
    assert "fastapiusersoauthcsrf" in google.cookies
    assert github.status_code == 302
    assert "github.com" in github.headers["location"]
