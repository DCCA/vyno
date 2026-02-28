from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

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
