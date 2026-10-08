import logging
import secrets
import uuid
from typing import Annotated
from urllib.parse import quote

import jwt
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi_users import BaseUserManager, exceptions
from fastapi_users.authentication import AuthenticationBackend, Strategy
from fastapi_users.jwt import decode_jwt
from fastapi_users.manager import UserManagerDependency
from fastapi_users.router.oauth import (
    CSRF_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_KEY,
    STATE_TOKEN_AUDIENCE,
    generate_csrf_token,
    generate_state_token,
)
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.integrations.fastapi import (
    OAuth2AuthorizeCallback,
    OAuth2AuthorizeCallbackError,
)
from httpx_oauth.oauth2 import OAuth2Token

from apps.api.config import Settings
from apps.api.db import User

logger = logging.getLogger(__name__)

type OAuthClient = GoogleOAuth2 | GitHubOAuth2


def include_oauth(
    app: FastAPI,
    settings: Settings,
    backend: AuthenticationBackend[User, uuid.UUID],
    get_user_manager: UserManagerDependency[User, uuid.UUID],
) -> None:
    """Mount Google and GitHub only when both client id and secret are set.

    The library callback returns the bearer token as a JSON document. The browser
    is sent back to the SPA with that token in the URL fragment instead.
    """
    mounted = False
    if settings.google is not None:
        client_id, client_secret = settings.google
        _mount(
            app,
            settings,
            backend,
            get_user_manager,
            "google",
            GoogleOAuth2(client_id, client_secret),
        )
        mounted = True
    if settings.github is not None:
        client_id, client_secret = settings.github
        _mount(
            app,
            settings,
            backend,
            get_user_manager,
            "github",
            GitHubOAuth2(client_id, client_secret),
        )
        mounted = True
    if mounted:
        _redirect_oauth_errors(app, settings)


def _mount(
    app: FastAPI,
    settings: Settings,
    backend: AuthenticationBackend[User, uuid.UUID],
    get_user_manager: UserManagerDependency[User, uuid.UUID],
    name: str,
    client: OAuthClient,
) -> None:
    router = APIRouter()
    callback_name = f"oauth-{name}-callback"
    authorize_callback = OAuth2AuthorizeCallback(client, route_name=callback_name)

    @router.get("/authorize", name=f"oauth-{name}-authorize")
    async def authorize(request: Request) -> RedirectResponse:
        csrf_token = generate_csrf_token()
        state = generate_state_token({CSRF_TOKEN_KEY: csrf_token}, settings.secret)
        authorization_url = await client.get_authorization_url(
            str(request.url_for(callback_name)),
            state,
        )
        response = RedirectResponse(authorization_url, status_code=302)
        response.set_cookie(
            CSRF_TOKEN_COOKIE_NAME,
            csrf_token,
            max_age=3600,
            path="/",
            secure=_csrf_secure(request, settings),
            httponly=True,
            samesite="lax",
        )
        return response

    @router.get("/callback", name=callback_name)
    async def callback(
        request: Request,
        access_token_state: Annotated[
            tuple[OAuth2Token, str], Depends(authorize_callback)
        ],
        user_manager: Annotated[
            BaseUserManager[User, uuid.UUID], Depends(get_user_manager)
        ],
        strategy: Annotated[Strategy[User, uuid.UUID], Depends(backend.get_strategy)],
    ) -> RedirectResponse:
        token, state = access_token_state
        if not _csrf_matches(request, state, settings.secret):
            return _failure(settings, "oauth_invalid_state")
        access_token = token.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            return _failure(settings, "oauth_failed")
        try:
            account_id, account_email = await client.get_id_email(access_token)
        except Exception:
            logger.warning("OAuth profile lookup failed for %s", name)
            return _failure(settings, "oauth_failed")
        if account_email is None:
            return _failure(settings, "oauth_failed")
        expires_raw = token.get("expires_at")
        refresh_raw = token.get("refresh_token")
        try:
            user = await _oauth_user(
                user_manager,
                client.name,
                access_token,
                account_id,
                account_email,
                expires_raw if isinstance(expires_raw, int) else None,
                refresh_raw if isinstance(refresh_raw, str) else None,
                request,
            )
        except exceptions.UserAlreadyExists:
            return _failure(settings, "oauth_account_exists")
        if not user.is_active:
            return _failure(settings, "oauth_failed")
        jwt_token = await strategy.write_token(user)
        response = RedirectResponse(
            _account_location(settings, jwt_token), status_code=302
        )
        await user_manager.on_after_login(user, request, response)
        return response

    app.include_router(router, prefix=f"/auth/{name}", tags=["auth"])


async def _oauth_user(
    user_manager: BaseUserManager[User, uuid.UUID],
    oauth_name: str,
    access_token: str,
    account_id: str,
    account_email: str,
    expires_at: int | None,
    refresh_token: str | None,
    request: Request,
) -> User:
    # UserOAuthProtocol subclasses Generic, so it is not a Protocol on Python 3.14.
    # oauth_callback's self type therefore matches no user model.
    user = await user_manager.oauth_callback(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
        oauth_name,
        access_token,
        account_id,
        account_email,
        expires_at,
        refresh_token,
        request,
        associate_by_email=False,
        is_verified_by_default=True,
    )
    if not isinstance(user, User):
        message = "OAuth callback returned an unexpected account."
        raise RuntimeError(message)
    return user


def _redirect_oauth_errors(app: FastAPI, settings: Settings) -> None:
    @app.exception_handler(OAuth2AuthorizeCallbackError)
    async def oauth_callback_error(
        _request: Request, exc: OAuth2AuthorizeCallbackError
    ) -> RedirectResponse:
        logger.warning("OAuth callback rejected with status %s", exc.status_code)
        return _failure(settings, "oauth_failed")


def _csrf_secure(request: Request, settings: Settings) -> bool:
    if settings.csrf_cookie_secure is not None:
        return settings.csrf_cookie_secure
    return request.url.scheme == "https"


def _csrf_matches(request: Request, state: str, secret: str) -> bool:
    try:
        state_data = decode_jwt(state, secret, [STATE_TOKEN_AUDIENCE])
    except jwt.PyJWTError:
        return False
    cookie_token = request.cookies.get(CSRF_TOKEN_COOKIE_NAME)
    state_token = state_data.get(CSRF_TOKEN_KEY)
    if not isinstance(cookie_token, str) or not isinstance(state_token, str):
        return False
    return secrets.compare_digest(cookie_token, state_token)


def _account_location(settings: Settings, jwt_token: str) -> str:
    return f"{settings.spa_origin}/account#access_token={quote(jwt_token, safe='')}"


def _failure(settings: Settings, code: str) -> RedirectResponse:
    location = f"{settings.spa_origin}/login?error={code}"
    return RedirectResponse(location, status_code=302)
