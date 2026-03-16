from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from digest.constants import DEFAULT_RUN_ID_LENGTH
from digest.logging_utils import get_run_logger
from digest.ops.onboarding import OnboardingSettings, run_preflight
from digest.ops.profile_registry import (
    load_effective_profile,
    load_effective_profile_dict,
    save_profile_overlay,
)
from digest.ops.run_lock import RunLock
from digest.ops.source_registry import (
    add_source,
    canonicalize_source_value,
    list_sources,
    load_effective_sources,
    remove_source,
    supported_source_types,
)
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore

WIZARD_TTL_SECONDS = 15 * 60
VALID_DEPTHS = {"practical", "balanced", "deep_technical"}
HH_MM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

BOT_COMMANDS = [
    {"command": "status", "description": "Run status, schedule, and sources overview"},
    {"command": "digest", "description": "Trigger a digest run"},
    {"command": "schedule", "description": "View and control the schedule"},
    {"command": "history", "description": "Recent run history"},
    {"command": "doctor", "description": "System health check"},
    {"command": "settings", "description": "Content depth and preferences"},
    {"command": "source", "description": "Manage sources (add/remove/list)"},
    {"command": "feedback", "description": "Mute or trust sources"},
    {"command": "help", "description": "Show all commands"},
]


@dataclass(slots=True)
class CommandContext:
    sources_path: str
    profile_path: str
    profile_overlay_path: str
    db_path: str
    overlay_path: str
    admin_chat_ids: set[str]
    admin_user_ids: set[str]
    lock: RunLock
    send_message: Callable[[str, str, dict | None], None]
    answer_callback: Callable[[str, str], None] | None = None
    web_public_url: str = ""
    wizard_state: dict[tuple[str, str], dict] = field(default_factory=dict)


@dataclass(slots=True)
class BotResponse:
    chat_id: str | None = None
    text: str | None = None
    reply_markup: dict | None = None
    callback_query_id: str | None = None
    callback_text: str | None = None
    edit_message_id: int | None = None


# ── Main dispatch ────────────────────────────────────────────────────


def handle_update(update: dict, ctx: CommandContext) -> BotResponse | None:
    _expire_wizard_state(ctx)

    cb = update.get("callback_query")
    if isinstance(cb, dict):
        return _handle_callback_query(cb, ctx)

    msg = extract_message(update)
    if msg is None:
        return None
    text, chat_id, user_id = msg

    if not _is_authorized(chat_id, user_id, ctx):
        return BotResponse(chat_id=chat_id, text="Not authorized.")

    state = _get_state(ctx, chat_id, user_id)
    if state.get("awaiting_value") and not text.startswith("/"):
        wizard = state.get("wizard", "source")
        if wizard == "schedule":
            return _handle_schedule_value_input(chat_id, user_id, text, ctx)
        if wizard == "settings":
            return _handle_settings_value_input(chat_id, user_id, text, ctx)
        return _handle_wizard_value_input(chat_id, user_id, text, ctx)

    cmd, args = _parse_command(text)
    if cmd in {"/help", "/start"}:
        return BotResponse(chat_id=chat_id, text=_help_text())
    if cmd == "/status":
        return BotResponse(
            chat_id=chat_id,
            text=_status_text(ctx),
            reply_markup=_status_keyboard(ctx),
        )
    if cmd == "/digest":
        if len(args) == 1 and args[0] == "run":
            return BotResponse(chat_id=chat_id, text=_trigger_run(ctx, chat_id))
        return BotResponse(chat_id=chat_id, text="Usage: /digest run")
    if cmd == "/source":
        return BotResponse(
            chat_id=chat_id,
            text=_handle_source(args, ctx, chat_id, user_id),
            reply_markup=_wizard_action_keyboard()
            if args and args[0] == "wizard"
            else None,
        )
    if cmd == "/schedule":
        return _handle_schedule_command(args, ctx, chat_id, user_id)
    if cmd == "/history":
        return _handle_history_command(args, ctx, chat_id)
    if cmd == "/doctor":
        return BotResponse(chat_id=chat_id, text=_doctor_text(ctx))
    if cmd == "/settings":
        return _handle_settings_command(args, ctx, chat_id, user_id)
    if cmd == "/feedback":
        return _handle_feedback_command(args, ctx, chat_id)

    return BotResponse(chat_id=chat_id, text="Unknown command. Use /help")


def extract_message(update: dict) -> tuple[str, str, str] | None:
    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict):
        return None
    text = str(message.get("text") or "").strip()
    chat_id = str((message.get("chat") or {}).get("id") or "").strip()
    user_id = str((message.get("from") or {}).get("id") or "").strip()
    if not text or not chat_id or not user_id:
        return None
    return text, chat_id, user_id


# ── Callback dispatcher ─────────────────────────────────────────────


