from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from digest.config import load_profile
from digest.logging_utils import get_run_logger
from digest.ops.run_lock import RunLock
from digest.ops.source_registry import add_source, list_sources, load_effective_sources, remove_source
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


@dataclass(slots=True)
class AdminConfig:
    sources_path: str
    profile_path: str
    db_path: str
    overlay_path: str
    run_lock_path: str
    bot_pid_path: str
    bot_log_path: str


class AdminService:
    def __init__(self, cfg: AdminConfig) -> None:
        self.cfg = cfg

    @property
    def store(self) -> SQLiteStore:
        return SQLiteStore(self.cfg.db_path)

    def list_sources(self) -> dict[str, list[str]]:
        return list_sources(self.cfg.sources_path, self.cfg.overlay_path)

    def add_source(self, actor: str, source_type: str, value: str) -> tuple[bool, str]:
        created, canonical = add_source(self.cfg.sources_path, self.cfg.overlay_path, source_type, value)
        self.store.log_admin_action(actor=actor, action="source_add", target=f"{source_type}:{canonical}")
        return created, canonical

    def remove_source(self, actor: str, source_type: str, value: str) -> tuple[bool, str]:
        removed, canonical = remove_source(self.cfg.sources_path, self.cfg.overlay_path, source_type, value)
        self.store.log_admin_action(actor=actor, action="source_remove", target=f"{source_type}:{canonical}")
        return removed, canonical

    def run_now(self, actor: str) -> tuple[bool, str]:
        lock = RunLock(self.cfg.run_lock_path)
        run_id = uuid.uuid4().hex[:12]
        acquired, current = lock.acquire(run_id)
        if not acquired and current is not None:
            return False, f"active:{current.run_id}:{current.started_at}"

        def worker() -> None:
            try:
                profile = load_profile(self.cfg.profile_path)
                sources = load_effective_sources(self.cfg.sources_path, self.cfg.overlay_path)
                report = run_digest(
                    sources,
                    profile,
                    self.store,
                    use_last_completed_window=False,
                    only_new=False,
                    logger=get_run_logger(run_id),
                )
                _write_last_telegram_messages(self.cfg.profile_path, report.run_id)
            finally:
                lock.release(run_id)

        threading.Thread(target=worker, daemon=True).start()
        self.store.log_admin_action(actor=actor, action="run_now", target=run_id)
        return True, run_id

    def runs(self, limit: int = 100):
        return self.store.list_runs(limit=limit)

    def logs(self, *, run_id: str = "", stage: str = "", level: str = "", limit: int = 200) -> list[dict]:
        path = Path(os.getenv("DIGEST_LOG_PATH", "logs/digest.log"))
        if not path.exists():
            return []
        rows: list[dict] = []
        for line in reversed(path.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if run_id and str(row.get("run_id", "")) != run_id:
                continue
            if stage and str(row.get("stage", "")) != stage:
                continue
            if level and str(row.get("level", "")).upper() != level.upper():
                continue
            rows.append(row)
            if len(rows) >= max(1, limit):
                break
        return rows

    def outputs(self) -> dict:
        profile = load_profile(self.cfg.profile_path)
        obsidian_latest = ""
        obsidian_preview = ""
        if profile.output.obsidian_vault_path:
            vault = Path(profile.output.obsidian_vault_path) / profile.output.obsidian_folder
            files = sorted(vault.glob("**/*.md"))
            if files:
                latest = files[-1]
                obsidian_latest = str(latest)
                obsidian_preview = latest.read_text(encoding="utf-8")[:8000]

        tel_path = Path(".runtime/last_telegram_messages.json")
        telegram_preview = ""
        if tel_path.exists():
            telegram_preview = tel_path.read_text(encoding="utf-8")[:8000]

        return {
            "obsidian_latest": obsidian_latest,
            "obsidian_preview": obsidian_preview,
            "telegram_preview": telegram_preview,
        }

    def add_feedback(self, actor: str, *, run_id: str, item_id: str, rating: int, label: str, comment: str) -> None:
        self.store.add_feedback(run_id=run_id, item_id=item_id, rating=rating, label=label, comment=comment)
        self.store.log_admin_action(actor=actor, action="feedback_add", target=f"{run_id}:{item_id}")

    def feedback(self, limit: int = 200) -> list[tuple[int, str, str, int, str, str, str]]:
        return self.store.list_feedback(limit=limit)

    def feedback_summary(self) -> list[tuple[int, int]]:
        return self.store.feedback_summary()

    def audit(self, limit: int = 200) -> list[tuple[int, str, str, str, str, str]]:
        return self.store.list_admin_actions(limit=limit)

    def bot_status(self) -> dict[str, str]:
        pid_path = Path(self.cfg.bot_pid_path)
        if not pid_path.exists():
            return {"state": "stopped", "pid": "", "started_at": ""}
        try:
            data = json.loads(pid_path.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            started_at = str(data.get("started_at", ""))
        except Exception:
            return {"state": "stopped", "pid": "", "started_at": ""}
        if pid <= 0 or not _pid_alive(pid):
            return {"state": "stopped", "pid": "", "started_at": ""}
        return {"state": "running", "pid": str(pid), "started_at": started_at}

    def bot_start(self, actor: str) -> tuple[bool, str]:
        status = self.bot_status()
        if status["state"] == "running":
            return False, f"already_running:{status['pid']}"

        log_path = Path(self.cfg.bot_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        out = log_path.open("ab")
        cmd = [
            sys.executable,
            "-m",
            "digest.cli",
            "--sources",
            self.cfg.sources_path,
            "--sources-overlay",
            self.cfg.overlay_path,
            "--profile",
            self.cfg.profile_path,
            "--db",
            self.cfg.db_path,
            "bot",
        ]
        proc = subprocess.Popen(cmd, stdout=out, stderr=out, start_new_session=True)
        out.close()
        payload = {
            "pid": proc.pid,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        pid_path = Path(self.cfg.bot_pid_path)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(json.dumps(payload), encoding="utf-8")
        self.store.log_admin_action(actor=actor, action="bot_start", target=str(proc.pid))
        return True, str(proc.pid)

    def bot_stop(self, actor: str) -> tuple[bool, str]:
        status = self.bot_status()
        if status["state"] != "running":
            return False, "not_running"
        pid = int(status["pid"])
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as exc:
            return False, str(exc)
        Path(self.cfg.bot_pid_path).unlink(missing_ok=True)
        self.store.log_admin_action(actor=actor, action="bot_stop", target=str(pid))
        return True, str(pid)

    def bot_restart(self, actor: str) -> tuple[bool, str]:
        self.bot_stop(actor)
        return self.bot_start(actor)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _write_last_telegram_messages(profile_path: str, run_id: str) -> None:
    # Runtime currently sends messages directly; this panel file is a best-effort
    # marker for latest completed run when run-now is triggered from panel.
    p = Path(".runtime/last_telegram_messages.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"run_id": run_id, "updated_at": datetime.now(timezone.utc).isoformat()}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
