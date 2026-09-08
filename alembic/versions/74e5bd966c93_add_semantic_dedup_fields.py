"""add_semantic_dedup_fields

Revision ID: 74e5bd966c93
Revises: 002
Create Date: 2026-09-08 12:46:02.416664

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "74e5bd966c93"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("events", sa.Column("embedding", Vector(384), nullable=True))
    op.add_column(
        "events",
        sa.Column("dedup_skipped", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("events", sa.Column("similar_to_id", sa.BigInteger(), nullable=True))
    op.add_column("events", sa.Column("similarity_score", sa.Float(), nullable=True))
    op.create_foreign_key("fk_events_similar_to_id", "events", "events", ["similar_to_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_events_similar_to_id", "events", type_="foreignkey")
    op.drop_column("events", "similarity_score")
    op.drop_column("events", "similar_to_id")
    op.drop_column("events", "dedup_skipped")
    op.drop_column("events", "embedding")
