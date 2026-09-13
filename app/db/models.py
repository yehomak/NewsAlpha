from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AttemptOutcome(StrEnum):
    STORED = "stored"
    REJECTED_UNIVERSE = "rejected_universe"
    TRUNCATED = "truncated"
    NO_SIGNAL = "no_signal"
    ERROR = "error"


class EventType(StrEnum):
    EARNINGS = "earnings"
    PRODUCT_LAUNCH = "product_launch"
    MACRO = "macro"
    GENERAL = "general"


class Direction(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    ticker_hints: Mapped[list[str] | None] = mapped_column(JSONB)
    coverage_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # semantic dedup fields (Stage 6)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    dedup_skipped: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    similar_to_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("events.id"), nullable=True
    )
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    signals: Mapped[list["Signal"]] = relationship(back_populates="event")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("events.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    direction: Mapped[Direction] = mapped_column(
        Enum(Direction, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(128))

    event: Mapped["Event"] = relationship(back_populates="signals")
    eval_result: Mapped["EvalResult | None"] = relationship(back_populates="signal", uselist=False)
    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(back_populates="signal")


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    signal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("signals.id"), nullable=False, unique=True
    )
    price_t0: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    price_t5: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    abnormal_return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    signal: Mapped["Signal"] = relationship(back_populates="eval_result")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        UniqueConstraint("signal_id", "offset_days", name="uq_price_snapshot_signal_offset"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    signal_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("signals.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    offset_days: Mapped[int] = mapped_column(Integer, nullable=False)

    signal: Mapped["Signal"] = relationship(back_populates="price_snapshots")


class ExtractionAttempt(Base):
    __tablename__ = "extraction_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("events.id"), nullable=False)
    outcome: Mapped[AttemptOutcome] = mapped_column(
        Enum(AttemptOutcome, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    ticker_proposed: Mapped[str | None] = mapped_column(String(16))
    signal_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("signals.id"), nullable=True
    )
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
