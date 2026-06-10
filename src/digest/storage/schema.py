from __future__ import annotations


SCHEMA_SQL = """
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    source TEXT,
                    author TEXT,
                    published_at TEXT,
                    type TEXT,
                    raw_text TEXT,
                    description TEXT,
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

                CREATE TABLE IF NOT EXISTS x_selector_cursors (
                    selector_type TEXT NOT NULL,
                    selector_value TEXT NOT NULL,
                    cursor TEXT,
                    last_item_id TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (selector_type, selector_value)
                );

                CREATE TABLE IF NOT EXISTS source_item_links (
                    source_key TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_value TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    run_id TEXT,
                    linked_at TEXT NOT NULL,
                    PRIMARY KEY (source_key, item_id)
                );

                CREATE TABLE IF NOT EXISTS link_previews (
                    url TEXT PRIMARY KEY,
                    resolved_url TEXT,
                    host TEXT,
                    title TEXT,
                    description TEXT,
                    image_url TEXT,
                    status TEXT,
                    error TEXT,
                    fetched_at TEXT NOT NULL
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

                CREATE TABLE IF NOT EXISTS run_selected_items (
                    run_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    section TEXT NOT NULL,
                    section_rank INTEGER NOT NULL,
                    source_family TEXT NOT NULL,
                    score_total INTEGER NOT NULL,
                    raw_total INTEGER,
                    adjusted_total INTEGER,
                    adjustment_breakdown_json TEXT,
                    summary TEXT,
                    tags_json TEXT NOT NULL,
                    topic_tags_json TEXT NOT NULL,
                    format_tags_json TEXT NOT NULL,
                    PRIMARY KEY (run_id, item_id)
                );

                CREATE TABLE IF NOT EXISTS run_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    preview_mode INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (run_id, channel, artifact_type)
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
                CREATE INDEX IF NOT EXISTS idx_x_selector_cursors_updated_at
                    ON x_selector_cursors(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_source_item_links_source_key
                    ON source_item_links(source_key, linked_at DESC);
                CREATE INDEX IF NOT EXISTS idx_source_item_links_item_id
                    ON source_item_links(item_id);
                """
