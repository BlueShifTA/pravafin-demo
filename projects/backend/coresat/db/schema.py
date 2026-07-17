"""Apply the SQL schema (idempotent)."""

from importlib import resources

import asyncpg


async def apply_schema(admin_dsn: str) -> None:
    """Run schema.sql against the database as an admin role."""
    sql = resources.files("coresat.db").joinpath("schema.sql").read_text(encoding="utf-8")
    conn = await asyncpg.connect(admin_dsn)
    try:
        await conn.execute(sql)
    finally:
        await conn.close()
