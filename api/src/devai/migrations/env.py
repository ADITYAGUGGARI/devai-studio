from alembic import context

import devai.models  # noqa: F401
from devai.core.database import Base

context.configure(connection=context.config.attributes["connection"], target_metadata=Base.metadata)
with context.begin_transaction():
    context.run_migrations()
