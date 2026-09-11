"""add_extraction_attempts

Revision ID: a1b2c3d4e5f6
Revises: 74e5bd966c93
Create Date: 2026-09-11 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "74e5bd966c93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TYPE IF EXISTS attemptoutcome")
    op.execute(
        "CREATE TYPE attemptoutcome AS ENUM "
        "('stored', 'rejected_universe', 'truncated', 'no_signal', 'error')"
    )
    op.execute("""
        CREATE TABLE extraction_attempts (
            id          BIGSERIAL PRIMARY KEY,
            event_id    BIGINT NOT NULL REFERENCES events(id),
            outcome     attemptoutcome NOT NULL,
            ticker_proposed VARCHAR(16),
            signal_id   BIGINT REFERENCES signals(id),
            cost_usd    NUMERIC(10, 6) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_extraction_attempts_event_id ON extraction_attempts (event_id)")
    op.execute("CREATE INDEX ix_extraction_attempts_outcome ON extraction_attempts (outcome)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS extraction_attempts")
    op.execute("DROP TYPE IF EXISTS attemptoutcome")
