"""Exercise PostgreSQL migrations in a temporary schema, rolled back afterward."""
from pathlib import Path
import unittest
from uuid import uuid4

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from fastapi_project import models
from fastapi_project.database import Base, engine


class MigrationTests(unittest.TestCase):
    def test_upgrade_downgrade_and_upgrade_again(self):
        schema = "migration_test_" + uuid4().hex
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                # The name is generated locally from a UUID, never user input.
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
                self.assertEqual(
                    set(inspect(connection).get_table_names(schema=schema)),
                    {"users", "posts", "votes", "alembic_version"},
                )
                context = MigrationContext.configure(
                    connection, opts={"compare_type": True, "compare_server_default": True}
                )
                self.assertEqual(compare_metadata(context, Base.metadata), [])

                user_id = connection.execute(
                    models.User.__table__.insert()
                    .values(email="migration@example.com", password="test-hash")
                    .returning(models.User.id)
                ).scalar_one()
                post_id = connection.execute(
                    models.Post.__table__.insert()
                    .values(title="Migration test", content="Temporary", owner_id=user_id)
                    .returning(models.Post.id)
                ).scalar_one()
                connection.execute(
                    models.Vote.__table__.insert().values(user_id=user_id, post_id=post_id)
                )
                row = connection.execute(
                    text("SELECT published, created_at FROM posts WHERE id=:id"), {"id": post_id}
                ).one()
                self.assertTrue(row.published)
                self.assertIsNotNone(row.created_at)
                connection.execute(models.Post.__table__.delete().where(models.Post.id == post_id))
                self.assertEqual(connection.execute(text("SELECT count(*) FROM votes")).scalar_one(), 0)

                command.downgrade(config, "base")
                self.assertEqual(
                    inspect(connection).get_table_names(schema=schema), ["alembic_version"]
                )
                command.upgrade(config, "head")
                self.assertEqual(context.get_current_revision(), "0001_initial_schema")
                self.assertEqual(compare_metadata(context, Base.metadata), [])
            finally:
                transaction.rollback()  # Removes the entire test schema and its rows.


if __name__ == "__main__":
    unittest.main()
