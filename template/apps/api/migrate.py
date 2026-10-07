import asyncio
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine

ALEMBIC_INI = Path(__file__).resolve().parent / "alembic.ini"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _upgrade_sync(connection: Connection) -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    config = Config(str(ALEMBIC_INI))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


async def _upgrade_once(database_url: str) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_upgrade_sync)
    finally:
        await engine.dispose()


async def migrate(database_url: str) -> None:
    delay = 0.5
    for attempt in range(1, 11):
        try:
            await _upgrade_once(database_url)
        except OperationalError:
            if attempt == 10:
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, 5.0)
        else:
            return
