from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class RunLockState:
    run_id: str
    started_at: str


class RunLock:
    def __init__(self, path: str, stale_seconds: int = 60 * 60 * 6) -> None:
        self.path = Path(path)
        self.stale_seconds = max(60, stale_seconds)

    def acquire(self, run_id: str) -> tuple[bool, RunLockState | None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        current = self.current()
        if current is not None:
            try:
                started = datetime.fromisoformat(current.started_at)
                age = (now - started).total_seconds()
                if age <= self.stale_seconds:
                    return False, current
            except Exception:
                pass
            self._clear()

        payload = {
            "run_id": run_id,
            "started_at": now.isoformat(),
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(self.path)
        return True, None

    def release(self, run_id: str) -> None:
        current = self.current()
        if current is None:
            return
        if current.run_id == run_id:
            self._clear()

    def current(self) -> RunLockState | None:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return None
        run_id = str(data.get("run_id") or "").strip()
        started_at = str(data.get("started_at") or "").strip()
        if not run_id or not started_at:
            return None
        return RunLockState(run_id=run_id, started_at=started_at)

    def _clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except Exception:
            pass
