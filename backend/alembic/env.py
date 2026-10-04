from contextlib import nullcontext

from alembic import context
from app import models  # noqa: F401 — register current model metadata
from app.core.config import Settings
from app.db.session import Base, create_db_engine
from app.models import analysis  # noqa: F401 — register analysis metadata

if context.is_offline_mode():
    context.configure(
        url=Settings().database_url.get_secret_value(),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    supplied = context.config.attributes.get("connection")
    engine = None if supplied is not None else create_db_engine(Settings())
    try:
        with (
            engine.connect() if engine is not None else nullcontext(supplied)
        ) as connection:
            context.configure(connection=connection, target_metadata=Base.metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        if engine is not None:
            engine.dispose()