def _handle_callback_query(callback: dict, ctx: CommandContext) -> BotResponse:
    callback_id = str(callback.get("id") or "").strip()
    data = str(callback.get("data") or "").strip()
    message = callback.get("message") or {}
    chat_id = str((message.get("chat") or {}).get("id") or "").strip()
    user_id = str((callback.get("from") or {}).get("id") or "").strip()
    message_id = int(message.get("message_id") or 0)

    if not chat_id or not user_id:
        return BotResponse(
            callback_query_id=callback_id, callback_text="Invalid callback"
        )

    if not _is_authorized(chat_id, user_id, ctx):
        return BotResponse(
            chat_id=chat_id,
            text="Not authorized.",
            callback_query_id=callback_id,
            callback_text="Not authorized",
        )

    if data.startswith("sw:"):
        return _handle_source_callback(
            data[3:], chat_id, user_id, callback_id, message_id, ctx
        )
    if data.startswith("sch:"):
        return _handle_schedule_callback(
            data[4:], chat_id, user_id, callback_id, message_id, ctx
        )
    if data.startswith("cfg:"):
        return _handle_settings_callback(
            data[4:], chat_id, user_id, callback_id, message_id, ctx
        )
    if data.startswith("hist:"):
        return _handle_history_callback(
            data[5:], chat_id, callback_id, message_id, ctx
        )
    if data.startswith("st:"):
        return _handle_status_callback(
            data[3:], chat_id, user_id, callback_id, message_id, ctx
        )

    return BotResponse(callback_query_id=callback_id, callback_text="Unsupported action")


# ── Source wizard (sw: prefix) ───────────────────────────────────────


def _handle_source_callback(
    key: str,
    chat_id: str,
    user_id: str,
    callback_id: str,
    message_id: int,
    ctx: CommandContext,
) -> BotResponse:
    state = _get_state(ctx, chat_id, user_id)
    state["wizard"] = "source"

    if key in {"add", "remove", "list"}:
        state.update(
            {
                "action": key,
                "source_type": "",
                "awaiting_value": False,
                "draft_value": "",
            }
        )
        return BotResponse(
            chat_id=chat_id,
            text=f"Selected action: {key}. Choose source type:",
            reply_markup=_wizard_type_keyboard(),
            callback_query_id=callback_id,
            callback_text="Action selected",
        )

    if key.startswith("t:"):
        source_type = key.split(":", 1)[1].strip()
        if source_type not in supported_source_types():
            return BotResponse(
                callback_query_id=callback_id, callback_text="Unknown source type"
            )
        state["source_type"] = source_type
        action = state.get("action", "")
        if action == "list":
            listing = list_sources(ctx.sources_path, ctx.overlay_path)
            return BotResponse(
                chat_id=chat_id,
                text=_render_source_list({source_type: listing.get(source_type, [])}),
                reply_markup=_wizard_action_keyboard(),
                callback_query_id=callback_id,
                callback_text="Listed",
            )
        state["awaiting_value"] = True
        state["draft_value"] = ""
        return BotResponse(
            chat_id=chat_id,
            text=(
                f"Send value for <code>{source_type}</code> now.\n"
                "Examples:\n"
                "- github_org: https://github.com/vercel-labs\n"
                "- github_repo: openai/openai-cookbook"
            ),
            reply_markup=_wizard_cancel_keyboard(),
            callback_query_id=callback_id,
            callback_text="Type selected",
        )

    if key == "ok":
        action = state.get("action", "")
        source_type = state.get("source_type", "")
        draft_value = state.get("draft_value", "")
        if action not in {"add", "remove"} or not source_type or not draft_value:
            return BotResponse(
                callback_query_id=callback_id, callback_text="Nothing to confirm"
            )
        try:
            if action == "add":
                created, canonical = add_source(
                    ctx.sources_path, ctx.overlay_path, source_type, draft_value
                )
                msg = (
                    f"Added {source_type}: {canonical}"
                    if created
                    else f"Already tracked: {canonical}"
                )
            else:
                removed, canonical = remove_source(
                    ctx.sources_path, ctx.overlay_path, source_type, draft_value
                )
                msg = (
                    f"Removed {source_type}: {canonical}"
                    if removed
                    else f"Not found: {canonical}"
                )
        except Exception as exc:
            msg = f"Source command failed: {exc}"
        _clear_state(ctx, chat_id, user_id)
        return BotResponse(
            chat_id=chat_id,
            text=msg,
            reply_markup=_wizard_action_keyboard(),
            callback_query_id=callback_id,
            callback_text="Saved",
        )

    if key == "back":
        state.update({"source_type": "", "awaiting_value": False, "draft_value": ""})
        return BotResponse(
            chat_id=chat_id,
            text="Back. Choose source type:",
            reply_markup=_wizard_type_keyboard(),
            callback_query_id=callback_id,
            callback_text="Back",
        )

    if key == "cancel":
        _clear_state(ctx, chat_id, user_id)
        return BotResponse(
            chat_id=chat_id,
            text="Source wizard canceled.",
            reply_markup=_wizard_action_keyboard(),
            callback_query_id=callback_id,
            callback_text="Canceled",
        )

    return BotResponse(callback_query_id=callback_id, callback_text="Unknown action")


