from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

from digest.models import Item, Score
from digest.timeutil import parse_dt
from digest.quality.online_repair import decayed_weight, source_family
from digest.storage.schema import SCHEMA_SQL


@dataclass(slots=True)
class RunRecord:
    run_id: str
    started_at: str
    window_start: str
    window_end: str
    status: str


class SQLiteStore:
    def __init__(self, db_path: str = "digest.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA_SQL)
            self._ensure_column(conn, "items", "description", "TEXT")
            self._ensure_column(conn, "scores", "tags_json", "TEXT")
            self._ensure_column(conn, "scores", "topic_tags_json", "TEXT")
            self._ensure_column(conn, "scores", "format_tags_json", "TEXT")
            self._ensure_column(conn, "scores", "provider", "TEXT")
            self._ensure_column(conn, "feedback", "target_kind", "TEXT")
            self._ensure_column(conn, "feedback", "target_key", "TEXT")
            self._ensure_column(conn, "feedback", "features_json", "TEXT")
            self._ensure_column(conn, "feedback", "actor", "TEXT")
            self._ensure_column(conn, "run_selected_items", "raw_total", "INTEGER")
            self._ensure_column(conn, "run_selected_items", "adjusted_total", "INTEGER")
            self._ensure_column(
                conn, "run_selected_items", "adjustment_breakdown_json", "TEXT"
            )

    def _ensure_column(
        self, conn: sqlite3.Connection, table: str, column: str, col_type: str
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        columns = {r[1] for r in rows}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def start_run(self, run_id: str, window_start: str, window_end: str) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO runs (run_id, started_at, window_start, window_end, status, source_errors, summary_errors) VALUES (?, ?, ?, ?, ?, '', '')",
                (run_id, now, window_start, window_end, "running"),
            )

    def finish_run(
        self,
        run_id: str,
        status: str,
        source_errors: list[str],
        summary_errors: list[str],
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE runs SET status = ?, source_errors = ?, summary_errors = ? WHERE run_id = ?",
                (status, "\n".join(source_errors), "\n".join(summary_errors), run_id),
            )

    def upsert_items(self, items: list[Item]) -> None:
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO items (id, url, title, source, author, published_at, type, raw_text, description, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        i.id,
                        i.url,
                        i.title,
                        i.source,
                        i.author,
                        i.published_at.isoformat() if i.published_at else None,
                        i.type,
                        i.raw_text,
                        i.description,
                        i.hash,
                    )
                    for i in items
                ],
            )

    def link_source_items(
        self,
        *,
        run_id: str,
        links: list[dict[str, str]],
    ) -> None:
        if not links:
            return
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO source_item_links (
                    source_key, source_type, source_value, item_id, run_id, linked_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(link.get("source_key") or "").strip(),
                        str(link.get("source_type") or "").strip(),
                        str(link.get("source_value") or "").strip(),
                        str(link.get("item_id") or "").strip(),
                        run_id,
                        now,
                    )
                    for link in links
                    if str(link.get("source_key") or "").strip()
                    and str(link.get("item_id") or "").strip()
                ],
            )

    def latest_items_for_sources(self, source_keys: list[str]) -> dict[str, dict[str, str]]:
        clean_keys = [str(key or "").strip() for key in source_keys if str(key or "").strip()]
        if not clean_keys:
            return {}
        placeholders = ",".join(["?"] * len(clean_keys))
        query = f"""
            SELECT
                l.source_key,
                l.source_type,
                l.source_value,
                l.item_id,
                l.linked_at,
                i.url,
                i.title,
                i.source,
                i.author,
                i.published_at,
                i.type,
                i.raw_text,
                i.description
            FROM source_item_links l
            JOIN items i ON i.id = l.item_id
            WHERE l.source_key IN ({placeholders})
            ORDER BY
                l.source_key ASC,
                CASE WHEN i.published_at IS NULL OR i.published_at = '' THEN 1 ELSE 0 END ASC,
                i.published_at DESC,
                l.linked_at DESC,
                l.item_id DESC
        """
        rows = []
        with self._conn() as conn:
            rows = conn.execute(query, clean_keys).fetchall()
        latest: dict[str, dict[str, str]] = {}
        for row in rows:
            source_key = str(row[0] or "").strip()
            if not source_key or source_key in latest:
                continue
            latest[source_key] = {
                "source_key": source_key,
                "source_type": str(row[1] or ""),
                "source_value": str(row[2] or ""),
                "item_id": str(row[3] or ""),
                "linked_at": str(row[4] or ""),
                "url": str(row[5] or ""),
                "title": str(row[6] or ""),
                "source": str(row[7] or ""),
                "author": str(row[8] or ""),
                "published_at": str(row[9] or ""),
                "item_type": str(row[10] or ""),
                "raw_text": str(row[11] or ""),
                "description": str(row[12] or ""),
            }
        return latest

    def insert_scores(self, run_id: str, scores: list[Score]) -> None:
        with self._conn() as conn:
            conn.executemany(
                (
                    "INSERT INTO scores "
                    "(run_id, item_id, relevance, quality, novelty, total, reason, tags_json, topic_tags_json, format_tags_json, provider) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                [
                    (
                        run_id,
                        s.item_id,
                        s.relevance,
                        s.quality,
                        s.novelty,
                        s.total,
                        s.reason,
                        json.dumps(s.tags),
                        json.dumps(s.topic_tags),
                        json.dumps(s.format_tags),
                        s.provider,
                    )
                    for s in scores
                ],
            )

    def replace_run_selected_items(
        self,
        run_id: str,
        selections: list[dict[str, object]],
    ) -> None:
        rid = run_id.strip()
        if not rid:
            return
        with self._conn() as conn:
            conn.execute("DELETE FROM run_selected_items WHERE run_id = ?", (rid,))
            conn.executemany(
                (
                    "INSERT INTO run_selected_items "
                    "(run_id, item_id, section, section_rank, source_family, score_total, raw_total, adjusted_total, "
                    "adjustment_breakdown_json, summary, tags_json, topic_tags_json, format_tags_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                [
                    (
                        rid,
                        str(row.get("item_id") or "").strip(),
                        str(row.get("section") or "").strip(),
                        int(row.get("section_rank") or 0),
                        str(row.get("source_family") or "").strip() or "unknown",
                        int(
                            row.get("adjusted_total")
                            or row.get("score_total")
                            or 0
                        ),
                        int(row.get("raw_total") or row.get("score_total") or 0),
                        int(
                            row.get("adjusted_total")
                            or row.get("score_total")
                            or 0
                        ),
                        json.dumps(
                            row.get("adjustment_breakdown") or {},
                            ensure_ascii=True,
                            sort_keys=True,
                        ),
                        str(row.get("summary") or "").strip(),
                        json.dumps(row.get("tags") or [], ensure_ascii=True),
                        json.dumps(row.get("topic_tags") or [], ensure_ascii=True),
                        json.dumps(row.get("format_tags") or [], ensure_ascii=True),
                    )
                    for row in selections
                    if str(row.get("item_id") or "").strip()
                ],
            )

    def list_run_items(self, *, run_id: str) -> list[dict[str, object]]:
        rid = run_id.strip()
        if not rid:
            return []
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT s.run_id, s.item_id, s.section, s.section_rank, s.source_family, s.score_total, "
                    "s.raw_total, s.adjusted_total, s.adjustment_breakdown_json, s.summary, "
                    "s.tags_json, s.topic_tags_json, s.format_tags_json, "
                    "i.url, i.title, i.source, i.author, i.published_at, i.type, i.description "
                    "FROM run_selected_items s "
                    "JOIN items i ON i.id = s.item_id "
                    "WHERE s.run_id = ? "
                    "ORDER BY CASE s.section "
                    "WHEN 'must_read' THEN 0 WHEN 'skim' THEN 1 WHEN 'videos' THEN 2 ELSE 3 END, "
                    "s.section_rank ASC"
                ),
                (rid,),
            ).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            raw_total = row[6]
            adjusted_total = row[7]
            breakdown = _json_object(row[8])
            legacy_score = raw_total is None and adjusted_total is None and not breakdown
            final_score = int(
                adjusted_total
                if adjusted_total is not None
                else row[5]
                or 0
            )
            original_score = int(
                raw_total
                if raw_total is not None
                else row[5]
                or 0
            )
            out.append(
                {
                    "run_id": str(row[0]),
                    "item_id": str(row[1]),
                    "section": str(row[2]),
                    "section_rank": int(row[3] or 0),
                    "source_family": str(row[4] or "unknown"),
                    "score_total": final_score,
                    "raw_total": original_score,
                    "adjusted_total": final_score,
                    "adjustment_breakdown": breakdown,
                    "score_mode": "legacy_raw" if legacy_score else "adjusted",
                    "summary": str(row[9] or ""),
                    "tags": _json_list(row[10]),
                    "topic_tags": _json_list(row[11]),
                    "format_tags": _json_list(row[12]),
                    "url": str(row[13] or ""),
                    "title": str(row[14] or ""),
                    "source": str(row[15] or ""),
                    "author": str(row[16] or ""),
                    "published_at": str(row[17] or ""),
                    "type": str(row[18] or ""),
                    "description": str(row[19] or ""),
                }
            )
        return out

    def upsert_run_artifact(
        self,
        *,
        run_id: str,
        channel: str,
        artifact_type: str,
        storage_path: str,
        preview_mode: bool = False,
        chunk_count: int = 0,
    ) -> None:
        rid = run_id.strip()
        if not rid:
            return
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO run_artifacts "
                    "(run_id, channel, artifact_type, storage_path, preview_mode, chunk_count, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(run_id, channel, artifact_type) DO UPDATE SET "
                    "storage_path=excluded.storage_path, preview_mode=excluded.preview_mode, "
                    "chunk_count=excluded.chunk_count, created_at=excluded.created_at"
                ),
                (
                    rid,
                    channel.strip(),
                    artifact_type.strip(),
                    storage_path.strip(),
                    1 if preview_mode else 0,
                    max(0, int(chunk_count)),
                    now,
                ),
            )

    def list_run_artifacts(self, *, run_id: str) -> list[dict[str, object]]:
        rid = run_id.strip()
        if not rid:
            return []
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT id, run_id, channel, artifact_type, storage_path, preview_mode, chunk_count, created_at "
                    "FROM run_artifacts WHERE run_id = ? ORDER BY created_at ASC, channel ASC"
                ),
                (rid,),
            ).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            out.append(
                {
                    "id": int(row[0] or 0),
                    "run_id": str(row[1] or ""),
                    "channel": str(row[2] or ""),
                    "artifact_type": str(row[3] or ""),
                    "storage_path": str(row[4] or ""),
                    "preview_mode": bool(row[5]),
                    "chunk_count": int(row[6] or 0),
                    "created_at": str(row[7] or ""),
                }
            )
        return out

    def list_archived_runs(self, limit: int = 50) -> list[dict[str, object]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT a.run_id, COALESCE(r.status, 'unknown'), COALESCE(r.started_at, MAX(a.created_at)), "
                    "COUNT(*), MAX(a.created_at) "
                    "FROM run_artifacts a "
                    "LEFT JOIN runs r ON r.run_id = a.run_id "
                    "WHERE a.preview_mode = 0 "
                    "GROUP BY a.run_id, r.status, r.started_at "
                    "ORDER BY MAX(a.created_at) DESC LIMIT ?"
                ),
                (max(1, limit),),
            ).fetchall()
        return [
            {
                "run_id": str(row[0] or ""),
                "status": str(row[1] or "unknown"),
                "started_at": str(row[2] or ""),
                "artifact_count": int(row[3] or 0),
                "archived_at": str(row[4] or ""),
            }
            for row in rows
        ]

    def mark_seen(self, keys: list[str]) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO seen (key, first_seen_at) VALUES (?, ?)",
                [(k, now) for k in keys],
            )

    def seen_keys(self) -> set[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT key FROM seen").fetchall()
        return {r[0] for r in rows}

    def get_x_cursor(self, selector_type: str, selector_value: str) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                (
                    "SELECT cursor FROM x_selector_cursors "
                    "WHERE selector_type = ? AND selector_value = ?"
                ),
                (selector_type, selector_value),
            ).fetchone()
        if not row:
            return None
        value = str(row[0] or "").strip()
        return value or None

    def set_x_cursor(
        self,
        *,
        selector_type: str,
        selector_value: str,
        cursor: str | None,
        last_item_id: str | None = None,
    ) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO x_selector_cursors "
                    "(selector_type, selector_value, cursor, last_item_id, updated_at) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(selector_type, selector_value) DO UPDATE SET "
                    "cursor = excluded.cursor, "
                    "last_item_id = excluded.last_item_id, "
                    "updated_at = excluded.updated_at"
                ),
                (
                    selector_type,
                    selector_value,
                    (cursor or "").strip() or None,
                    (last_item_id or "").strip() or None,
                    now,
                ),
            )

    def reset_seen(self, *, older_than_days: int | None = None) -> int:
        with self._conn() as conn:
            if older_than_days is None:
                row = conn.execute("SELECT COUNT(*) FROM seen").fetchone()
                count = int(row[0] or 0) if row else 0
                conn.execute("DELETE FROM seen")
                return count
            cutoff = datetime.now(tz=timezone.utc) - timedelta(
                days=max(1, int(older_than_days))
            )
            row = conn.execute(
                "SELECT COUNT(*) FROM seen WHERE first_seen_at <= ?",
                (cutoff.isoformat(),),
            ).fetchone()
            count = int(row[0] or 0) if row else 0
            conn.execute(
                "DELETE FROM seen WHERE first_seen_at <= ?",
                (cutoff.isoformat(),),
            )
            return count

    def last_completed_window_end(self) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT window_end FROM runs WHERE status IN ('success', 'partial') ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else None

    def latest_run_summary(self) -> tuple[str, str, str, int, int] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT run_id, status, started_at, source_errors, summary_errors FROM runs ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        src_errs = len((row[3] or "").splitlines()) if row[3] else 0
        sum_errs = len((row[4] or "").splitlines()) if row[4] else 0
        return str(row[0]), str(row[1]), str(row[2]), src_errs, sum_errs

    def latest_run_details(
        self,
        *,
        completed_only: bool = False,
    ) -> tuple[str, str, str, list[str], list[str]] | None:
        query = (
            "SELECT run_id, status, started_at, source_errors, summary_errors "
            "FROM runs ORDER BY started_at DESC LIMIT 1"
        )
        if completed_only:
            query = (
                "SELECT run_id, status, started_at, source_errors, summary_errors "
                "FROM runs WHERE status IN ('success','partial','failed') "
                "ORDER BY started_at DESC LIMIT 1"
            )
        with self._conn() as conn:
            row = conn.execute(query).fetchone()
        if not row:
            return None
        source_errors = [
            line.strip() for line in str(row[3] or "").splitlines() if line.strip()
        ]
        summary_errors = [
            line.strip() for line in str(row[4] or "").splitlines() if line.strip()
        ]
        return (
            str(row[0]),
            str(row[1]),
            str(row[2]),
            source_errors,
            summary_errors,
        )

    def recent_source_error_runs(
        self, limit: int = 20
    ) -> list[tuple[str, str, list[str]]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT run_id, started_at, source_errors "
                    "FROM runs WHERE source_errors IS NOT NULL AND source_errors != '' "
                    "ORDER BY started_at DESC LIMIT ?"
                ),
                (max(1, limit),),
            ).fetchall()
        out: list[tuple[str, str, list[str]]] = []
        for run_id, started_at, source_errors_raw in rows:
            source_errors = [
                line.strip()
                for line in str(source_errors_raw or "").splitlines()
                if line.strip()
            ]
            out.append((str(run_id), str(started_at), source_errors))
        return out

    def get_cached_score(
        self, item_hash: str, model: str, *, item_id: str, max_age_hours: int = 24
    ) -> Score | None:
        key = item_hash.strip()
        model_key = model.strip()
        if not key or not model_key:
            return None
        with self._conn() as conn:
            row = conn.execute(
                (
                    "SELECT cached_at, relevance, quality, novelty, total, reason, "
                    "tags_json, topic_tags_json, format_tags_json, provider "
                    "FROM score_cache WHERE item_hash = ? AND model = ?"
                ),
                (key, model_key),
            ).fetchone()
        if not row:
            return None
        cached_at = parse_dt(str(row[0] or ""))
        if cached_at is None:
            return None
        age_seconds = (datetime.now(tz=timezone.utc) - cached_at).total_seconds()
        if age_seconds > max(1, max_age_hours) * 3600:
            return None
        return Score(
            item_id=item_id,
            relevance=int(row[1] or 0),
            quality=int(row[2] or 0),
            novelty=int(row[3] or 0),
            total=int(row[4] or 0),
            reason=str(row[5] or ""),
            tags=_json_list(row[6]),
            topic_tags=_json_list(row[7]),
            format_tags=_json_list(row[8]),
            provider=str(row[9] or "agent"),
        )

    def upsert_cached_score(self, item_hash: str, model: str, score: Score) -> None:
        key = item_hash.strip()
        model_key = model.strip()
        if not key or not model_key:
            return
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO score_cache "
                    "(item_hash, model, cached_at, relevance, quality, novelty, total, reason, "
                    "tags_json, topic_tags_json, format_tags_json, provider) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(item_hash, model) DO UPDATE SET "
                    "cached_at=excluded.cached_at, relevance=excluded.relevance, quality=excluded.quality, "
                    "novelty=excluded.novelty, total=excluded.total, reason=excluded.reason, "
                    "tags_json=excluded.tags_json, topic_tags_json=excluded.topic_tags_json, "
                    "format_tags_json=excluded.format_tags_json, provider=excluded.provider"
                ),
                (
                    key,
                    model_key,
                    now,
                    int(score.relevance),
                    int(score.quality),
                    int(score.novelty),
                    int(score.total),
                    score.reason,
                    json.dumps(score.tags),
                    json.dumps(score.topic_tags),
                    json.dumps(score.format_tags),
                    score.provider,
                ),
            )

    def list_runs(self, limit: int = 50) -> list[RunRecord]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT run_id, started_at, window_start, window_end, status FROM runs ORDER BY started_at DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [RunRecord(*r) for r in rows]

    def insert_quality_eval(
        self,
        *,
        run_id: str,
        quality_score: float,
        confidence: float,
        issues: list[str],
        before_ids: list[str],
        after_ids: list[str],
        repaired: bool,
        model: str,
    ) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT OR REPLACE INTO run_quality_eval "
                    "(run_id, quality_score, confidence, issues_json, before_ids_json, after_ids_json, "
                    "repaired, model, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    run_id.strip(),
                    float(quality_score),
                    float(confidence),
                    json.dumps(list(issues)),
                    json.dumps(list(before_ids)),
                    json.dumps(list(after_ids)),
                    1 if repaired else 0,
                    model.strip(),
                    now,
                ),
            )

    def quality_prior_weights(
        self,
        *,
        half_life_days: int = 14,
        max_abs_weight: float = 8.0,
    ) -> dict[tuple[str, str], float]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT feature_type, feature_key, weight, updated_at "
                    "FROM quality_priors"
                )
            ).fetchall()
        out: dict[tuple[str, str], float] = {}
        for row in rows:
            feature_type = str(row[0] or "").strip().lower()
            feature_key = str(row[1] or "").strip().lower()
            if not feature_type or not feature_key:
                continue
            base_weight = float(row[2] or 0.0)
            weight = decayed_weight(
                base_weight,
                updated_at=str(row[3] or ""),
                half_life_days=max(1, half_life_days),
            )
            out[(feature_type, feature_key)] = max(
                -max_abs_weight, min(max_abs_weight, weight)
            )
        return out

    def apply_quality_prior_deltas(
        self,
        deltas: dict[tuple[str, str], float],
        *,
        max_abs_weight: float = 8.0,
    ) -> None:
        if not deltas:
            return
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            for (feature_type, feature_key), delta in deltas.items():
                ftype = feature_type.strip().lower()
                fkey = feature_key.strip().lower()
                if not ftype or not fkey or not delta:
                    continue
                row = conn.execute(
                    (
                        "SELECT weight, pos_count, neg_count "
                        "FROM quality_priors WHERE feature_type = ? AND feature_key = ?"
                    ),
                    (ftype, fkey),
                ).fetchone()
                prev_weight = float(row[0] or 0.0) if row else 0.0
                pos_count = int(row[1] or 0) if row else 0
                neg_count = int(row[2] or 0) if row else 0
                next_weight = prev_weight + float(delta)
                next_weight = max(-max_abs_weight, min(max_abs_weight, next_weight))
                if delta > 0:
                    pos_count += 1
                elif delta < 0:
                    neg_count += 1
                conn.execute(
                    (
                        "INSERT INTO quality_priors "
                        "(feature_type, feature_key, weight, pos_count, neg_count, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(feature_type, feature_key) DO UPDATE SET "
                        "weight=excluded.weight, pos_count=excluded.pos_count, "
                        "neg_count=excluded.neg_count, updated_at=excluded.updated_at"
                    ),
                    (ftype, fkey, next_weight, pos_count, neg_count, now),
                )

    def feedback_feature_bias(
        self,
        *,
        lookback_days: int = 45,
        max_abs_bias: float = 2.0,
    ) -> dict[tuple[str, str], float]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max(1, lookback_days))
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT f.rating, f.features_json, i.source, i.type "
                    "FROM feedback f LEFT JOIN items i ON i.id = f.item_id "
                    # IS NOT (not <>) so legacy rows with NULL target_kind survive.
                    "WHERE f.created_at >= ? AND f.target_kind IS NOT 'ingest'"
                ),
                (cutoff.isoformat(),),
            ).fetchall()

        sums: dict[tuple[str, str], float] = {}
        counts: Counter[tuple[str, str]] = Counter()
        for rating_raw, features_raw, source_raw, type_raw in rows:
            try:
                rating = int(rating_raw)
            except Exception:
                continue
            centered = max(-2.0, min(2.0, float(rating - 3))) / 2.0
            features = _json_feature_list(features_raw)
            if not features:
                source_key = source_family(str(source_raw or ""))
                type_key = str(type_raw or "").strip().lower()
                if source_key:
                    features.append(("source", source_key))
                if type_key:
                    features.append(("type", type_key))
            for key in features:
                sums[key] = float(sums.get(key, 0.0)) + centered
                counts[key] += 1

        out: dict[tuple[str, str], float] = {}
        for key, total in sums.items():
            count = max(1, counts[key])
            avg = total / count
            confidence = min(1.0, count / 6.0)
            bias = avg * confidence * max_abs_bias
            out[key] = max(-max_abs_bias, min(max_abs_bias, bias))
        return out

    def add_feedback(
        self,
        *,
        run_id: str,
        item_id: str,
        rating: int,
        label: str,
        comment: str,
        target_kind: str = "item",
        target_key: str = "",
        features: list[tuple[str, str]] | None = None,
        actor: str = "",
    ) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO feedback "
                    "(run_id, item_id, rating, label, comment, created_at, target_kind, target_key, features_json, actor) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    run_id.strip(),
                    item_id.strip(),
                    int(rating),
                    label.strip(),
                    comment.strip(),
                    now,
                    target_kind.strip() or "item",
                    target_key.strip(),
                    json.dumps(
                        [[ft, fk] for ft, fk in (features or []) if ft and fk],
                        ensure_ascii=True,
                    ),
                    actor.strip(),
                ),
            )

    def list_feedback(
        self, limit: int = 200
    ) -> list[tuple[int, str, str, int, str, str, str, str, str, str, str]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT id, run_id, item_id, rating, label, comment, created_at, "
                    "target_kind, target_key, features_json, actor "
                    "FROM feedback ORDER BY created_at DESC LIMIT ?"
                ),
                (max(1, limit),),
            ).fetchall()
        return [tuple(r) for r in rows]

    def feedback_summary(self) -> list[tuple[int, int]]:
        with self._conn() as conn:
            rows = conn.execute(
                # IS NOT (not <>) so legacy rows with NULL target_kind still count.
                "SELECT rating, COUNT(*) FROM feedback "
                "WHERE target_kind IS NOT 'ingest' "
                "GROUP BY rating ORDER BY rating DESC"
            ).fetchall()
        return [(int(r[0]), int(r[1])) for r in rows]

def _json_list(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (bytes, bytearray)):
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = str(raw)
    try:
        rows = json.loads(text)
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    out: list[str] = []
    for value in rows:
        if isinstance(value, str) and value.strip():
            out.append(value.strip())
    return out


def _json_dict(raw: object) -> dict[str, object]:
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = str(raw)
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _json_object(raw: object) -> dict[str, float]:
    payload = _json_dict(raw)
    out: dict[str, float] = {}
    for key, value in payload.items():
        label = str(key or "").strip()
        if not label:
            continue
        try:
            out[label] = round(float(value), 3)
        except Exception:
            continue
    return out


def _json_feature_list(raw: object) -> list[tuple[str, str]]:
    try:
        payload = json.loads(str(raw or "[]"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    out: list[tuple[str, str]] = []
    for row in payload:
        if isinstance(row, list) and len(row) == 2:
            feature_type = str(row[0] or "").strip().lower()
            feature_key = str(row[1] or "").strip().lower()
        elif isinstance(row, dict):
            feature_type = str(row.get("type") or "").strip().lower()
            feature_key = str(row.get("key") or "").strip().lower()
        else:
            continue
        if feature_type and feature_key:
            out.append((feature_type, feature_key))
    return out


