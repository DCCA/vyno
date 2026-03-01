from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from digest.constants import DEFAULT_OPENAI_MODEL, DIGEST_MUST_READ_LIMIT
from digest.models import DigestSections, ScoredItem

FeatureKey = tuple[str, str]


@dataclass(slots=True)
class QualityRepairResult:
    quality_score: float
    confidence: float
    issues: list[str]
    repaired_must_read_ids: list[str]
    model: str


class ResponsesAPIQualityRepair:
    provider = "openai_responses"

    def __init__(self, model: str = DEFAULT_OPENAI_MODEL, timeout: int = 30) -> None:
        self.model = model
        self.timeout = timeout
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for quality repair")

    def evaluate_and_repair(
        self,
        current_must_read: list[ScoredItem],
        candidate_pool: list[ScoredItem],
    ) -> QualityRepairResult:
        current_ids = [si.item.id for si in current_must_read]
        if len(current_ids) < DIGEST_MUST_READ_LIMIT:
            raise RuntimeError(
                f"Quality repair requires at least {DIGEST_MUST_READ_LIMIT} current must-read items"
            )
        pool_ids = [si.item.id for si in candidate_pool]
        if len(pool_ids) < DIGEST_MUST_READ_LIMIT:
            raise RuntimeError(
                f"Quality repair requires candidate pool size >= {DIGEST_MUST_READ_LIMIT}"
            )

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are an editor for an AI daily digest. "
                                "Assess Must-read quality and propose a repaired Must-read list "
                                f"of exactly {DIGEST_MUST_READ_LIMIT} ids selected only from the provided candidate pool. "
                                "Prioritize practical impact, novelty, source diversity, and reduced redundancy."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": _quality_eval_input(
                                current_must_read=current_must_read,
                                candidate_pool=candidate_pool,
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "must_read_quality_repair",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "quality_score": {"type": "number"},
                            "confidence": {"type": "number"},
                            "issues": {"type": "array", "items": {"type": "string"}},
                            "repaired_must_read_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": DIGEST_MUST_READ_LIMIT,
                                "maxItems": DIGEST_MUST_READ_LIMIT,
                            },
                        },
                        "required": [
                            "quality_score",
                            "confidence",
                            "issues",
                            "repaired_must_read_ids",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Quality repair HTTPError: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("Quality repair connection error") from exc

        parsed = _extract_json_output(raw)
        quality_score = max(0.0, min(100.0, float(parsed.get("quality_score", 0.0))))
        confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.0))))
        issues = _normalize_issue_list(parsed.get("issues", []))
        repaired_ids = _normalize_repaired_ids(parsed.get("repaired_must_read_ids", []))

        allowed = set(pool_ids)
        if len(repaired_ids) != DIGEST_MUST_READ_LIMIT:
            raise RuntimeError(
                "Quality repair invalid schema: repaired_must_read_ids size"
            )
        if len(set(repaired_ids)) != len(repaired_ids):
            raise RuntimeError("Quality repair invalid schema: duplicate repaired ids")
        if any(item_id not in allowed for item_id in repaired_ids):
            raise RuntimeError(
                "Quality repair invalid schema: id outside candidate pool"
            )

        # Keep the existing list if model emits empty issues with no change.
        if not issues and repaired_ids == current_ids:
            issues = ["no_material_issues"]

        return QualityRepairResult(
            quality_score=quality_score,
            confidence=confidence,
            issues=issues,
            repaired_must_read_ids=repaired_ids,
            model=self.model,
        )


def rebuild_sections_with_repair(
    sections: DigestSections,
    ranked_non_videos: list[ScoredItem],
    repaired_must_read_ids: list[str],
) -> DigestSections:
    id_map = {si.item.id: si for si in ranked_non_videos}
    missing = [item_id for item_id in repaired_must_read_ids if item_id not in id_map]
    if missing:
        raise RuntimeError(
            f"Cannot rebuild sections, missing ids: {', '.join(missing)}"
        )

    must_read = [id_map[item_id] for item_id in repaired_must_read_ids]
    used = {si.item.id for si in must_read}
    skim = [si for si in ranked_non_videos if si.item.id not in used][:10]

    max_skim = max(0, 20 - len(must_read) - len(sections.videos))
    skim = skim[:max_skim]
    max_videos = max(0, 20 - len(must_read) - len(skim))
    videos = sections.videos[:max_videos]
    return DigestSections(
        must_read=must_read,
        skim=skim,
        videos=videos,
        themes=list(sections.themes),
    )


