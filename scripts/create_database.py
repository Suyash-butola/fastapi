"""Create the local course database after installing PostgreSQL."""
import psycopg
from psycopg import sql

from fastapi_project.config import settings

with psycopg.connect(
    host=settings.database_hostname,
    port=settings.database_port,
    dbname="postgres",
    user=settings.database_username,
    password=settings.database_password.get_secret_value(),
    autocommit=True,
) as connection:
    exists = connection.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s", (settings.database_name,)
    ).fetchone()
    if exists:
        print(f"Database {settings.database_name!r} already exists.")
    else:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.database_name)))
        print(f"Created database {settings.database_name!r}.")
