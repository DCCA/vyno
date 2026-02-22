from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from digest.models import Item, Score


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
                """
            )
            self._ensure_column(conn, "scores", "tags_json", "TEXT")
            self._ensure_column(conn, "scores", "topic_tags_json", "TEXT")
            self._ensure_column(conn, "scores", "format_tags_json", "TEXT")
            self._ensure_column(conn, "scores", "provider", "TEXT")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
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

    def finish_run(self, run_id: str, status: str, source_errors: list[str], summary_errors: list[str]) -> None:
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

    def list_runs(self, limit: int = 50) -> list[RunRecord]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT run_id, started_at, window_start, window_end, status FROM runs ORDER BY started_at DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [RunRecord(*r) for r in rows]

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
                (run_id.strip(), item_id.strip(), int(rating), label.strip(), comment.strip(), now),
            )

    def list_feedback(self, limit: int = 200) -> list[tuple[int, str, str, int, str, str, str]]:
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

    def log_admin_action(self, *, actor: str, action: str, target: str, details: str = "") -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                (
                    "INSERT INTO admin_audit (actor, action, target, details, created_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (actor.strip(), action.strip(), target.strip(), details.strip(), now),
            )

    def list_admin_actions(self, limit: int = 200) -> list[tuple[int, str, str, str, str, str]]:
        with self._conn() as conn:
            rows = conn.execute(
                (
                    "SELECT id, actor, action, target, details, created_at "
                    "FROM admin_audit ORDER BY created_at DESC LIMIT ?"
                ),
                (max(1, limit),),
            ).fetchall()
        return [tuple(r) for r in rows]
