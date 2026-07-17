"""CLI entrypoint: apply schema. Used by `just db-apply`."""

import asyncio

from coresat.core.config import get_settings
from coresat.db.schema import apply_schema


def main() -> None:
    asyncio.run(apply_schema(get_settings().admin_database_url))
    print("schema applied")  # noqa: T201 — CLI feedback, not app logging


if __name__ == "__main__":
    main()