def build_rank_overrides(
    scored_items: list[ScoredItem],
    *,
    prior_weights: dict[FeatureKey, float],
    feedback_weights: dict[FeatureKey, float],
    max_offset: float,
) -> dict[str, float]:
    merged = Counter(prior_weights)
    merged.update(feedback_weights)
    overrides: dict[str, float] = {}
    for scored in scored_items:
        adjustment = 0.0
        for feature in item_features(scored):
            adjustment += float(merged.get(feature, 0.0))
        adjustment = _clamp(adjustment, -max_offset, max_offset)
        overrides[scored.item.id] = float(scored.score.total) + adjustment
    return overrides


def compute_repair_feature_deltas(
    before_ids: list[str],
    after_ids: list[str],
    *,
    feature_map: dict[str, list[FeatureKey]],
    step: float = 0.8,
) -> dict[FeatureKey, float]:
    before_set = set(before_ids)
    after_set = set(after_ids)
    promoted = after_set - before_set
    demoted = before_set - after_set
    deltas: dict[FeatureKey, float] = {}

    for item_id in promoted:
        for feature in feature_map.get(item_id, []):
            deltas[feature] = float(deltas.get(feature, 0.0)) + step

    for item_id in demoted:
        for feature in feature_map.get(item_id, []):
            deltas[feature] = float(deltas.get(feature, 0.0)) - step

    return {k: float(v) for k, v in deltas.items() if v != 0}


def item_features(scored: ScoredItem) -> list[FeatureKey]:
    features: list[FeatureKey] = [
        ("source", source_family(scored.item.source)),
        ("type", scored.item.type),
    ]
    for tag in scored.score.topic_tags:
        features.append(("topic", tag.strip().lower()))
    for tag in scored.score.format_tags:
        features.append(("format", tag.strip().lower()))

    seen: set[FeatureKey] = set()
    deduped: list[FeatureKey] = []
    for feature in features:
        if not feature[1]:
            continue
        if feature in seen:
            continue
        seen.add(feature)
        deduped.append(feature)
    return deduped


def source_family(source: str) -> str:
    raw = (source or "").strip().lower()
    if not raw:
        return "unknown"
    if raw.startswith("github:"):
        return "github"
    if raw in {"x.com", "twitter.com"}:
        return "x.com"
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urllib.parse.urlparse(raw)
        host = (parsed.netloc or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        return host or raw
    return raw


def decayed_weight(
    weight: float,
    *,
    updated_at: str,
    half_life_days: int,
    now: datetime | None = None,
) -> float:
    dt = _parse_dt(updated_at)
    if dt is None:
        return weight
    ref = now or datetime.now(timezone.utc)
    age_days = max(0.0, (ref - dt).total_seconds() / 86400.0)
    half_life = float(max(1, half_life_days))
    factor = 0.5 ** (age_days / half_life)
    return float(weight) * factor


def _quality_eval_input(
    *,
    current_must_read: list[ScoredItem],
    candidate_pool: list[ScoredItem],
) -> str:
    payload = {
        "current_must_read_ids": [si.item.id for si in current_must_read],
        "current_must_read": [_item_payload(si) for si in current_must_read],
        "candidate_pool": [_item_payload(si) for si in candidate_pool],
        "selection_policy": {
            "must_read_count": DIGEST_MUST_READ_LIMIT,
            "prefer_source_diversity": True,
            "avoid_redundant_theme_overlap": True,
            "prefer_actionable_and_specific_items": True,
        },
    }
    return json.dumps(payload, ensure_ascii=True)


def _item_payload(scored: ScoredItem) -> dict[str, object]:
    summary = scored.summary
    return {
        "id": scored.item.id,
        "title": scored.item.title,
        "url": scored.item.url,
        "source": scored.item.source,
        "type": scored.item.type,
        "score_total": scored.score.total,
        "tags": list(scored.score.tags),
        "topic_tags": list(scored.score.topic_tags),
        "format_tags": list(scored.score.format_tags),
        "tldr": (summary.tldr if summary else "")[:280],
        "why_it_matters": (summary.why_it_matters if summary else "")[:280],
        "snippet": " ".join((scored.item.raw_text or "").split())[:420],
    }


def _extract_json_output(raw: dict) -> dict:
    output = raw.get("output", [])
    for out in output:
        for content in out.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text", "{}")
                if not isinstance(text, str) or not text.strip():
                    raise RuntimeError("Quality repair returned empty response")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    continue
    text = raw.get("output_text", "{}")
    if isinstance(text, str):
        if not text.strip():
            raise RuntimeError("Quality repair returned empty response")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Quality repair returned non-JSON output") from exc
    raise RuntimeError("Quality repair output missing structured JSON")


def _normalize_issue_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            continue
        item = " ".join(value.split()).strip().lower().replace(" ", "_")
        if item and item not in out:
            out.append(item)
    return out[:8]


def _normalize_repaired_ids(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            continue
        item_id = value.strip()
        if item_id:
            out.append(item_id)
    return out


def _parse_dt(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except Exception:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
