import asyncio

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from apps.api.config import load_settings
from apps.api.db import Base

config = context.config
target_metadata = Base.metadata


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def _given_connection(value: object) -> Connection | None:
    if isinstance(value, Connection):
        return value
    return None


async def _run_from_url() -> None:
    engine = create_async_engine(load_settings().database_url)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run)
    finally:
        await engine.dispose()


def run_migrations_online() -> None:
    connection = _given_connection(config.attributes.get("connection"))
    if connection is not None:
        _run(connection)
        return
    asyncio.run(_run_from_url())


if context.is_offline_mode():
    message = "Offline migrations are not supported."
    raise RuntimeError(message)
run_migrations_online()
