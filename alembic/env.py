"""Use the application models and private connection settings."""
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool
from fastapi_project import models
from fastapi_project.config import settings
from fastapi_project.database import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=settings.sqlalchemy_url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"},
                      compare_type=True, compare_server_default=True)
    with context.begin_transaction():
        context.run_migrations()

def migrate_connection(connection):
    context.configure(connection=connection, target_metadata=target_metadata,
                      compare_type=True, compare_server_default=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connection = config.attributes.get("connection")
    if connection is not None:
        migrate_connection(connection)
        return
    engine = create_engine(settings.sqlalchemy_url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            migrate_connection(connection)
    finally:
        engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
