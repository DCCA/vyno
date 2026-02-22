from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

ItemType = Literal["article", "video", "link"]


@dataclass(slots=True)
class Item:
    id: str
    url: str
    title: str
    source: str
    author: str | None
    published_at: datetime | None
    type: ItemType
    raw_text: str
    description: str = ""
    hash: str = ""


@dataclass(slots=True)
class Score:
    item_id: str
    relevance: int
    quality: int
    novelty: int
    total: int
    reason: str = ""


@dataclass(slots=True)
class Summary:
    tldr: str
    key_points: list[str] = field(default_factory=list)
    why_it_matters: str = ""
    provider: str = "extractive"


@dataclass(slots=True)
class ScoredItem:
    item: Item
    score: Score
    summary: Summary | None = None


@dataclass(slots=True)
class DigestSections:
    must_read: list[ScoredItem]
    skim: list[ScoredItem]
    videos: list[ScoredItem]
    themes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RunReport:
    run_id: str
    status: Literal["success", "partial", "failed"]
    source_errors: list[str] = field(default_factory=list)
    summary_errors: list[str] = field(default_factory=list)
