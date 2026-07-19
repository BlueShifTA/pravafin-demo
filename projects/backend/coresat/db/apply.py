"""CLI entrypoint: apply schema. Used by `just db-apply`."""

import asyncio

import coresat.core as csc
from coresat.db.schema import apply_schema


def main() -> None:
    asyncio.run(apply_schema(csc.get_settings().admin_database_url))
    print("schema applied")  # noqa: T201 — CLI feedback, not app logging


if __name__ == "__main__":
    main()
