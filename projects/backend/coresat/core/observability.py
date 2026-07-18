"""Runtime logging: console + a rotating file the whole app dumps into.

Modeled on the lino `_logging` pattern. `setup_logging()` attaches a console
handler and a `RotatingFileHandler` writing to the configured runtime-log
directory (default `~/Projects/etops-demo-data/runtime_log/combined.log`), so
agent SQL, tool errors, and request flow land in one greppable file for
debugging. `with_runtime_logging()` times a block at DEBUG.
"""

import asyncio
import contextlib
import logging
import pathlib
import time
from collections.abc import Iterator
from logging import handlers

_LOG_FORMAT = "%(asctime)s %(levelname).4s %(name)s %(message)s"
_MAX_BYTES = 50 * 1024 * 1024
_BACKUP_COUNT = 10
# Names our console handler so setup_logging is idempotent even when the file
# sink fails to attach (a handler-type check would miss that case).
_CONSOLE_MARKER = "coresat-console"

log = logging.getLogger(__name__)


class _MetadataFormatter(logging.Formatter):
    """Append file:line, thread, and asyncio-task metadata to each record."""

    def __init__(self) -> None:
        super().__init__(_LOG_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        parts = [f"{record.filename}:{record.lineno}", f"tid={record.thread}"]
        try:
            task = asyncio.current_task()
        except RuntimeError:
            task = None
        if task is not None:
            parts.append(f"task={task.get_name()}")
        return f"{message} [{' '.join(parts)}]"


def _file_handler(log_dir: pathlib.Path) -> logging.Handler:
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = handlers.RotatingFileHandler(
        filename=str(log_dir / "combined.log"),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(_MetadataFormatter())
    return handler


def setup_logging(runtime_log_dir: str, level: int) -> None:
    """Attach console + rotating-file handlers to the root logger.

    Idempotent: a second call (e.g. a second create_app() in tests) never
    stacks another file handler. A missing/read-only log directory disables the
    file sink with a warning rather than stopping the app from booting.
    """
    root = logging.getLogger()
    root.setLevel(level)
    # Guard on the named console handler (added first, always), so a second call
    # never duplicates it even if the file sink failed to attach the first time.
    if any(handler.name == _CONSOLE_MARKER for handler in root.handlers):
        return
    console = logging.StreamHandler()
    console.name = _CONSOLE_MARKER
    console.setFormatter(_MetadataFormatter())
    root.addHandler(console)
    log_dir = pathlib.Path(runtime_log_dir).expanduser()
    try:
        root.addHandler(_file_handler(log_dir))
    except OSError as exc:
        log.warning("runtime file logging disabled (%s): %s", log_dir, exc)
    else:
        log.info("runtime logging → %s", log_dir / "combined.log")


@contextlib.contextmanager
def with_runtime_logging(identifier: str) -> Iterator[None]:
    """Log the wall-clock runtime of the wrapped block at DEBUG."""
    start = time.perf_counter()
    try:
        yield
    finally:
        log.debug("%s: %.3f ms", identifier, (time.perf_counter() - start) * 1000)
