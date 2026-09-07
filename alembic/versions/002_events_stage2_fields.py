"""events: add ticker_hints, coverage_count, processed index

Revision ID: 002
Revises: 001
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("events", sa.Column("ticker_hints", JSONB, nullable=True))
    op.add_column(
        "events",
        sa.Column("coverage_count", sa.Integer, nullable=False, server_default="1"),
    )
    # composite index for Stage 3 batch query: WHERE processed = false ORDER BY fetched_at
    op.create_index(
        "ix_events_processed_fetched_at",
        "events",
        ["processed", "fetched_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_events_processed_fetched_at", "events")
    op.drop_column("events", "coverage_count")
    op.drop_column("events", "ticker_hints")
