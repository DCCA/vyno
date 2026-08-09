from __future__ import annotations

from datetime import datetime, timezone


def parse_dt(value: str) -> datetime | None:
    """Parse an ISO timestamp, defaulting naive values to UTC.

    Returns None for blank or unparseable input so callers can treat a bad
    stored timestamp as "unknown" rather than crashing a run.
    """
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
