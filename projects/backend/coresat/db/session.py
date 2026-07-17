"""Engine factory and RLS-scoped connections."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True)


def to_async_url(dsn: str) -> str:
    """asyncpg DSN (postgresql://…) → SQLAlchemy async URL (postgresql+asyncpg://…)."""
    return dsn.replace("postgresql://", "postgresql+asyncpg://", 1)


@asynccontextmanager
async def portfolio_scope(engine: AsyncEngine, portfolio_id: int) -> AsyncIterator[AsyncConnection]:
    """Connection whose transaction carries the RLS context.

    set_config(..., true) is transaction-local (SET LOCAL semantics): it dies at
    commit/rollback, so pooled-connection reuse can never leak another
    portfolio's scope.
    """
    async with engine.connect() as conn, conn.begin():
        await conn.execute(
            text("SELECT set_config('app.portfolio_id', :pid, true)"),
            {"pid": str(portfolio_id)},
        )
        yield conn
