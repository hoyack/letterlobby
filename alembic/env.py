import sys
from pathlib import Path

# Adjust PYTHONPATH so 'app' package can be found
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Now we can safely import from app since we've adjusted sys.path
from app.core.config import settings
from app.core.database import Base

# this is the Alembic Config object, which provides
# access to values within the alembic.ini file.
config = context.config

# Interpret the config file for Python logging.
# This sets up the loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata to your models' metadata object
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.DATABASE_URL  # override with your env variable
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
