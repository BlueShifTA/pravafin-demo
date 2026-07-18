"""Runtime logging: setup writes records to the configured dir; the timer logs."""

import logging
import pathlib
from logging import handlers

import pytest

from coresat.core.observability import setup_logging, with_runtime_logging


def test_setup_logging_writes_records_to_the_runtime_dir(tmp_path: pathlib.Path) -> None:
    # create_app() already installed a root file handler at import; setup_logging
    # is idempotent, so drop it for this test then restore, to prove a fresh
    # setup writes to the directory it is given.
    root = logging.getLogger()
    saved = [h for h in root.handlers if isinstance(h, handlers.RotatingFileHandler)]
    for handler in saved:
        root.removeHandler(handler)
    try:
        setup_logging(str(tmp_path), logging.INFO)
        logging.getLogger("coresat.smoke").warning("run_sql failed: boom | sql=SELECT 1")
        for handler in root.handlers:
            handler.flush()
        content = (tmp_path / "combined.log").read_text()
        assert "run_sql failed: boom" in content
        assert "SELECT 1" in content
    finally:
        for handler in [h for h in root.handlers if isinstance(h, handlers.RotatingFileHandler)]:
            root.removeHandler(handler)
        for handler in saved:
            root.addHandler(handler)


def test_with_runtime_logging_emits_a_timing_line(caplog: pytest.LogCaptureFixture) -> None:
    with (
        caplog.at_level(logging.DEBUG, logger="coresat.core.observability"),
        with_runtime_logging("unit-block"),
    ):
        pass
    assert any("unit-block" in record.message for record in caplog.records)
