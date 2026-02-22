from __future__ import annotations

import argparse
import time
from datetime import datetime
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

from digest.admin.app import make_admin_service, run_admin_server
from digest.config import load_dotenv, load_profile
from digest.delivery.telegram import answer_telegram_callback, get_telegram_updates, send_telegram_message
from digest.logging_utils import setup_logging
from digest.ops.run_lock import RunLock
from digest.ops.source_registry import load_effective_sources
from digest.ops.telegram_commands import CommandContext, handle_update
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


def _cmd_run(args: argparse.Namespace) -> int:
    return _execute_run(args, use_last_completed_window=False, only_new=False)


def _execute_run(args: argparse.Namespace, *, use_last_completed_window: bool, only_new: bool) -> int:
    sources = load_effective_sources(args.sources, args.sources_overlay)
    profile = load_profile(args.profile)
    store = SQLiteStore(args.db)
    report = run_digest(
        sources,
        profile,
        store,
        use_last_completed_window=use_last_completed_window,
        only_new=only_new,
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
            _execute_run(args, use_last_completed_window=True, only_new=True)
            time.sleep(61)
        time.sleep(1)


def _parse_id_set(raw: str) -> set[str]:
    return {p.strip() for p in (raw or "").split(",") if p.strip()}


def _cmd_bot(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    bot_token = profile.output.telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for bot mode")
    admin_chat_ids = _parse_id_set(os.getenv("TELEGRAM_ADMIN_CHAT_IDS", ""))
    admin_user_ids = _parse_id_set(os.getenv("TELEGRAM_ADMIN_USER_IDS", ""))
    if not admin_chat_ids or not admin_user_ids:
        raise RuntimeError("TELEGRAM_ADMIN_CHAT_IDS and TELEGRAM_ADMIN_USER_IDS are required for bot mode")

    lock = RunLock(args.run_lock_path, stale_seconds=args.run_lock_stale_seconds)
    ctx = CommandContext(
        sources_path=args.sources,
        profile_path=args.profile,
        db_path=args.db,
        overlay_path=args.sources_overlay,
        admin_chat_ids=admin_chat_ids,
        admin_user_ids=admin_user_ids,
        lock=lock,
        send_message=lambda chat_id, msg, reply_markup=None: send_telegram_message(
            bot_token, chat_id, msg, reply_markup=reply_markup
        ),
        answer_callback=lambda callback_id, text="": answer_telegram_callback(bot_token, callback_id, text),
    )

    offset: int | None = None
    while True:
        try:
            updates = get_telegram_updates(bot_token, offset=offset, timeout=args.poll_timeout)
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
                    answer_telegram_callback(bot_token, response.callback_query_id, response.callback_text or "")
        except Exception as exc:
            print(f"bot_error: {exc}")
            time.sleep(2)


def _cmd_admin(args: argparse.Namespace) -> int:
    admin_user = os.getenv("ADMIN_PANEL_USER", "").strip()
    admin_password = os.getenv("ADMIN_PANEL_PASSWORD", "").strip()
    if not admin_user or not admin_password:
        raise RuntimeError("ADMIN_PANEL_USER and ADMIN_PANEL_PASSWORD are required for admin mode")
    service = make_admin_service(
        sources_path=args.sources,
        profile_path=args.profile,
        db_path=args.db,
        overlay_path=args.sources_overlay,
        run_lock_path=args.run_lock_path,
        bot_pid_path=args.bot_pid_path,
        bot_log_path=args.bot_log_path,
    )
    run_admin_server(
        host=args.host,
        port=args.port,
        service=service,
        admin_user=admin_user,
        admin_password=admin_password,
    )
    return 0


def _cmd_admin_streamlit(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["ADMIN_STREAMLIT_SOURCES"] = args.sources
    env["ADMIN_STREAMLIT_PROFILE"] = args.profile
    env["ADMIN_STREAMLIT_DB"] = args.db
    env["ADMIN_STREAMLIT_OVERLAY"] = args.sources_overlay
    env["ADMIN_STREAMLIT_RUN_LOCK"] = args.run_lock_path
    env["ADMIN_STREAMLIT_BOT_PID"] = args.bot_pid_path
    env["ADMIN_STREAMLIT_BOT_LOG"] = args.bot_log_path

    cmd = [
        "streamlit",
        "run",
        "src/digest/admin_streamlit/app.py",
        "--server.address",
        args.host,
        "--server.port",
        str(args.port),
    ]
    try:
        subprocess.run(cmd, check=True, env=env)
    except FileNotFoundError as exc:
        raise RuntimeError("streamlit binary not found. Install with: pip install streamlit") from exc
    return 0


def _cmd_admin_streamlit_prototype(args: argparse.Namespace) -> int:
    cmd = [
        "streamlit",
        "run",
        "src/digest/admin_streamlit/prototype.py",
        "--server.address",
        args.host,
        "--server.port",
        str(args.port),
    ]
    try:
        subprocess.run(cmd, check=True, env=dict(os.environ))
    except FileNotFoundError as exc:
        raise RuntimeError("streamlit binary not found. Install with: pip install streamlit") from exc
    return 0


def main() -> int:
    load_dotenv(".env")
    setup_logging()
    parser = argparse.ArgumentParser(prog="digest")
    parser.add_argument("--sources", default="config/sources.yaml")
    parser.add_argument("--sources-overlay", default="data/sources.local.yaml")
    parser.add_argument("--profile", default="config/profile.yaml")
    parser.add_argument("--db", default="digest.db")

    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run digest once")
    run_p.set_defaults(func=_cmd_run)

    sched = sub.add_parser("schedule", help="Run digest daily at fixed local time")
    sched.add_argument("--time", default="07:00")
    sched.add_argument("--timezone", default="America/Sao_Paulo")
    sched.set_defaults(func=_cmd_schedule)

    bot = sub.add_parser("bot", help="Run Telegram command bot worker")
    bot.add_argument("--run-lock-path", default=".runtime/run.lock")
    bot.add_argument("--run-lock-stale-seconds", type=int, default=21600)
    bot.add_argument("--poll-timeout", type=int, default=30)
    bot.set_defaults(func=_cmd_bot)

    admin = sub.add_parser("admin", help="Run admin web panel")
    admin.add_argument("--host", default="127.0.0.1")
    admin.add_argument("--port", type=int, default=8787)
    admin.add_argument("--run-lock-path", default=".runtime/run.lock")
    admin.add_argument("--bot-pid-path", default=".runtime/bot.pid")
    admin.add_argument("--bot-log-path", default=".runtime/bot.out")
    admin.set_defaults(func=_cmd_admin)

    admin_st = sub.add_parser("admin-streamlit", help="Run Streamlit admin UI")
    admin_st.add_argument("--host", default="127.0.0.1")
    admin_st.add_argument("--port", type=int, default=8788)
    admin_st.add_argument("--run-lock-path", default=".runtime/run.lock")
    admin_st.add_argument("--bot-pid-path", default=".runtime/bot.pid")
    admin_st.add_argument("--bot-log-path", default=".runtime/bot.out")
    admin_st.set_defaults(func=_cmd_admin_streamlit)

    admin_stp = sub.add_parser("admin-streamlit-prototype", help="Run Streamlit UX prototype (no backend writes)")
    admin_stp.add_argument("--host", default="127.0.0.1")
    admin_stp.add_argument("--port", type=int, default=8790)
    admin_stp.set_defaults(func=_cmd_admin_streamlit_prototype)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