def _handle_wizard_value_input(
    chat_id: str, user_id: str, raw_value: str, ctx: CommandContext
) -> BotResponse:
    state = _get_state(ctx, chat_id, user_id)
    source_type = state.get("source_type", "")
    action = state.get("action", "")
    try:
        canonical = canonicalize_source_value(source_type, raw_value)
    except Exception as exc:
        return BotResponse(
            chat_id=chat_id,
            text=f"Invalid value: {exc}",
            reply_markup=_wizard_cancel_keyboard(),
        )
    state["draft_value"] = canonical
    state["awaiting_value"] = False
    return BotResponse(
        chat_id=chat_id,
        text=f"Confirm {action} for {source_type}:\n<code>{canonical}</code>",
        reply_markup=_wizard_confirm_keyboard(),
    )


# ── Schedule (sch: prefix) ──────────────────────────────────────────


def _handle_schedule_command(
    args: list[str], ctx: CommandContext, chat_id: str, user_id: str
) -> BotResponse:
    if not args:
        return BotResponse(
            chat_id=chat_id,
            text=_schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
        )
    action = args[0]
    if action == "on":
        _save_schedule_field(ctx, "enabled", True)
        return BotResponse(
            chat_id=chat_id,
            text="Schedule <b>enabled</b>.\n\n" + _schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
        )
    if action == "off":
        _save_schedule_field(ctx, "enabled", False)
        return BotResponse(
            chat_id=chat_id,
            text="Schedule <b>disabled</b>.\n\n" + _schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
        )
    if action == "time" and len(args) >= 2:
        time_val = args[1].strip()
        if not HH_MM_RE.match(time_val):
            return BotResponse(
                chat_id=chat_id,
                text="Invalid time. Use HH:MM format (e.g. 14:30).",
            )
        _save_schedule_field(ctx, "time_local", time_val)
        return BotResponse(
            chat_id=chat_id,
            text=f"Schedule time set to <b>{time_val}</b>.\n\n"
            + _schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
        )
    if action == "cadence" and len(args) >= 2:
        cadence = args[1].strip()
        if cadence not in {"daily", "hourly"}:
            return BotResponse(
                chat_id=chat_id, text="Cadence must be <b>daily</b> or <b>hourly</b>."
            )
        _save_schedule_field(ctx, "cadence", cadence)
        return BotResponse(
            chat_id=chat_id,
            text=f"Cadence set to <b>{cadence}</b>.\n\n"
            + _schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
        )
    return BotResponse(
        chat_id=chat_id,
        text=(
            "Usage:\n"
            "/schedule — view status\n"
            "/schedule on|off — toggle\n"
            "/schedule time HH:MM\n"
            "/schedule cadence daily|hourly"
        ),
    )


def _handle_schedule_callback(
    key: str,
    chat_id: str,
    user_id: str,
    callback_id: str,
    message_id: int,
    ctx: CommandContext,
) -> BotResponse:
    if key == "toggle":
        profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
        schedule = profile.get("schedule") or {}
        new_val = not bool(schedule.get("enabled", False))
        _save_schedule_field(ctx, "enabled", new_val)
        label = "enabled" if new_val else "disabled"
        return BotResponse(
            chat_id=chat_id,
            text=f"Schedule <b>{label}</b>.\n\n" + _schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
            edit_message_id=message_id,
            callback_query_id=callback_id,
            callback_text=f"Schedule {label}",
        )

    if key == "time":
        state = _get_state(ctx, chat_id, user_id)
        state["wizard"] = "schedule"
        state["action"] = "time"
        state["awaiting_value"] = True
        return BotResponse(
            chat_id=chat_id,
            text="Send new time in <b>HH:MM</b> format (24h).\nExample: 14:30",
            reply_markup=_cancel_keyboard("sch:cancel"),
            callback_query_id=callback_id,
            callback_text="Enter time",
        )

    if key.startswith("c:"):
        cadence = key[2:]
        if cadence in {"daily", "hourly"}:
            _save_schedule_field(ctx, "cadence", cadence)
            return BotResponse(
                chat_id=chat_id,
                text=f"Cadence set to <b>{cadence}</b>.\n\n"
                + _schedule_status_text(ctx),
                reply_markup=_schedule_keyboard(ctx),
                edit_message_id=message_id,
                callback_query_id=callback_id,
                callback_text=f"Cadence: {cadence}",
            )

    if key == "cadence":
        return BotResponse(
            chat_id=chat_id,
            text="Choose cadence:",
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "Daily", "callback_data": "sch:c:daily"},
                        {"text": "Hourly", "callback_data": "sch:c:hourly"},
                    ],
                    [{"text": "Back", "callback_data": "sch:back"}],
                ]
            },
            edit_message_id=message_id,
            callback_query_id=callback_id,
            callback_text="Choose cadence",
        )

    if key in {"back", "cancel"}:
        _clear_state(ctx, chat_id, user_id)
        return BotResponse(
            chat_id=chat_id,
            text=_schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
            edit_message_id=message_id,
            callback_query_id=callback_id,
            callback_text="Back",
        )

    return BotResponse(callback_query_id=callback_id, callback_text="Unknown action")


