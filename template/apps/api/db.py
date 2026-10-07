import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

_engines: dict[str, AsyncEngine] = {}


class Base(DeclarativeBase):
    pass


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )


def engine_for(database_url: str) -> AsyncEngine:
    existing = _engines.get(database_url)
    if existing is not None:
        return existing
    created = create_async_engine(database_url)
    _engines[database_url] = created
    return created


def session_dependency(
    database_url: str,
) -> Callable[..., AsyncGenerator[AsyncSession]]:
    maker = async_sessionmaker(engine_for(database_url), expire_on_commit=False)

    async def get_async_session() -> AsyncGenerator[AsyncSession]:
        async with maker() as session:
            yield session

    return get_async_session


def user_db_dependency(
    get_async_session: Callable[..., AsyncGenerator[AsyncSession]],
) -> Callable[..., AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID]]]:
    async def get_user_db(
        session: Annotated[AsyncSession, Depends(get_async_session)],
    ) -> AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID]]:
        yield SQLAlchemyUserDatabase(session, User, OAuthAccount)

    return get_user_db
