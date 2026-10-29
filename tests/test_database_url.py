import unittest

from fastapi_project.config import Settings


class DatabaseURLTests(unittest.TestCase):
    def settings(self, **overrides):
        return Settings(_env_file=None, secret_key="test-only-" * 5, **overrides)

    def test_render_url_uses_installed_psycopg_driver(self):
        for scheme in ("postgres", "postgresql", "postgresql+psycopg"):
            with self.subTest(scheme=scheme):
                settings = self.settings(
                    database_url=f"{scheme}://app:p%40ss@db.example:5432/course?sslmode=require",
                    database_hostname="ignored.example",
                )
                url = settings.sqlalchemy_url
                self.assertEqual(url.drivername, "postgresql+psycopg")
                self.assertEqual(url.password, "p@ss")
                self.assertEqual(url.host, "db.example")
                self.assertEqual(url.query["sslmode"], "require")
                self.assertNotIn("p%40ss", str(url))

    def test_existing_local_fields_still_work(self):
        url = self.settings(
            database_hostname="localhost", database_name="course",
            database_username="postgres", database_password="example",
        ).sqlalchemy_url
        self.assertEqual(url.drivername, "postgresql+psycopg")
        self.assertEqual(url.database, "course")
        self.assertEqual(url.password, "example")

    def test_rejects_other_database_drivers(self):
        with self.assertRaises(ValueError):
            _ = self.settings(database_url="sqlite:///example.db").sqlalchemy_url