def _handle_schedule_value_input(
    chat_id: str, user_id: str, raw_value: str, ctx: CommandContext
) -> BotResponse:
    state = _get_state(ctx, chat_id, user_id)
    action = state.get("action", "")
    value = raw_value.strip()

    if action == "time":
        if not HH_MM_RE.match(value):
            return BotResponse(
                chat_id=chat_id,
                text="Invalid time. Use HH:MM format (e.g. 14:30).",
                reply_markup=_cancel_keyboard("sch:cancel"),
            )
        _save_schedule_field(ctx, "time_local", value)
        _clear_state(ctx, chat_id, user_id)
        return BotResponse(
            chat_id=chat_id,
            text=f"Schedule time set to <b>{value}</b>.\n\n"
            + _schedule_status_text(ctx),
            reply_markup=_schedule_keyboard(ctx),
        )

    _clear_state(ctx, chat_id, user_id)
    return BotResponse(chat_id=chat_id, text="Unexpected input.")


def _schedule_status_text(ctx: CommandContext) -> str:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    schedule = profile.get("schedule") or {}
    enabled = bool(schedule.get("enabled", False))
    cadence = str(schedule.get("cadence", "daily") or "daily")
    time_local = str(schedule.get("time_local", "09:00") or "09:00")
    tz = str(schedule.get("timezone", "UTC") or "UTC")
    quiet = bool(schedule.get("quiet_hours_enabled", False))
    quiet_start = str(schedule.get("quiet_start_local", "22:00") or "22:00")
    quiet_end = str(schedule.get("quiet_end_local", "07:00") or "07:00")

    status = "Enabled" if enabled else "Disabled"
    lines = [
        f"<b>Schedule</b>: {status}",
        f"<b>Cadence</b>: {cadence} at {time_local}",
        f"<b>Timezone</b>: {tz}",
    ]
    if quiet:
        lines.append(f"<b>Quiet hours</b>: {quiet_start}–{quiet_end}")
    else:
        lines.append("<b>Quiet hours</b>: off")
    return "\n".join(lines)


def _save_schedule_field(ctx: CommandContext, field: str, value: Any) -> None:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    schedule = dict(profile.get("schedule") or {})
    schedule[field] = value
    profile["schedule"] = schedule
    save_profile_overlay(ctx.profile_path, ctx.profile_overlay_path, profile)


def _schedule_keyboard(ctx: CommandContext) -> dict:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    schedule = profile.get("schedule") or {}
    enabled = bool(schedule.get("enabled", False))
    toggle_text = "Disable" if enabled else "Enable"

    rows: list[list[dict]] = [
        [
            {"text": toggle_text, "callback_data": "sch:toggle"},
            {"text": "Change Time", "callback_data": "sch:time"},
            {"text": "Cadence", "callback_data": "sch:cadence"},
        ],
    ]
    if ctx.web_public_url:
        rows.append(
            [{"text": "Open in Console", "web_app": {"url": f"{ctx.web_public_url}/schedule"}}]
        )
    return {"inline_keyboard": rows}


# ── History (hist: prefix) ──────────────────────────────────────────


def _handle_history_command(
    args: list[str], ctx: CommandContext, chat_id: str
) -> BotResponse:
    store = SQLiteStore(ctx.db_path)

    if args and args[0] == "last":
        return BotResponse(chat_id=chat_id, text=_run_detail_text(store))

    if args:
        run_id = args[0]
        return BotResponse(chat_id=chat_id, text=_run_detail_text(store, run_id))

    runs = store.list_runs(limit=5)
    if not runs:
        return BotResponse(chat_id=chat_id, text="No runs found.")

    lines = ["<b>Recent Runs</b>\n"]
    buttons: list[list[dict]] = []
    for r in runs:
        status_icon = "\u2713" if r.status == "completed" else "\u2717"
        started = str(r.started_at or "")[:16]
        lines.append(
            f"<code>{r.run_id}</code> {status_icon} {r.status} \u00b7 {started}"
        )
        buttons.append(
            [{"text": f"Details: {r.run_id}", "callback_data": f"hist:{r.run_id}"}]
        )
    if ctx.web_public_url:
        buttons.append(
            [{"text": "Open in Console", "web_app": {"url": f"{ctx.web_public_url}/"}}]
        )
    return BotResponse(
        chat_id=chat_id,
        text="\n".join(lines),
        reply_markup={"inline_keyboard": buttons},
    )


def _handle_history_callback(
    key: str,
    chat_id: str,
    callback_id: str,
    message_id: int,
    ctx: CommandContext,
) -> BotResponse:
    store = SQLiteStore(ctx.db_path)
    return BotResponse(
        chat_id=chat_id,
        text=_run_detail_text(store, key),
        callback_query_id=callback_id,
        callback_text="Run details",
    )


