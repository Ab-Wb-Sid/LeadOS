"""add audit log

Revision ID: b1850b732b6c
Revises: a1750b732b6c
Create Date: 2026-08-30 19:46:16.596530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1850b732b6c'
down_revision: Union[str, Sequence[str], None] = 'a1750b732b6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    field VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(120) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_audit_log_entity_type ON audit_log(entity_type);
CREATE INDEX idx_audit_log_entity_id ON audit_log(entity_id);
    """)

def downgrade() -> None:
    op.execute("""
DROP TABLE IF EXISTS audit_log CASCADE;
    """)
