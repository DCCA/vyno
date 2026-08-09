from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from digest.models import Item
from digest.ops.source_registry import source_key_for

ProgressCallback = Callable[[dict[str, Any]], None]


class RunProgressEmitter:
    def __init__(
        self,
        *,
        run_id: str,
        started_at: datetime,
        progress_cb: ProgressCallback | None,
    ) -> None:
        self.run_id = run_id
        self.started_at = started_at
        self.progress_cb = progress_cb

    def emit(self, stage: str, message: str, **fields: Any) -> None:
        if self.progress_cb is None:
            return
        payload: dict[str, Any] = {
            "run_id": self.run_id,
            "stage": stage,
            "message": message,
            "elapsed_s": round(
                (datetime.now(tz=timezone.utc) - self.started_at).total_seconds(),
                1,
            ),
        }
        payload.update(fields)
        try:
            self.progress_cb(payload)
        except Exception:
            return


def source_link_recorder() -> tuple[
    list[dict[str, str]],
    Callable[[str, str, list[Item]], None],
]:
    """Return an append-only link list plus the recorder that fills it."""
    links: list[dict[str, str]] = []

    def record(source_type: str, source_value: str, items: list[Item]) -> None:
        source_key = source_key_for(source_type, source_value)
        links.extend(
            {
                "source_key": source_key,
                "source_type": source_type,
                "source_value": source_value,
                "item_id": item.id,
            }
            for item in items
        )

    return links, record