def _run_detail_text(store: SQLiteStore, run_id: str | None = None) -> str:
    if run_id:
        row = store.latest_run_details(completed_only=False)
        if row and row[0] != run_id:
            return f"Run <code>{run_id}</code> not found in latest."
    else:
        row = store.latest_run_details(completed_only=True)
    if not row:
        return "No completed runs found."
    rid, status, started, src_errs, sum_errs = row
    lines = [
        f"<b>Run</b>: <code>{rid}</code>",
        f"<b>Status</b>: {status}",
        f"<b>Started</b>: {started}",
    ]
    if src_errs:
        lines.append(f"<b>Source errors</b> ({len(src_errs)}):")
        for e in src_errs[:10]:
            lines.append(f"  - {e[:80]}")
        if len(src_errs) > 10:
            lines.append(f"  ... +{len(src_errs) - 10} more")
    if sum_errs:
        lines.append(f"<b>Summary errors</b> ({len(sum_errs)}):")
        for e in sum_errs[:5]:
            lines.append(f"  - {e[:80]}")
    return "\n".join(lines)


# ── Doctor ───────────────────────────────────────────────────────────


def _doctor_text(ctx: CommandContext) -> str:
    settings = OnboardingSettings(
        sources_path=ctx.sources_path,
        sources_overlay_path=ctx.overlay_path,
        profile_path=ctx.profile_path,
        profile_overlay_path=ctx.profile_overlay_path,
        db_path=ctx.db_path,
    )
    report = run_preflight(settings)
    checks = report.get("checks", [])
    lines = ["<b>System Health</b>\n"]
    for check in checks:
        status = str(check.get("status", "")).strip().upper()
        label = str(check.get("label", "")).strip()
        marker = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}.get(
            status, "[INFO]"
        )
        lines.append(f"{marker} {label}")
        hint = str(check.get("hint", "")).strip()
        if hint and status in {"WARN", "FAIL"}:
            lines.append(f"  <i>{hint}</i>")

    pc = report.get("pass_count", 0)
    wc = report.get("warn_count", 0)
    fc = report.get("fail_count", 0)
    lines.append(f"\n<b>Result</b>: {pc} pass, {wc} warn, {fc} fail")
    return "\n".join(lines)


# ── Settings (cfg: prefix) ──────────────────────────────────────────


def _handle_settings_command(
    args: list[str], ctx: CommandContext, chat_id: str, user_id: str
) -> BotResponse:
    if not args:
        return BotResponse(
            chat_id=chat_id,
            text=_settings_status_text(ctx),
            reply_markup=_settings_keyboard(ctx),
        )
    if args[0] == "depth" and len(args) >= 2:
        depth = args[1].strip()
        if depth not in VALID_DEPTHS:
            return BotResponse(
                chat_id=chat_id,
                text=f"Invalid depth. Choose: {', '.join(sorted(VALID_DEPTHS))}",
            )
        _save_profile_field(ctx, "content_depth_preference", depth)
        return BotResponse(
            chat_id=chat_id,
            text=f"Content depth set to <b>{depth}</b>.",
            reply_markup=_settings_keyboard(ctx),
        )
    return BotResponse(
        chat_id=chat_id,
        text=(
            "Usage:\n"
            "/settings — view current\n"
            "/settings depth practical|balanced|deep_technical"
        ),
    )


def _handle_settings_callback(
    key: str,
    chat_id: str,
    user_id: str,
    callback_id: str,
    message_id: int,
    ctx: CommandContext,
) -> BotResponse:
    if key.startswith("d:"):
        depth = key[2:]
        if depth in VALID_DEPTHS:
            _save_profile_field(ctx, "content_depth_preference", depth)
            return BotResponse(
                chat_id=chat_id,
                text=f"Content depth set to <b>{depth}</b>.\n\n"
                + _settings_status_text(ctx),
                reply_markup=_settings_keyboard(ctx),
                edit_message_id=message_id,
                callback_query_id=callback_id,
                callback_text=f"Depth: {depth}",
            )

    if key == "topics":
        state = _get_state(ctx, chat_id, user_id)
        state["wizard"] = "settings"
        state["action"] = "add_topic"
        state["awaiting_value"] = True
        profile = load_effective_profile_dict(
            ctx.profile_path, ctx.profile_overlay_path
        )
        topics = profile.get("topics") or []
        current = ", ".join(topics) if topics else "none"
        return BotResponse(
            chat_id=chat_id,
            text=f"Current topics: <i>{current}</i>\n\nSend a topic to add:",
            reply_markup=_cancel_keyboard("cfg:cancel"),
            edit_message_id=message_id,
            callback_query_id=callback_id,
            callback_text="Add topic",
        )

    if key == "cancel":
        _clear_state(ctx, chat_id, user_id)
        return BotResponse(
            chat_id=chat_id,
            text=_settings_status_text(ctx),
            reply_markup=_settings_keyboard(ctx),
            edit_message_id=message_id,
            callback_query_id=callback_id,
            callback_text="Canceled",
        )

    return BotResponse(callback_query_id=callback_id, callback_text="Unknown action")


