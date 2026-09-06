"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("url_hash", sa.String(64), nullable=False),
        sa.Column("processed", sa.Boolean, server_default="false", nullable=False),
    )
    op.create_index("ix_events_url_hash", "events", ["url_hash"], unique=True)
    op.create_index("ix_events_published_at", "events", ["published_at"])

    op.create_table(
        "signals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id"), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("bullish", "bearish", "neutral", name="direction"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column(
            "event_type",
            sa.Enum("earnings", "product_launch", "macro", "general", name="eventtype"),
            nullable=False,
        ),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("langfuse_trace_id", sa.String(128)),
    )
    op.create_index("ix_signals_ticker", "signals", ["ticker"])
    op.create_index("ix_signals_ticker_created_at", "signals", ["ticker", "created_at"])
    op.create_index("ix_signals_event_type", "signals", ["event_type"])

    op.create_table(
        "eval_results",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.BigInteger, sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("price_t0", sa.Numeric(12, 4), nullable=False),
        sa.Column("price_t5", sa.Numeric(12, 4), nullable=False),
        sa.Column("return_pct", sa.Float, nullable=False),
        sa.Column("correct", sa.Boolean, nullable=False),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_eval_results_signal_id", "eval_results", ["signal_id"], unique=True)

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.BigInteger, sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("price", sa.Numeric(12, 4), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("offset_days", sa.Integer, nullable=False),
    )
    op.create_index("ix_price_snapshots_signal_id", "price_snapshots", ["signal_id"])


def downgrade() -> None:
    op.drop_table("price_snapshots")
    op.drop_index("ix_eval_results_signal_id", "eval_results")
    op.drop_table("eval_results")
    op.drop_index("ix_signals_event_type", "signals")
    op.drop_index("ix_signals_ticker_created_at", "signals")
    op.drop_index("ix_signals_ticker", "signals")
    op.drop_table("signals")
    op.drop_index("ix_events_published_at", "events")
    op.drop_index("ix_events_url_hash", "events")
    op.drop_table("events")
    op.execute("DROP TYPE IF EXISTS direction")
    op.execute("DROP TYPE IF EXISTS eventtype")
