import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the backend directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import db
from app import create_app

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Create the Flask app to get the proper database URI
flask_app = create_app()
config.set_main_option("sqlalchemy.url", flask_app.config["SQLALCHEMY_DATABASE_URI"])

target_metadata = db.metadata


def _use_batch():
    """Use batch mode for SQLite (required for ALTER TABLE operations)."""
    url = config.get_main_option("sqlalchemy.url") or ""
    return url.startswith("sqlite")


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_use_batch(),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=_use_batch(),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