def _handle_settings_value_input(
    chat_id: str, user_id: str, raw_value: str, ctx: CommandContext
) -> BotResponse:
    state = _get_state(ctx, chat_id, user_id)
    action = state.get("action", "")
    value = raw_value.strip()

    if action == "add_topic" and value:
        profile = load_effective_profile_dict(
            ctx.profile_path, ctx.profile_overlay_path
        )
        topics = list(profile.get("topics") or [])
        if value not in topics:
            topics.append(value)
            profile["topics"] = topics
            save_profile_overlay(
                ctx.profile_path, ctx.profile_overlay_path, profile
            )
        _clear_state(ctx, chat_id, user_id)
        return BotResponse(
            chat_id=chat_id,
            text=f"Topic <b>{value}</b> added.\n\n" + _settings_status_text(ctx),
            reply_markup=_settings_keyboard(ctx),
        )

    _clear_state(ctx, chat_id, user_id)
    return BotResponse(chat_id=chat_id, text="Unexpected input.")


def _settings_status_text(ctx: CommandContext) -> str:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    depth = str(profile.get("content_depth_preference", "balanced") or "balanced")
    topics = profile.get("topics") or []
    exclusions = profile.get("exclusions") or []
    topics_str = ", ".join(topics[:10]) if topics else "none"
    excl_str = ", ".join(exclusions[:10]) if exclusions else "none"
    return (
        f"<b>Content depth</b>: {depth}\n"
        f"<b>Topics</b>: {topics_str}\n"
        f"<b>Exclusions</b>: {excl_str}"
    )


def _settings_keyboard(ctx: CommandContext) -> dict:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    current = str(profile.get("content_depth_preference", "balanced") or "balanced")
    depth_buttons = []
    for d in ["practical", "balanced", "deep_technical"]:
        label = d.replace("_", " ").title()
        if d == current:
            label = f"\u2713 {label}"
        depth_buttons.append({"text": label, "callback_data": f"cfg:d:{d}"})
    rows: list[list[dict]] = [
        depth_buttons,
        [{"text": "Add Topic", "callback_data": "cfg:topics"}],
    ]
    if ctx.web_public_url:
        rows.append(
            [{"text": "Open in Console", "web_app": {"url": f"{ctx.web_public_url}/profile"}}]
        )
    return {"inline_keyboard": rows}


def _save_profile_field(ctx: CommandContext, field: str, value: Any) -> None:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    profile[field] = value
    save_profile_overlay(ctx.profile_path, ctx.profile_overlay_path, profile)


# ── Feedback ─────────────────────────────────────────────────────────


def _handle_feedback_command(
    args: list[str], ctx: CommandContext, chat_id: str
) -> BotResponse:
    if not args:
        return BotResponse(
            chat_id=chat_id,
            text=(
                "Usage:\n"
                "/feedback mute &lt;type&gt; &lt;value&gt;\n"
                "/feedback trust &lt;type&gt; &lt;value&gt;\n"
                "/feedback summary"
            ),
        )

    action = args[0]
    if action == "summary":
        store = SQLiteStore(ctx.db_path)
        rows = store.feedback_summary()
        if not rows:
            return BotResponse(chat_id=chat_id, text="No feedback recorded yet.")
        lines = ["<b>Feedback Summary</b>\n"]
        labels = {1: "Positive", 0: "Neutral", -1: "Negative", -2: "Spam"}
        for rating, count in rows:
            label = labels.get(rating, f"Rating {rating}")
            lines.append(f"  {label}: {count}")
        return BotResponse(chat_id=chat_id, text="\n".join(lines))

    if action in {"mute", "trust"} and len(args) >= 3:
        source_type = args[1]
        source_value = " ".join(args[2:]).strip()
        try:
            _apply_source_preference(ctx, action, source_type, source_value)
        except Exception as exc:
            return BotResponse(chat_id=chat_id, text=f"Failed: {exc}")
        verb = "muted (blocked)" if action == "mute" else "trusted"
        return BotResponse(
            chat_id=chat_id,
            text=f"Source <b>{verb}</b>: {source_type} / {source_value}",
        )

    return BotResponse(
        chat_id=chat_id,
        text="Usage: /feedback mute|trust &lt;type&gt; &lt;value&gt;",
    )


def _apply_source_preference(
    ctx: CommandContext, action: str, source_type: str, source_value: str
) -> None:
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    if action == "mute":
        if source_type.startswith("x_"):
            key = "blocked_authors_x"
        elif source_type.startswith("github_"):
            key = "blocked_orgs_github"
        else:
            key = "blocked_sources"
        blocked = list(profile.get(key) or [])
        if source_value not in blocked:
            blocked.append(source_value)
            profile[key] = blocked
            save_profile_overlay(
                ctx.profile_path, ctx.profile_overlay_path, profile
            )
    elif action == "trust":
        if source_type.startswith("x_"):
            key = "trusted_authors_x"
        elif source_type.startswith("github_"):
            key = "trusted_orgs_github"
        else:
            key = "trusted_sources"
        trusted = list(profile.get(key) or [])
        if source_value not in trusted:
            trusted.append(source_value)
            profile[key] = trusted
            save_profile_overlay(
                ctx.profile_path, ctx.profile_overlay_path, profile
            )


# ── Enhanced /status ─────────────────────────────────────────────────


