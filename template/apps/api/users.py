import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, override

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.jwt import SecretType

from apps.api.config import Settings
from apps.api.db import User, session_dependency, user_db_dependency

MIN_PASSWORD_LENGTH = 8


def build_auth(
    settings: Settings,
) -> tuple[AuthenticationBackend[User, uuid.UUID], FastAPIUsers[User, uuid.UUID]]:
    get_user_db = user_db_dependency(session_dependency(settings.database_url))

    class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
        reset_password_token_secret: SecretType = settings.secret
        verification_token_secret: SecretType = settings.secret

        @override
        async def validate_password(self, password: str, user: object) -> None:
            if len(password) < MIN_PASSWORD_LENGTH:
                reason = "Password must be at least 8 characters."
                raise exceptions.InvalidPasswordException(reason=reason)

    async def get_user_manager(
        user_db: Annotated[
            SQLAlchemyUserDatabase[User, uuid.UUID], Depends(get_user_db)
        ],
    ) -> AsyncGenerator[UserManager]:
        yield UserManager(user_db)

    def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
        return JWTStrategy(
            secret=settings.secret,
            lifetime_seconds=settings.access_token_lifetime_seconds,
        )

    backend: AuthenticationBackend[User, uuid.UUID] = AuthenticationBackend(
        name="jwt",
        transport=BearerTransport(tokenUrl="auth/jwt/login"),
        get_strategy=get_jwt_strategy,
    )
    return backend, FastAPIUsers[User, uuid.UUID](get_user_manager, [backend])
