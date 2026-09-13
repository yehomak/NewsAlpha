"""eval_hardening

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-13 00:00:00.000000

Changes:
- eval_results: add abnormal_return_pct (nullable float)
- price_snapshots: add UNIQUE(signal_id, offset_days) to prevent duplicate fetches on retry
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE eval_results ADD COLUMN abnormal_return_pct DOUBLE PRECISION"
    )
    # Deduplicate existing rows before adding the unique constraint
    op.execute("""
        DELETE FROM price_snapshots a
        USING price_snapshots b
        WHERE a.id > b.id
          AND a.signal_id = b.signal_id
          AND a.offset_days = b.offset_days
    """)
    op.create_unique_constraint(
        "uq_price_snapshot_signal_offset",
        "price_snapshots",
        ["signal_id", "offset_days"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_price_snapshot_signal_offset", "price_snapshots", type_="unique")
    op.execute("ALTER TABLE eval_results DROP COLUMN abnormal_return_pct")