def _status_text(ctx: CommandContext) -> str:
    lock_state = ctx.lock.current()
    store = SQLiteStore(ctx.db_path)
    row = store.latest_run_summary()

    # Schedule summary
    profile = load_effective_profile_dict(ctx.profile_path, ctx.profile_overlay_path)
    schedule = profile.get("schedule") or {}
    sch_enabled = bool(schedule.get("enabled", False))
    cadence = str(schedule.get("cadence", "daily") or "daily")
    time_local = str(schedule.get("time_local", "09:00") or "09:00")
    tz = str(schedule.get("timezone", "UTC") or "UTC")

    # Sources summary
    sources = list_sources(ctx.sources_path, ctx.overlay_path)
    total_sources = sum(len(v) for v in sources.values())

    lines = ["<b>Vyno Status</b>\n"]

    if sch_enabled:
        lines.append(f"<b>Schedule</b>: {cadence} at {time_local} ({tz})")
    else:
        lines.append("<b>Schedule</b>: disabled")

    if lock_state is not None:
        lines.append(
            f"<b>Active run</b>: <code>{lock_state.run_id}</code>"
        )
    else:
        lines.append("<b>Active run</b>: none")

    if row:
        lines.append(
            f"<b>Last run</b>: <code>{row[0]}</code> {row[1]} \u00b7 {row[3]} src err, {row[4]} sum err"
        )
    else:
        lines.append("<b>Last run</b>: none")

    lines.append(f"<b>Sources</b>: {total_sources} configured")
    return "\n".join(lines)


def _status_keyboard(ctx: CommandContext) -> dict:
    rows: list[list[dict]] = [
        [
            {"text": "\u25b6 Run Now", "callback_data": "st:run"},
            {"text": "History", "callback_data": "st:history"},
            {"text": "Doctor", "callback_data": "st:doctor"},
        ],
    ]
    if ctx.web_public_url:
        rows.append(
            [{"text": "Open Console", "web_app": {"url": ctx.web_public_url}}]
        )
    return {"inline_keyboard": rows}


def _handle_status_callback(
    key: str,
    chat_id: str,
    user_id: str,
    callback_id: str,
    message_id: int,
    ctx: CommandContext,
) -> BotResponse:
    if key == "run":
        return BotResponse(
            chat_id=chat_id,
            text=_trigger_run(ctx, chat_id),
            callback_query_id=callback_id,
            callback_text="Run triggered",
        )
    if key == "history":
        store = SQLiteStore(ctx.db_path)
        runs = store.list_runs(limit=5)
        if not runs:
            return BotResponse(
                chat_id=chat_id,
                text="No runs found.",
                callback_query_id=callback_id,
                callback_text="No runs",
            )
        lines = ["<b>Recent Runs</b>\n"]
        for r in runs:
            status_icon = "\u2713" if r.status == "completed" else "\u2717"
            started = str(r.started_at or "")[:16]
            lines.append(
                f"<code>{r.run_id}</code> {status_icon} {r.status} \u00b7 {started}"
            )
        return BotResponse(
            chat_id=chat_id,
            text="\n".join(lines),
            callback_query_id=callback_id,
            callback_text="History",
        )
    if key == "doctor":
        return BotResponse(
            chat_id=chat_id,
            text=_doctor_text(ctx),
            callback_query_id=callback_id,
            callback_text="Doctor",
        )
    return BotResponse(callback_query_id=callback_id, callback_text="Unknown")


# ── Shared: source commands, trigger, help ───────────────────────────


def _handle_source(
    args: list[str], ctx: CommandContext, chat_id: str, user_id: str
) -> str:
    if not args:
        return "Usage: /source &lt;add|remove|list|wizard&gt; ..."

    action = args[0]
    if action == "wizard":
        _clear_state(ctx, chat_id, user_id)
        return "Source wizard started. Choose an action:"

    if action == "list":
        st = args[1] if len(args) > 1 else ""
        listing = list_sources(ctx.sources_path, ctx.overlay_path)
        if st:
            st = st.strip().lower()
            if st not in listing:
                return f"Unknown source type '{st}'."
            vals = listing[st]
            return _render_source_list({st: vals})
        return _render_source_list(listing)

    if action in {"add", "remove"}:
        if len(args) < 3:
            return f"Usage: /source {action} &lt;type&gt; &lt;value&gt;"
        source_type = args[1]
        source_value = " ".join(args[2:]).strip()
        try:
            if action == "add":
                created, canonical = add_source(
                    ctx.sources_path, ctx.overlay_path, source_type, source_value
                )
                if created:
                    return f"Added {source_type}: {canonical}"
                return f"Already tracked: {canonical}"
            removed, canonical = remove_source(
                ctx.sources_path, ctx.overlay_path, source_type, source_value
            )
            if removed:
                return f"Removed {source_type}: {canonical}"
            return f"Not found: {canonical}"
        except Exception as exc:
            return f"Source command failed: {exc}"

    return "Usage: /source &lt;add|remove|list|wizard&gt; ..."


def _render_source_list(rows: dict[str, list[str]]) -> str:
    lines = ["<b>Tracked sources</b>:"]
    for st in sorted(rows):
        vals = rows[st]
        lines.append(f"<b>{st}</b>: {len(vals)}")
        for v in vals[:10]:
            lines.append(f"  - {v}")
        if len(vals) > 10:
            lines.append(f"  - ... (+{len(vals) - 10} more)")
    return "\n".join(lines)


