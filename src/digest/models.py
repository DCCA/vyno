from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ItemType = Literal[
    "article",
    "video",
    "link",
    "x_post",
    "github_release",
    "github_issue",
    "github_pr",
    "github_repo",
]


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
    tags: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    format_tags: list[str] = field(default_factory=list)
    provider: str = "rules"
    raw_total: int | None = None
    adjusted_total: int | None = None
    adjustment_breakdown: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.raw_total is None:
            self.raw_total = int(self.total)
        if self.adjusted_total is None:
            self.adjusted_total = int(self.total)

    @property
    def final_total(self) -> int:
        return int(self.adjusted_total if self.adjusted_total is not None else self.total)


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
    telegram_messages: list[str] = field(default_factory=list)
    obsidian_note: str = ""
    source_count: int = 0
    must_read_count: int = 0
    skim_count: int = 0
    video_count: int = 0
    context: dict[str, Any] = field(default_factory=dict)
