"""add drug_name to predictions

Revision ID: 002
Revises: 001
Create Date: 2026-09-06 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This tells Postgres to add the column that was missing from the initial schema
    op.add_column("predictions", sa.Column("drug_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("predictions", "drug_name")
