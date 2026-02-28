from __future__ import annotations

from dataclasses import dataclass

from digest.config import ProfileConfig
from digest.models import Item

MEDIUM_SEVERITY_KEYWORDS = (
    "regression",
    "outage",
    "crash",
    "failing",
    "incident",
    "permission",
    "auth",
    "latency",
    "degraded",
    "data-loss",
    "data loss",
)


@dataclass(slots=True)
class IssueImpactDecision:
    keep: bool
    trusted_org: bool
    owner: str
    matched_keywords: list[str]
    reason: str


def evaluate_github_issue_impact(
    item: Item, profile: ProfileConfig
) -> IssueImpactDecision:
    if item.type != "github_issue":
        return IssueImpactDecision(
            keep=True,
            trusted_org=False,
            owner="",
            matched_keywords=[],
            reason="not_github_issue",
        )

    owner = _source_owner(item.source)
    trusted_orgs = {org.strip().lower() for org in profile.trusted_orgs_github}
    trusted_org = owner in trusted_orgs
    text = _text_for_match(item)
    matched_keywords = [kw for kw in MEDIUM_SEVERITY_KEYWORDS if kw in text]
    keep = trusted_org and bool(matched_keywords)

    if keep:
        reason = "trusted_org_with_medium_signal"
    elif not trusted_org:
        reason = "untrusted_org"
    else:
        reason = "missing_medium_signal"

    return IssueImpactDecision(
        keep=keep,
        trusted_org=trusted_org,
        owner=owner,
        matched_keywords=matched_keywords,
        reason=reason,
    )


def _source_owner(source: str) -> str:
    if not source.startswith("github:"):
        return ""
    tail = source.split(":", 1)[1].strip().lower()
    if "/" in tail:
        return tail.split("/", 1)[0]
    return ""


def _text_for_match(item: Item) -> str:
    return f"{item.title} {item.description} {item.raw_text}".lower()