def _trigger_run(ctx: CommandContext, chat_id: str) -> str:
    run_id = uuid.uuid4().hex[:DEFAULT_RUN_ID_LENGTH]
    acquired, current = ctx.lock.acquire(run_id)
    if not acquired and current is not None:
        return f"Run already active: {current.run_id} (started {current.started_at})"

    def worker() -> None:
        try:
            profile = load_effective_profile(ctx.profile_path, ctx.profile_overlay_path)
            sources = load_effective_sources(ctx.sources_path, ctx.overlay_path)
            store = SQLiteStore(ctx.db_path)
            report = run_digest(
                sources,
                profile,
                store,
                use_last_completed_window=True,
                only_new=True,
                allow_seen_fallback=False,
                logger=get_run_logger(run_id),
            )
            ctx.send_message(
                chat_id,
                (
                    f"Run completed: run_id={report.run_id} status={report.status} "
                    f"source_errors={len(report.source_errors)} summary_errors={len(report.summary_errors)}"
                ),
                None,
            )
        except Exception as exc:
            ctx.send_message(chat_id, f"Run failed: {exc}", None)
        finally:
            ctx.lock.release(run_id)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return f"Run started: <code>{run_id}</code>"


def _help_text() -> str:
    types = ", ".join(supported_source_types())
    return (
        "<b>Commands</b>\n\n"
        "/status — run status, schedule, sources\n"
        "/digest run — trigger a digest run\n"
        "/schedule [on|off] — view/toggle schedule\n"
        "/schedule time HH:MM — set run time\n"
        "/history [last|run_id] — run history\n"
        "/doctor — system health check\n"
        "/settings — content preferences\n"
        "/settings depth practical|balanced|deep_technical\n"
        "/source wizard — manage sources\n"
        "/source list [type] — list sources\n"
        "/source add|remove &lt;type&gt; &lt;value&gt;\n"
        "/feedback mute|trust &lt;type&gt; &lt;value&gt;\n"
        "/feedback summary\n\n"
        f"<b>Source types</b>: {types}"
    )


# ── Keyboards ────────────────────────────────────────────────────────


def _wizard_action_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Add", "callback_data": "sw:add"},
                {"text": "Remove", "callback_data": "sw:remove"},
                {"text": "List", "callback_data": "sw:list"},
            ],
            [{"text": "Cancel", "callback_data": "sw:cancel"}],
        ]
    }


def _wizard_type_keyboard() -> dict:
    types = supported_source_types()
    rows: list[list[dict]] = []
    row: list[dict] = []
    for st in types:
        row.append({"text": st, "callback_data": f"sw:t:{st}"})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            {"text": "Back", "callback_data": "sw:back"},
            {"text": "Cancel", "callback_data": "sw:cancel"},
        ]
    )
    return {"inline_keyboard": rows}


def _wizard_confirm_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Confirm", "callback_data": "sw:ok"},
                {"text": "Back", "callback_data": "sw:back"},
                {"text": "Cancel", "callback_data": "sw:cancel"},
            ]
        ]
    }


def _wizard_cancel_keyboard() -> dict:
    return {"inline_keyboard": [[{"text": "Cancel", "callback_data": "sw:cancel"}]]}


def _cancel_keyboard(callback_data: str) -> dict:
    return {"inline_keyboard": [[{"text": "Cancel", "callback_data": callback_data}]]}


# ── Auth & state ─────────────────────────────────────────────────────


def _is_authorized(chat_id: str, user_id: str, ctx: CommandContext) -> bool:
    return chat_id in ctx.admin_chat_ids and user_id in ctx.admin_user_ids


def _parse_command(text: str) -> tuple[str, list[str]]:
    tokens = text.strip().split()
    if not tokens:
        return "", []
    cmd = tokens[0].split("@", 1)[0].lower()
    args = [
        t.strip().lower() if i == 0 else t.strip() for i, t in enumerate(tokens[1:])
    ]
    return cmd, args


def _get_state(ctx: CommandContext, chat_id: str, user_id: str) -> dict:
    key = (chat_id, user_id)
    state = ctx.wizard_state.get(key)
    if state is None:
        state = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "wizard": "",
            "action": "",
            "source_type": "",
            "awaiting_value": False,
            "draft_value": "",
        }
        ctx.wizard_state[key] = state
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


def _clear_state(ctx: CommandContext, chat_id: str, user_id: str) -> None:
    ctx.wizard_state.pop((chat_id, user_id), None)


def _expire_wizard_state(ctx: CommandContext) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=WIZARD_TTL_SECONDS)
    stale: list[tuple[str, str]] = []
    for k, state in ctx.wizard_state.items():
        updated = str(state.get("updated_at") or "")
        try:
            dt = datetime.fromisoformat(updated)
        except Exception:
            stale.append(k)
            continue
        if dt < cutoff:
            stale.append(k)
    for k in stale:
        ctx.wizard_state.pop(k, None)
