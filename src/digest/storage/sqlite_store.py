from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

from digest.models import Item, Score
from digest.quality.online_repair import decayed_weight, source_family


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
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    source TEXT,
                    author TEXT,
                    published_at TEXT,
                    type TEXT,
                    raw_text TEXT,
                    hash TEXT
                );

                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT,
                    window_start TEXT,
                    window_end TEXT,
                    status TEXT,
                    source_errors TEXT,
                    summary_errors TEXT
                );

                CREATE TABLE IF NOT EXISTS scores (
                    run_id TEXT,
                    item_id TEXT,
                    relevance INTEGER,
                    quality INTEGER,
                    novelty INTEGER,
                    total INTEGER,
                    reason TEXT,
                    tags_json TEXT,
                    topic_tags_json TEXT,
                    format_tags_json TEXT,
                    provider TEXT
                );

                CREATE TABLE IF NOT EXISTS seen (
                    key TEXT PRIMARY KEY,
                    first_seen_at TEXT
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    item_id TEXT,
                    rating INTEGER,
                    label TEXT,
                    comment TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS admin_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT,
                    action TEXT,
                    target TEXT,
                    details TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS score_cache (
                    item_hash TEXT,
                    model TEXT,
                    cached_at TEXT,
                    relevance INTEGER,
                    quality INTEGER,
                    novelty INTEGER,
                    total INTEGER,
                    reason TEXT,
                    tags_json TEXT,
                    topic_tags_json TEXT,
                    format_tags_json TEXT,
                    provider TEXT,
                    PRIMARY KEY (item_hash, model)
                );

                CREATE TABLE IF NOT EXISTS run_quality_eval (
                    run_id TEXT PRIMARY KEY,
                    quality_score REAL,
                    confidence REAL,
                    issues_json TEXT,
                    before_ids_json TEXT,
                    after_ids_json TEXT,
                    repaired INTEGER,
                    model TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS quality_priors (
                    feature_type TEXT,
                    feature_key TEXT,
                    weight REAL,
                    pos_count INTEGER,
                    neg_count INTEGER,
                    updated_at TEXT,
                    PRIMARY KEY (feature_type, feature_key)
                );

                CREATE TABLE IF NOT EXISTS run_timeline_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_index INTEGER NOT NULL,
                    ts_utc TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    elapsed_s REAL NOT NULL,
                    details_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS run_timeline_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    author TEXT,
                    note TEXT NOT NULL,
                    labels_json TEXT NOT NULL,
                    actions_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_timeline_events_run_idx
                    ON run_timeline_events(run_id, event_index);
                CREATE INDEX IF NOT EXISTS idx_timeline_events_run_stage
                    ON run_timeline_events(run_id, stage);
                CREATE INDEX IF NOT EXISTS idx_timeline_events_run_severity
                    ON run_timeline_events(run_id, severity);
                CREATE INDEX IF NOT EXISTS idx_timeline_notes_run_created
                    ON run_timeline_notes(run_id, created_at_utc DESC);
                """
            )
            self._ensure_column(conn, "scores", "tags_json", "TEXT")
            self._ensure_column(conn, "scores", "topic_tags_json", "TEXT")
            self._ensure_column(conn, "scores", "format_tags_json", "TEXT")
            self._ensure_column(conn, "scores", "provider", "TEXT")

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
                INSERT OR REPLACE INTO items (id, url, title, source, author, published_at, type, raw_text, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        i.hash,
                    )
                    for i in items
                ],
            )

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
        cached_at = _parse_dt(str(row[0] or ""))
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
                    "SELECT f.rating, i.source, i.type "
                    "FROM feedback f JOIN items i ON i.id = f.item_id "
                    "WHERE f.created_at >= ?"
                ),
                (cutoff.isoformat(),),
            ).fetchall()

        sums: dict[tuple[str, str], float] = {}
        counts: Counter[tuple[str, str]] = Counter()
        for rating_raw, source_raw, type_raw in rows:
            try:
                rating = int(rating_raw)
            except Exception:
                continue
            centered = max(-2.0, min(2.0, float(rating - 3))) / 2.0
            source_key = source_family(str(source_raw or ""))
            type_key = str(type_raw or "").strip().lower()
            if source_key:
                key = ("source", source_key)
                sums[key] = float(sums.get(key, 0.0)) + centered
                counts[key] += 1
            if type_key:
                key = ("type", type_key)
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
    ) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO feedback (run_id, item_id, rating, label, comment, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (
                    run_id.strip(),
                    item_id.strip(),
                    int(rating),
                    label.strip(),
                    comment.strip(),
                    now,
                ),
            )

    def list_feedback(
        self, limit: int = 200
    ) -> list[tuple[int, str, str, int, str, str, str]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT id, run_id, item_id, rating, label, comment, created_at "
                    "FROM feedback ORDER BY created_at DESC LIMIT ?"
                ),
                (max(1, limit),),
            ).fetchall()
        return [tuple(r) for r in rows]

    def feedback_summary(self) -> list[tuple[int, int]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating DESC"
            ).fetchall()
        return [(int(r[0]), int(r[1])) for r in rows]

    def log_admin_action(
        self, *, actor: str, action: str, target: str, details: str = ""
    ) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO admin_audit (actor, action, target, details, created_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (actor.strip(), action.strip(), target.strip(), details.strip(), now),
            )

    def list_admin_actions(
        self, limit: int = 200
    ) -> list[tuple[int, str, str, str, str, str]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT id, actor, action, target, details, created_at "
                    "FROM admin_audit ORDER BY created_at DESC LIMIT ?"
                ),
                (max(1, limit),),
            ).fetchall()
        return [tuple(r) for r in rows]

    def insert_timeline_event(
        self,
        *,
        run_id: str,
        event_index: int,
        stage: str,
        severity: str,
        message: str,
        elapsed_s: float,
        details: dict[str, object] | None = None,
        ts_utc: str = "",
    ) -> None:
        rid = run_id.strip()
        if not rid:
            return
        sev = (severity or "").strip().lower() or "info"
        if sev not in {"info", "warn", "error"}:
            sev = "info"
        now = ts_utc.strip() or datetime.now(tz=timezone.utc).isoformat()
        payload = details if isinstance(details, dict) else {}
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO run_timeline_events "
                    "(run_id, event_index, ts_utc, stage, severity, message, elapsed_s, details_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    rid,
                    max(0, int(event_index)),
                    now,
                    (stage or "").strip() or "unknown",
                    sev,
                    (message or "").strip() or "event",
                    float(elapsed_s or 0.0),
                    json.dumps(payload, ensure_ascii=True),
                ),
            )

    def list_timeline_events(
        self,
        *,
        run_id: str,
        limit: int = 200,
        after_event_index: int = 0,
        stage: str = "",
        severity: str = "",
        order: str = "asc",
    ) -> list[dict[str, object]]:
        rid = run_id.strip()
        if not rid:
            return []
        where = ["run_id = ?", "event_index > ?"]
        params: list[object] = [rid, max(0, int(after_event_index))]
        stage_filter = stage.strip()
        severity_filter = severity.strip().lower()
        if stage_filter:
            where.append("stage = ?")
            params.append(stage_filter)
        if severity_filter:
            where.append("severity = ?")
            params.append(severity_filter)
        order_sql = "DESC" if order.strip().lower() == "desc" else "ASC"
        params.append(max(1, min(1000, int(limit))))
        query = (
            "SELECT id, run_id, event_index, ts_utc, stage, severity, message, elapsed_s, details_json "
            "FROM run_timeline_events "
            f"WHERE {' AND '.join(where)} "
            f"ORDER BY event_index {order_sql} LIMIT ?"
        )
        with self._conn() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            out.append(
                {
                    "id": int(row[0]),
                    "run_id": str(row[1]),
                    "event_index": int(row[2]),
                    "ts_utc": str(row[3]),
                    "stage": str(row[4]),
                    "severity": str(row[5]),
                    "message": str(row[6]),
                    "elapsed_s": float(row[7] or 0.0),
                    "details": _json_dict(row[8]),
                }
            )
        return out

    def list_timeline_runs(self, limit: int = 50) -> list[dict[str, object]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT r.run_id, r.status, r.started_at, r.window_start, r.window_end, "
                    "(SELECT COUNT(*) FROM run_timeline_events e WHERE e.run_id = r.run_id) AS event_count "
                    "FROM runs r ORDER BY r.started_at DESC LIMIT ?"
                ),
                (max(1, min(500, int(limit))),),
            ).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            out.append(
                {
                    "run_id": str(row[0]),
                    "status": str(row[1]),
                    "started_at": str(row[2]),
                    "window_start": str(row[3]),
                    "window_end": str(row[4]),
                    "event_count": int(row[5] or 0),
                }
            )
        return out

    def timeline_summary(self, *, run_id: str) -> dict[str, object]:
        rid = run_id.strip()
        if not rid:
            return {}
        with self._conn() as conn:
            run_row = conn.execute(
                (
                    "SELECT run_id, status, started_at, source_errors, summary_errors "
                    "FROM runs WHERE run_id = ?"
                ),
                (rid,),
            ).fetchone()
            if run_row is None:
                return {}
            counts_row = conn.execute(
                (
                    "SELECT COUNT(*), "
                    "SUM(CASE WHEN severity = 'error' THEN 1 ELSE 0 END), "
                    "SUM(CASE WHEN severity = 'warn' THEN 1 ELSE 0 END), "
                    "MAX(elapsed_s) "
                    "FROM run_timeline_events WHERE run_id = ?"
                ),
                (rid,),
            ).fetchone()
            last_row = conn.execute(
                (
                    "SELECT stage, message, details_json "
                    "FROM run_timeline_events WHERE run_id = ? "
                    "ORDER BY event_index DESC LIMIT 1"
                ),
                (rid,),
            ).fetchone()

        details = _json_dict(last_row[2]) if last_row is not None else {}
        source_errors = [
            line.strip() for line in str(run_row[3] or "").splitlines() if line.strip()
        ]
        summary_errors = [
            line.strip() for line in str(run_row[4] or "").splitlines() if line.strip()
        ]
        return {
            "run_id": str(run_row[0]),
            "status": str(run_row[1]),
            "started_at": str(run_row[2]),
            "event_count": int((counts_row[0] or 0) if counts_row else 0),
            "error_event_count": int((counts_row[1] or 0) if counts_row else 0),
            "warn_event_count": int((counts_row[2] or 0) if counts_row else 0),
            "duration_s": float((counts_row[3] or 0.0) if counts_row else 0.0),
            "last_stage": str(last_row[0]) if last_row is not None else "",
            "last_message": str(last_row[1]) if last_row is not None else "",
            "final_item_count": int(details.get("final_item_count") or 0),
            "must_read_count": int(details.get("must_read_count") or 0),
            "skim_count": int(details.get("skim_count") or 0),
            "video_count": int(details.get("video_count") or 0),
            "source_error_count": len(source_errors),
            "summary_error_count": len(summary_errors),
        }

    def add_timeline_note(
        self,
        *,
        run_id: str,
        note: str,
        author: str = "",
        labels: list[str] | None = None,
        actions: list[str] | None = None,
    ) -> int:
        rid = run_id.strip()
        text = note.strip()
        if not rid or not text:
            return 0
        now = datetime.now(tz=timezone.utc).isoformat()
        clean_labels = [str(v).strip() for v in (labels or []) if str(v).strip()]
        clean_actions = [str(v).strip() for v in (actions or []) if str(v).strip()]
        with self._conn() as conn:
            cur = conn.execute(
                (
                    "INSERT INTO run_timeline_notes "
                    "(run_id, created_at_utc, author, note, labels_json, actions_json) "
                    "VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (
                    rid,
                    now,
                    author.strip(),
                    text,
                    json.dumps(clean_labels, ensure_ascii=True),
                    json.dumps(clean_actions, ensure_ascii=True),
                ),
            )
            row_id = int(cur.lastrowid or 0)
        return row_id

    def list_timeline_notes(
        self,
        *,
        run_id: str,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        rid = run_id.strip()
        if not rid:
            return []
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT id, run_id, created_at_utc, author, note, labels_json, actions_json "
                    "FROM run_timeline_notes "
                    "WHERE run_id = ? ORDER BY created_at_utc DESC LIMIT ?"
                ),
                (rid, max(1, min(500, int(limit)))),
            ).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            out.append(
                {
                    "id": int(row[0]),
                    "run_id": str(row[1]),
                    "created_at_utc": str(row[2]),
                    "author": str(row[3] or ""),
                    "note": str(row[4] or ""),
                    "labels": _json_list(row[5]),
                    "actions": _json_list(row[6]),
                }
            )
        return out

    def export_timeline(
        self,
        *,
        run_id: str,
        limit_events: int = 2000,
        limit_notes: int = 500,
    ) -> dict[str, object]:
        rid = run_id.strip()
        if not rid:
            return {}
        summary = self.timeline_summary(run_id=rid)
        if not summary:
            return {}
        return {
            "run_id": rid,
            "summary": summary,
            "events": self.list_timeline_events(
                run_id=rid,
                limit=max(1, min(10000, int(limit_events))),
                order="asc",
            ),
            "notes": self.list_timeline_notes(
                run_id=rid,
                limit=max(1, min(2000, int(limit_notes))),
            ),
        }


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
