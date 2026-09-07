from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass
class RawArticle:
    url: str
    title: str
    source: str
    body: str | None = None
    published_at: datetime | None = None
    ticker_hints: list[str] = field(default_factory=list)


@runtime_checkable
class NewsSource(Protocol):
    name: str

    async def fetch(self) -> list[RawArticle]: ...
