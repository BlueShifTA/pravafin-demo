"""Every planner SQL template must be valid against the live schema.

The vetted patterns in sql_templates are rendered into the planner prompts, so a
template that references a dropped column or mistypes SQL would teach the model
bad SQL. Executing each one read-only against coresat_test fails that here
instead of silently degrading a live agent turn. Auto-skips without Postgres.
"""

import asyncpg
import pytest

from coresat.db.schema import apply_schema
from coresat.services.agent.sql_templates import SQL_TEMPLATES

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def test_every_sql_template_executes_against_the_schema() -> None:
    # Empty tables are fine — a template that returns zero rows is still valid
    # SQL; only a bad column or syntax error raises PostgresError.
    conn = await _connect_or_skip()
    failures: list[str] = []
    try:
        await apply_schema(ADMIN_DSN)
        for intent, sql in SQL_TEMPLATES:
            try:
                await conn.fetch(sql)
            except asyncpg.PostgresError as error:
                failures.append(f"{intent}: {error}")
    finally:
        await conn.close()
    assert not failures, "invalid SQL templates:\n" + "\n".join(failures)
