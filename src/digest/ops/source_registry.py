from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable
import urllib.parse

import yaml

from digest.config import SourceConfig, load_sources
from digest.connectors.github import normalize_github_org

_SOURCE_FIELDS = {
    "rss": "rss_feeds",
    "youtube_channel": "youtube_channels",
    "youtube_query": "youtube_queries",
    "x_author": "x_authors",
    "x_theme": "x_themes",
    "github_repo": "github_repos",
    "github_topic": "github_topics",
    "github_query": "github_search_queries",
    "github_org": "github_orgs",
}


@dataclass(slots=True)
class OverlayData:
    added: dict[str, list[str]] = field(default_factory=dict)
    removed: dict[str, list[str]] = field(default_factory=dict)


def load_effective_sources(base_path: str, overlay_path: str) -> SourceConfig:
    base = load_sources(base_path)
    overlay = load_overlay(overlay_path)

    payload = {
        "rss_feeds": _merge_field("rss", base.rss_feeds, overlay),
        "youtube_channels": _merge_field("youtube_channel", base.youtube_channels, overlay),
        "youtube_queries": _merge_field("youtube_query", base.youtube_queries, overlay),
        "x_authors": _merge_field("x_author", base.x_authors, overlay),
        "x_themes": _merge_field("x_theme", base.x_themes, overlay),
        "github_repos": _merge_field("github_repo", base.github_repos, overlay),
        "github_topics": _merge_field("github_topic", base.github_topics, overlay),
        "github_search_queries": _merge_field("github_query", base.github_search_queries, overlay),
        "github_orgs": _merge_field("github_org", base.github_orgs, overlay),
        "x_inbox_path": base.x_inbox_path,
    }
    return SourceConfig(**payload)


def list_sources(base_path: str, overlay_path: str) -> dict[str, list[str]]:
    s = load_effective_sources(base_path, overlay_path)
    return {
        "rss": s.rss_feeds,
        "youtube_channel": s.youtube_channels,
        "youtube_query": s.youtube_queries,
        "x_author": s.x_authors,
        "x_theme": s.x_themes,
        "github_repo": s.github_repos,
        "github_topic": s.github_topics,
        "github_query": s.github_search_queries,
        "github_org": s.github_orgs,
    }


def add_source(base_path: str, overlay_path: str, source_type: str, value: str) -> tuple[bool, str]:
    st = _norm_type(source_type)
    cv = canonicalize_source_value(st, value)
    overlay = load_overlay(overlay_path)
    effective = list_sources(base_path, overlay_path).get(st, [])
    if cv in {canonicalize_source_value(st, v) for v in effective}:
        return False, cv
    _append_unique(overlay.added, st, cv)
    _remove_if_present(overlay.removed, st, cv)
    save_overlay(overlay_path, overlay)
    return True, cv


def remove_source(base_path: str, overlay_path: str, source_type: str, value: str) -> tuple[bool, str]:
    st = _norm_type(source_type)
    cv = canonicalize_source_value(st, value)
    overlay = load_overlay(overlay_path)

    removed_any = _remove_if_present(overlay.added, st, cv)
    base_values = list_sources(base_path, overlay_path).get(st, [])
    if cv in {canonicalize_source_value(st, v) for v in base_values}:
        _append_unique(overlay.removed, st, cv)
        removed_any = True

    save_overlay(overlay_path, overlay)
    return removed_any, cv


def load_overlay(path: str) -> OverlayData:
    p = Path(path)
    if not p.exists():
        return OverlayData()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return OverlayData()
    added = _sanitize_overlay_map(data.get("added"))
    removed = _sanitize_overlay_map(data.get("removed"))
    return OverlayData(added=added, removed=removed)


def save_overlay(path: str, overlay: OverlayData) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "added": {k: v for k, v in overlay.added.items() if v},
        "removed": {k: v for k, v in overlay.removed.items() if v},
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    tmp.replace(p)


def canonicalize_source_value(source_type: str, value: str) -> str:
    st = _norm_type(source_type)
    raw = (value or "").strip()
    if not raw:
        raise ValueError("source value is required")

    if st == "rss":
        parsed = urllib.parse.urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("rss must be a valid http/https URL")
        return raw

    if st == "youtube_channel":
        if not re.fullmatch(r"[A-Za-z0-9_-]{5,64}", raw):
            raise ValueError("youtube_channel must be a channel id")
        return raw

    if st == "youtube_query":
        return " ".join(raw.split())

    if st == "x_author":
        handle = raw.lstrip("@").strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{1,15}", handle):
            raise ValueError("x_author must be a valid X handle (without URL)")
        return handle

    if st == "x_theme":
        theme = " ".join(raw.split())
        if len(theme) < 2:
            raise ValueError("x_theme must contain at least 2 characters")
        return theme

    if st == "github_repo":
        repo = raw.lower().strip("/")
        if repo.startswith("https://github.com/"):
            repo = repo.split("https://github.com/", 1)[1]
        if not re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", repo):
            raise ValueError("github_repo must be in owner/repo format")
        return repo

    if st == "github_topic":
        topic = raw.lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,49}", topic):
            raise ValueError("github_topic must be a valid topic token")
        return topic

    if st == "github_query":
        return " ".join(raw.split())

    if st == "github_org":
        org = normalize_github_org(raw)
        if not org:
            raise ValueError("github_org must be a valid GitHub org login or URL")
        return org

    raise ValueError(f"unsupported source type: {source_type}")


def supported_source_types() -> list[str]:
    return sorted(_SOURCE_FIELDS)


def _sanitize_overlay_map(raw: object) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if not isinstance(raw, dict):
        return out
    for k, vals in raw.items():
        if k not in _SOURCE_FIELDS:
            continue
        if not isinstance(vals, list):
            continue
        clean: list[str] = []
        for v in vals:
            if not isinstance(v, str):
                continue
            vv = v.strip()
            if vv:
                clean.append(vv)
        if clean:
            out[k] = clean
    return out


def _merge_field(source_type: str, base_values: list[str], overlay: OverlayData) -> list[str]:
    cv: Callable[[str], str] = lambda v: canonicalize_source_value(source_type, v)
    removed = {cv(v) for v in overlay.removed.get(source_type, [])}
    merged: list[str] = []
    seen: set[str] = set()

    for value in base_values + overlay.added.get(source_type, []):
        canon = cv(value)
        if canon in removed or canon in seen:
            continue
        seen.add(canon)
        merged.append(canon)
    return merged


def _append_unique(bucket: dict[str, list[str]], source_type: str, value: str) -> None:
    rows = bucket.setdefault(source_type, [])
    if value not in rows:
        rows.append(value)


def _remove_if_present(bucket: dict[str, list[str]], source_type: str, value: str) -> bool:
    rows = bucket.get(source_type, [])
    if value not in rows:
        return False
    bucket[source_type] = [v for v in rows if v != value]
    return True


def _norm_type(source_type: str) -> str:
    st = (source_type or "").strip().lower()
    if st not in _SOURCE_FIELDS:
        allowed = ", ".join(supported_source_types())
        raise ValueError(f"unsupported source type '{source_type}'. allowed: {allowed}")
    return st
