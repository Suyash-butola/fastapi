"""Adopt matching pre-Alembic tables once, then apply pending migrations."""
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from fastapi_project import models
from fastapi_project.database import Base, engine

INITIAL_REVISION = "0001_initial_schema"


def main():
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        context = MigrationContext.configure(
            connection, opts={"compare_type": True, "compare_server_default": True}
        )
        tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
        if context.get_current_revision() is None and tables:
            differences = compare_metadata(context, Base.metadata)
            if differences:
                raise RuntimeError(
                    "Existing schema differs from the course models. Refusing to stamp "
                    "or modify it automatically; review the schema differences first."
                )
            command.stamp(config, INITIAL_REVISION)
            print("Existing matching tables adopted; no application data changed.")
        command.upgrade(config, "head")
        print("Database is at the latest migration.")


if __name__ == "__main__":
    main()
