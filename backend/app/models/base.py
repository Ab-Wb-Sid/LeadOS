from sqlalchemy.orm import declarative_base

# Shared declarative base — every model in this package inherits from this
# so they all register on the same metadata object (needed later for
# Alembic autogenerate, even though migration #1 was hand-written SQL).
Base = declarative_base()
