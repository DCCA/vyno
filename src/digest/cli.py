from __future__ import annotations

import argparse
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from digest.config import load_dotenv, load_profile, load_sources
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


def _cmd_run(args: argparse.Namespace) -> int:
    return _execute_run(args, use_last_completed_window=False, only_new=False)


def _execute_run(args: argparse.Namespace, *, use_last_completed_window: bool, only_new: bool) -> int:
    sources = load_sources(args.sources)
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


def main() -> int:
    load_dotenv(".env")
    parser = argparse.ArgumentParser(prog="digest")
    parser.add_argument("--sources", default="config/sources.yaml")
    parser.add_argument("--profile", default="config/profile.yaml")
    parser.add_argument("--db", default="digest.db")

    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run digest once")
    run_p.set_defaults(func=_cmd_run)

    sched = sub.add_parser("schedule", help="Run digest daily at fixed local time")
    sched.add_argument("--time", default="07:00")
    sched.add_argument("--timezone", default="America/Sao_Paulo")
    sched.set_defaults(func=_cmd_schedule)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
