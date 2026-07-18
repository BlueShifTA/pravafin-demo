"""Runtime logging: setup writes records to the configured dir; the timer logs."""

import logging
import pathlib

import pytest

from coresat.core.observability import setup_logging, with_runtime_logging


def test_setup_logging_writes_records_to_the_runtime_dir(tmp_path: pathlib.Path) -> None:
    # create_app() already installed console + file handlers at import;
    # setup_logging is idempotent (guards on the named console handler), so
    # detach them for this test then restore, proving a fresh setup writes to
    # the directory it is given.
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers.clear()
    try:
        setup_logging(str(tmp_path), logging.INFO)
        logging.getLogger("coresat.smoke").warning("run_sql failed: boom | sql=SELECT 1")
        for handler in root.handlers:
            handler.flush()
        content = (tmp_path / "combined.log").read_text()
        assert "run_sql failed: boom" in content
        assert "SELECT 1" in content
    finally:
        root.handlers.clear()
        root.handlers.extend(saved)


def test_with_runtime_logging_emits_a_timing_line(caplog: pytest.LogCaptureFixture) -> None:
    with (
        caplog.at_level(logging.DEBUG, logger="coresat.core.observability"),
        with_runtime_logging("unit-block"),
    ):
        pass
    assert any("unit-block" in record.message for record in caplog.records)
