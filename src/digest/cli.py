from __future__ import annotations

import argparse
import importlib
import json
import time
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from digest.constants import (
    DEFAULT_RUN_LOCK_STALE_SECONDS,
    WEB_DEFAULT_HOST,
    WEB_DEFAULT_PORT,
)
from digest.config import load_dotenv
from digest.ops.onboarding import OnboardingSettings, run_preflight
from digest.ops.profile_registry import load_effective_profile
from digest.delivery.telegram import (
    answer_telegram_callback,
    get_telegram_updates,
    send_telegram_message,
)
from digest.logging_utils import setup_logging
from digest.ops.run_lock import RunLock
from digest.ops.source_registry import load_effective_sources
from digest.ops.telegram_commands import CommandContext, handle_update
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


def _cmd_run(args: argparse.Namespace) -> int:
    return _execute_run(
        args,
        use_last_completed_window=False,
        only_new=False,
        show_progress=True,
    )


def _execute_run(
    args: argparse.Namespace,
    *,
    use_last_completed_window: bool,
    only_new: bool,
    show_progress: bool,
) -> int:
    sources = load_effective_sources(args.sources, args.sources_overlay)
    profile = load_effective_profile(args.profile, args.profile_overlay)
    store = SQLiteStore(args.db)
    if show_progress:
        print("Starting digest run...", flush=True)
    report = run_digest(
        sources,
        profile,
        store,
        use_last_completed_window=use_last_completed_window,
        only_new=only_new,
        progress_cb=_print_progress if show_progress else None,
    )
    print(f"run_id={report.run_id} status={report.status}")
    for err in report.source_errors:
        print(f"source_error: {err}")
    for err in report.summary_errors:
        print(f"summary_error: {err}")
    return 0


def _cmd_schedule(args: argparse.Namespace) -> int:
    hh, mm = args.time.split(":")
    hour = int(hh)
    minute = int(mm)
    tz = ZoneInfo(args.timezone)

    while True:
        now = datetime.now(tz)
        if now.hour == hour and now.minute == minute:
            _execute_run(
                args,
                use_last_completed_window=True,
                only_new=True,
                show_progress=False,
            )
            time.sleep(61)
        time.sleep(1)


def _cmd_doctor(args: argparse.Namespace) -> int:
    settings = OnboardingSettings(
        sources_path=args.sources,
        sources_overlay_path=args.sources_overlay,
        profile_path=args.profile,
        profile_overlay_path=args.profile_overlay,
        db_path=args.db,
    )
    report = run_preflight(settings)

    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report.get("ok", False) else 1

    print("Digest doctor report")
    print(
        (
            f"status={'ok' if report.get('ok', False) else 'issues'} "
            f"pass={report.get('pass_count', 0)} "
            f"warn={report.get('warn_count', 0)} "
            f"fail={report.get('fail_count', 0)}"
        )
    )

    for check in report.get("checks", []):
        status = str(check.get("status", "")).strip().lower()
        marker = {
            "pass": "PASS",
            "warn": "WARN",
            "fail": "FAIL",
        }.get(status, "INFO")
        label = str(check.get("label", "")).strip() or "check"
        detail = str(check.get("detail", "")).strip()
        hint = str(check.get("hint", "")).strip()
        print(f"[{marker}] {label} - {detail}")
        if hint:
            print(f"  hint: {hint}")

    return 0 if report.get("ok", False) else 1


def _print_progress(event: dict[str, Any]) -> None:
    elapsed = _fmt_elapsed(event.get("elapsed_s"))
    stage = str(event.get("stage", "")).strip()
    message = str(event.get("message", "")).strip()
    extras = _compact_progress_fields(event)
    suffix = f" | {extras}" if extras else ""
    print(f"[{elapsed}] {stage} - {message}{suffix}", flush=True)


def _fmt_elapsed(value: Any) -> str:
    try:
        seconds = max(0.0, float(value))
    except Exception:
        seconds = 0.0
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def _compact_progress_fields(event: dict[str, Any]) -> str:
    keys = [
        "source",
        "channel_id",
        "query",
        "item_count",
        "candidate_count",
        "score_count",
        "scored_item_count",
        "quality_score",
        "threshold",
        "status",
        "error",
        "summary_error_count",
        "source_error_count",
    ]
    parts: list[str] = []
    for key in keys:
        if key not in event:
            continue
        value = event.get(key)
        if value is None:
            continue
        raw = str(value)
        if len(raw) > 90:
            raw = raw[:87].rstrip() + "..."
        parts.append(f"{key}={raw}")
    return " ".join(parts)


