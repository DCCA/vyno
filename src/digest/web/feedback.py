from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse


def _feedback_rating_for_label(label: str) -> int:
    normalized = str(label or "").strip().lower()
    mapping = {
        "more_like_this": 5,
        "prefer_source": 5,
        "not_relevant": 2,
        "too_technical": 1,
        "repeat_source": 1,
        "less_source": 2,
        "mute_source": 1,
    }
    if normalized not in mapping:
        raise ValueError("unsupported feedback label")
    return mapping[normalized]


def _feedback_features_for_item_feedback(
    row: dict[str, Any],
    *,
    label: str,
) -> list[tuple[str, str]]:
    features: list[tuple[str, str]] = [
        ("source", str(row.get("source_family") or "unknown").strip().lower()),
        ("source_exact", str(row.get("source") or "").strip().lower()),
        ("type", str(row.get("type") or "").strip().lower()),
    ]
    author = str(row.get("author") or "").strip().lower()
    if author:
        features.append(("author", author))
    for tag in row.get("topic_tags", []) or []:
        clean = str(tag or "").strip().lower()
        if clean:
            features.append(("topic", clean))
    for tag in row.get("format_tags", []) or []:
        clean = str(tag or "").strip().lower()
        if clean:
            features.append(("format", clean))
    if label == "repeat_source":
        features.extend(
            feature
            for feature in features
            if feature[0] in {"source", "source_exact", "author", "github_org"}
        )
    if label == "too_technical":
        features.append(("format", "technical"))
    return _dedupe_feedback_features(features)


def _feedback_features_for_source_feedback(
    *,
    source_type: str,
    source_value: str,
    label: str,
) -> list[tuple[str, str]]:
    st = str(source_type or "").strip().lower()
    value = str(source_value or "").strip().lower()
    features: list[tuple[str, str]] = []
    if st == "x_author":
        features.extend([("source", "x.com"), ("author", value)])
    elif st == "github_org":
        features.extend([("source", "github"), ("github_org", value)])
    elif st == "github_repo":
        owner = value.split("/", 1)[0].strip()
        features.extend([("source", "github"), ("source_exact", f"github:{value}")])
        if owner:
            features.append(("github_org", owner))
    elif st == "github_topic":
        features.extend([("source", "github"), ("topic", value)])
    elif st == "x_theme":
        features.append(("topic", value))
    elif st == "rss":
        parsed = urlparse(value)
        host = (parsed.netloc or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        if host:
            features.append(("source", host))
        features.append(("source_exact", value))
    else:
        features.append(("source_exact", value))
    if label == "mute_source" and not features:
        features.append(("source_exact", value))
    return _dedupe_feedback_features(features)


def _dedupe_feedback_features(
    rows: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for feature_type, feature_key in rows:
        clean = (str(feature_type or "").strip().lower(), str(feature_key or "").strip().lower())
        if not clean[0] or not clean[1] or clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return out


def _feedback_feature_rows_from_feedback_tuple(
    row: tuple[Any, ...],
) -> list[tuple[str, str]]:
    if len(row) < 10:
        return []
    raw = str(row[9] or "[]")
    try:
        payload = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    out: list[tuple[str, str]] = []
    for entry in payload:
        if not isinstance(entry, list) or len(entry) != 2:
            continue
        feature_type = str(entry[0] or "").strip().lower()
        feature_key = str(entry[1] or "").strip().lower()
        if feature_type and feature_key:
            out.append((feature_type, feature_key))
    return out
