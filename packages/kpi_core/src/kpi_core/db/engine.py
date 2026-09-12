"""Async engine and session factory with lazy, cached construction."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engines: dict[str, AsyncEngine] = {}


def get_engine(database_url: str) -> AsyncEngine:
    engine = _engines.get(database_url)
    if engine is None:
        engine = create_async_engine(database_url, pool_size=5, max_overflow=10, pool_pre_ping=True)
        _engines[database_url] = engine
    return engine


def get_sessionmaker(database_url: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(database_url), expire_on_commit=False)


@asynccontextmanager
async def session_scope(database_url: str) -> AsyncIterator[AsyncSession]:
    """One transaction per use; commits on success, rolls back on error."""
    maker = get_sessionmaker(database_url)
    async with maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engines() -> None:
    for engine in list(_engines.values()):
        await engine.dispose()
    _engines.clear()
