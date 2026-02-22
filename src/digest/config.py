from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import urllib.parse

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required. Install with: pip install PyYAML") from exc


@dataclass(slots=True)
class SourceConfig:
    rss_feeds: list[str] = field(default_factory=list)
    youtube_channels: list[str] = field(default_factory=list)
    youtube_queries: list[str] = field(default_factory=list)
    x_inbox_path: str = ""
    github_repos: list[str] = field(default_factory=list)
    github_topics: list[str] = field(default_factory=list)
    github_search_queries: list[str] = field(default_factory=list)
    github_orgs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OutputSettings:
    telegram_chat_id: str = ""
    telegram_bot_token: str = ""
    obsidian_vault_path: str = ""
    obsidian_folder: str = "AI Digest"
    obsidian_naming: str = "timestamped"
    render_mode: str = "sectioned"


@dataclass(slots=True)
class ProfileConfig:
    topics: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    trusted_sources: list[str] = field(default_factory=list)
    blocked_sources: list[str] = field(default_factory=list)
    trusted_authors_x: list[str] = field(default_factory=list)
    blocked_authors_x: list[str] = field(default_factory=list)
    trusted_orgs_github: list[str] = field(default_factory=list)
    blocked_orgs_github: list[str] = field(default_factory=list)
    github_min_stars: int = 0
    github_include_forks: bool = False
    github_include_archived: bool = False
    github_max_repos_per_org: int = 20
    github_max_items_per_org: int = 40
    output: OutputSettings = field(default_factory=OutputSettings)
    llm_enabled: bool = False
    agent_scoring_enabled: bool = True
    openai_model: str = "gpt-5.1-codex-mini"


def _read_yaml(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML object at {path}")
    return data


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_sources(path: str | Path) -> SourceConfig:
    data = _read_yaml(path)
    rss_feeds = _as_str_list(data, "rss_feeds")
    youtube_channels = _as_str_list(data, "youtube_channels")
    youtube_queries = _as_str_list(data, "youtube_queries")
    github_repos = _as_str_list(data, "github_repos")
    github_topics = _as_str_list(data, "github_topics")
    github_search_queries = _as_str_list(data, "github_search_queries")
    github_orgs = [_normalize_github_org(v) for v in _as_str_list(data, "github_orgs")]
    github_orgs = [v for v in github_orgs if v]
    x_inbox_path = str(data.get("x_inbox_path", "") or "").strip()
    if not (
        rss_feeds
        or youtube_channels
        or youtube_queries
        or github_repos
        or github_topics
        or github_search_queries
        or github_orgs
        or x_inbox_path
    ):
        raise ValueError("At least one source must be configured in sources.yaml")
    return SourceConfig(
        rss_feeds=rss_feeds,
        youtube_channels=youtube_channels,
        youtube_queries=youtube_queries,
        x_inbox_path=x_inbox_path,
        github_repos=github_repos,
        github_topics=github_topics,
        github_search_queries=github_search_queries,
        github_orgs=github_orgs,
    )


def load_profile(path: str | Path) -> ProfileConfig:
    data = _read_yaml(path)
    out = data.get("output", {})
    naming = str(out.get("obsidian_naming", "timestamped")).strip().lower()
    if naming not in {"timestamped", "daily"}:
        raise ValueError("output.obsidian_naming must be 'timestamped' or 'daily'")
    render_mode = str(out.get("render_mode", "sectioned")).strip().lower()
    if render_mode not in {"sectioned", "source_segmented"}:
        raise ValueError("output.render_mode must be 'sectioned' or 'source_segmented'")
    env_telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    env_telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    env_obsidian_vault = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()
    env_obsidian_folder = os.getenv("OBSIDIAN_FOLDER", "").strip()
    output = OutputSettings(
        telegram_chat_id=str(out.get("telegram_chat_id", "")).strip() or env_telegram_chat_id,
        telegram_bot_token=str(out.get("telegram_bot_token", "")).strip() or env_telegram_bot_token,
        obsidian_vault_path=str(out.get("obsidian_vault_path", "")).strip() or env_obsidian_vault,
        obsidian_folder=str(out.get("obsidian_folder", "AI Digest")).strip() or env_obsidian_folder or "AI Digest",
        obsidian_naming=naming,
        render_mode=render_mode,
    )
    env_model = os.getenv("OPENAI_MODEL", "").strip()
    return ProfileConfig(
        topics=_as_str_list(data, "topics"),
        entities=_as_str_list(data, "entities"),
        exclusions=_as_str_list(data, "exclusions"),
        trusted_sources=_as_str_list(data, "trusted_sources"),
        blocked_sources=_as_str_list(data, "blocked_sources"),
        trusted_authors_x=_as_str_list(data, "trusted_authors_x"),
        blocked_authors_x=_as_str_list(data, "blocked_authors_x"),
        trusted_orgs_github=_as_str_list(data, "trusted_orgs_github"),
        blocked_orgs_github=_as_str_list(data, "blocked_orgs_github"),
        github_min_stars=max(0, int(data.get("github_min_stars", 0) or 0)),
        github_include_forks=bool(data.get("github_include_forks", False)),
        github_include_archived=bool(data.get("github_include_archived", False)),
        github_max_repos_per_org=max(1, int(data.get("github_max_repos_per_org", 20) or 20)),
        github_max_items_per_org=max(1, int(data.get("github_max_items_per_org", 40) or 40)),
        output=output,
        llm_enabled=bool(data.get("llm_enabled", False)),
        agent_scoring_enabled=bool(data.get("agent_scoring_enabled", True)),
        openai_model=str(data.get("openai_model", env_model or "gpt-5.1-codex-mini")),
    )


def _as_str_list(data: dict, key: str) -> list[str]:
    raw = data.get(key, [])
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"Expected list for '{key}'")
    values = []
    for idx, value in enumerate(raw):
        if not isinstance(value, str):
            raise ValueError(f"Expected string at '{key}[{idx}]'")
        stripped = value.strip()
        if stripped:
            values.append(stripped)
    return values


def _normalize_github_org(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urllib.parse.urlparse(raw)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            return ""
        path = parsed.path.strip("/")
        if not path:
            return ""
        raw = path.split("/", 1)[0]
    else:
        raw = raw.split("/", 1)[0].lstrip("@")
    return raw.lower()
