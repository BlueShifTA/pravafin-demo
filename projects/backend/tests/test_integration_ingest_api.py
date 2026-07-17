"""Ingest API (integration): upload → report; runs + quarantine visible.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio
from collections.abc import Iterator

import asyncpg
import pytest
from fastapi.testclient import TestClient

from coresat.db.schema import apply_schema
from coresat.main import app

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat"

UNIVERSE_CSV = b"""ticker,type,sector,industry
TSTN,stock,semiconductor,Semiconductors
,stock,broken-row,
"""


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _prepare() -> None:
    conn = await _connect_or_skip()
    await apply_schema(ADMIN_DSN)
    await conn.execute("TRUNCATE ingest_quarantine, ingest_runs RESTART IDENTITY CASCADE")
    await conn.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    asyncio.run(_prepare())
    with TestClient(app) as test_client:
        yield test_client


def test_upload_ingests_and_reports(client: TestClient) -> None:
    response = client.post(
        "/api/ingest/universe_csv",
        files={"file": ("universe.csv", UNIVERSE_CSV, "text/csv")},
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["rows_ok"] == 1
    assert report["rows_quarantined"] == 1
    assert report["status"] == "succeeded"

    runs = client.get("/api/ingest/runs").json()
    assert any(run["source"] == "universe_csv" for run in runs)

    quarantine = client.get("/api/ingest/quarantine").json()
    assert len(quarantine) == 1
    assert "ticker" in quarantine[0]["reason"]


def test_unknown_adapter_is_404(client: TestClient) -> None:
    response = client.post(
        "/api/ingest/nope",
        files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert response.status_code == 404
