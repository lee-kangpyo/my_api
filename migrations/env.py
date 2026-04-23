import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from models import Base

target_metadata = Base.metadata

SMALLSTEP_DATABASE_URL = os.getenv("smallstep_mysql") or os.getenv("mysql")
if not SMALLSTEP_DATABASE_URL:
    raise RuntimeError(
        "smallstep_mysql or mysql environment variable is not set. "
        "Cannot run database migrations."
    )

config.set_main_option("sqlalchemy.url", SMALLSTEP_DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from pathlib import Path
    
    connect_args = {}
    ssl_ca_path = Path(__file__).parent.parent / "ssl" / "ca-cert.pem"
    if ssl_ca_path.exists():
        connect_args = {
            "ssl": {
                "ca": str(ssl_ca_path),
                "check_hostname": False,
                "verify_mode": False
            }
        }
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