def _parse_id_set(raw: str) -> set[str]:
    return {p.strip() for p in (raw or "").split(",") if p.strip()}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _write_bot_health(
    path: str,
    *,
    status: str,
    poll_timeout: int,
    consecutive_errors: int,
    last_error: str,
    last_ok_at: str,
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "updated_at": _utc_now_iso(),
        "last_ok_at": last_ok_at,
        "consecutive_errors": max(0, int(consecutive_errors)),
        "poll_timeout_s": max(1, int(poll_timeout)),
        "last_error": str(last_error or ""),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
    tmp.replace(p)


def _parse_iso_utc(value: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("timestamp is required")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _cmd_bot_health_check(args: argparse.Namespace) -> int:
    health_path = str(args.health_path or "").strip()
    if not health_path:
        print("bot_health_error: --health-path is required")
        return 1
    p = Path(health_path)
    if not p.exists():
        print(f"bot_health_error: missing health file at {health_path}")
        return 1
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"bot_health_error: invalid health payload ({exc})")
        return 1
    if not isinstance(payload, dict):
        print("bot_health_error: health payload is not an object")
        return 1

    status = str(payload.get("status", "")).strip().lower()
    updated_at_raw = str(payload.get("updated_at", "")).strip()
    if not updated_at_raw:
        print("bot_health_error: missing updated_at")
        return 1

    try:
        updated_at = _parse_iso_utc(updated_at_raw)
    except Exception as exc:
        print(f"bot_health_error: invalid updated_at ({exc})")
        return 1

    now = datetime.now(timezone.utc)
    age = max(0.0, (now - updated_at.astimezone(timezone.utc)).total_seconds())
    stale_seconds = max(5, int(args.stale_seconds))
    if age > stale_seconds:
        print(
            f"bot_health_error: stale heartbeat age={int(age)}s threshold={stale_seconds}s"
        )
        return 1

    consecutive_errors = int(payload.get("consecutive_errors", 0) or 0)
    max_error_streak = max(1, int(args.max_error_streak))
    if status == "error" and consecutive_errors > max_error_streak:
        print(
            "bot_health_error: error streak exceeded "
            f"(current={consecutive_errors} threshold={max_error_streak})"
        )
        return 1

    print(
        "bot_health_ok: "
        f"status={status or 'unknown'} age={int(age)}s errors={consecutive_errors}"
    )
    return 0


def _cmd_bot(args: argparse.Namespace) -> int:
    profile = load_effective_profile(args.profile, args.profile_overlay)
    bot_token = (
        profile.output.telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for bot mode")
    admin_chat_ids = _parse_id_set(os.getenv("TELEGRAM_ADMIN_CHAT_IDS", ""))
    admin_user_ids = _parse_id_set(os.getenv("TELEGRAM_ADMIN_USER_IDS", ""))
    if not admin_chat_ids or not admin_user_ids:
        raise RuntimeError(
            "TELEGRAM_ADMIN_CHAT_IDS and TELEGRAM_ADMIN_USER_IDS are required for bot mode"
        )

    lock = RunLock(args.run_lock_path, stale_seconds=args.run_lock_stale_seconds)
    ctx = CommandContext(
        sources_path=args.sources,
        profile_path=args.profile,
        profile_overlay_path=args.profile_overlay,
        db_path=args.db,
        overlay_path=args.sources_overlay,
        admin_chat_ids=admin_chat_ids,
        admin_user_ids=admin_user_ids,
        lock=lock,
        send_message=lambda chat_id, msg, reply_markup=None: send_telegram_message(
            bot_token, chat_id, msg, reply_markup=reply_markup
        ),
        answer_callback=lambda callback_id, text="": answer_telegram_callback(
            bot_token, callback_id, text
        ),
    )

    offset: int | None = None
    last_ok_at = ""
    consecutive_errors = 0
    _write_bot_health(
        args.health_path,
        status="starting",
        poll_timeout=args.poll_timeout,
        consecutive_errors=0,
        last_error="",
        last_ok_at="",
    )
    while True:
        try:
            updates = get_telegram_updates(
                bot_token, offset=offset, timeout=args.poll_timeout
            )
            for upd in updates:
                update_id = int(upd.get("update_id", 0))
                if update_id:
                    offset = update_id + 1
                response = handle_update(upd, ctx)
                if not response:
                    continue
                if response.chat_id and response.text:
                    send_telegram_message(
                        bot_token,
                        response.chat_id,
                        response.text,
                        reply_markup=response.reply_markup,
                    )
                if response.callback_query_id:
                    answer_telegram_callback(
                        bot_token,
                        response.callback_query_id,
                        response.callback_text or "",
                    )
            consecutive_errors = 0
            last_ok_at = _utc_now_iso()
            _write_bot_health(
                args.health_path,
                status="ok",
                poll_timeout=args.poll_timeout,
                consecutive_errors=0,
                last_error="",
                last_ok_at=last_ok_at,
            )
        except Exception as exc:
            consecutive_errors += 1
            _write_bot_health(
                args.health_path,
                status="error",
                poll_timeout=args.poll_timeout,
                consecutive_errors=consecutive_errors,
                last_error=str(exc),
                last_ok_at=last_ok_at,
            )
            print(f"bot_error: {exc}")
            time.sleep(2)


def _cmd_web(args: argparse.Namespace) -> int:
    try:
        uvicorn = importlib.import_module("uvicorn")
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "uvicorn is required for web mode. Install optional web dependencies."
        ) from exc

    from digest.web.app import WebSettings, create_app

    settings = WebSettings(
        sources_path=args.sources,
        sources_overlay_path=args.sources_overlay,
        profile_path=args.profile,
        profile_overlay_path=args.profile_overlay,
        db_path=args.db,
        run_lock_path=args.run_lock_path,
        run_lock_stale_seconds=args.run_lock_stale_seconds,
        history_dir=args.history_dir,
        onboarding_state_path=args.onboarding_state_path,
    )
    app = create_app(settings)
    uvicorn.run(app, host=args.host, port=args.port, reload=False)
    return 0


def main() -> int:
    load_dotenv(".env")
    setup_logging()
    parser = argparse.ArgumentParser(prog="digest")
    parser.add_argument("--sources", default="config/sources.yaml")
    parser.add_argument("--sources-overlay", default="data/sources.local.yaml")
    parser.add_argument("--profile", default="config/profile.yaml")
    parser.add_argument("--profile-overlay", default="data/profile.local.yaml")
    parser.add_argument("--db", default="digest.db")

    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run digest once")
    run_p.set_defaults(func=_cmd_run)

    sched = sub.add_parser("schedule", help="Run digest daily at fixed local time")
    sched.add_argument("--time", default="07:00")
    sched.add_argument("--timezone", default="America/Sao_Paulo")
    sched.set_defaults(func=_cmd_schedule)

    doctor = sub.add_parser("doctor", help="Run onboarding preflight checks")
    doctor.add_argument("--json", action="store_true", help="Output JSON report")
    doctor.set_defaults(func=_cmd_doctor)

    bot = sub.add_parser("bot", help="Run Telegram command bot worker")
    bot.add_argument("--run-lock-path", default=".runtime/run.lock")
    bot.add_argument(
        "--run-lock-stale-seconds",
        type=int,
        default=DEFAULT_RUN_LOCK_STALE_SECONDS,
    )
    bot.add_argument("--poll-timeout", type=int, default=30)
    bot.add_argument("--health-path", default=".runtime/bot-health.json")
    bot.set_defaults(func=_cmd_bot)

    bot_health = sub.add_parser(
        "bot-health-check", help="Check bot health heartbeat for container liveness"
    )
    bot_health.add_argument("--health-path", default=".runtime/bot-health.json")
    bot_health.add_argument("--stale-seconds", type=int, default=90)
    bot_health.add_argument("--max-error-streak", type=int, default=5)
    bot_health.set_defaults(func=_cmd_bot_health_check)

    web = sub.add_parser("web", help="Run config web API server")
    web.add_argument("--host", default=WEB_DEFAULT_HOST)
    web.add_argument("--port", type=int, default=WEB_DEFAULT_PORT)
    web.add_argument("--run-lock-path", default=".runtime/run.lock")
    web.add_argument(
        "--run-lock-stale-seconds",
        type=int,
        default=DEFAULT_RUN_LOCK_STALE_SECONDS,
    )
    web.add_argument("--history-dir", default=".runtime/config-history")
    web.add_argument(
        "--onboarding-state-path", default=".runtime/onboarding-state.json"
    )
    web.set_defaults(func=_cmd_web)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
