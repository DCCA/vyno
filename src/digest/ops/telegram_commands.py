from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from digest.config import load_profile
from digest.logging_utils import get_run_logger
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


@dataclass(slots=True)
class CommandContext:
    sources_path: str
    profile_path: str
    db_path: str
    overlay_path: str
    admin_chat_ids: set[str]
    admin_user_ids: set[str]
    lock: RunLock
    send_message: Callable[[str, str, dict | None], None]
    answer_callback: Callable[[str, str], None] | None = None
    wizard_state: dict[tuple[str, str], dict] = field(default_factory=dict)


@dataclass(slots=True)
class BotResponse:
    chat_id: str | None = None
    text: str | None = None
    reply_markup: dict | None = None
    callback_query_id: str | None = None
    callback_text: str | None = None


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
        return _handle_wizard_value_input(chat_id, user_id, text, ctx)

    cmd, args = _parse_command(text)
    if cmd in {"/help", "/start"}:
        return BotResponse(chat_id=chat_id, text=_help_text())
    if cmd == "/status":
        return BotResponse(chat_id=chat_id, text=_status_text(ctx))
    if cmd == "/digest":
        if len(args) == 1 and args[0] == "run":
            return BotResponse(chat_id=chat_id, text=_trigger_run(ctx, chat_id))
        return BotResponse(chat_id=chat_id, text="Usage: /digest run")
    if cmd == "/source":
        return BotResponse(chat_id=chat_id, text=_handle_source(args, ctx, chat_id, user_id), reply_markup=_wizard_action_keyboard() if args and args[0] == "wizard" else None)

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


def _handle_callback_query(callback: dict, ctx: CommandContext) -> BotResponse:
    callback_id = str(callback.get("id") or "").strip()
    data = str(callback.get("data") or "").strip()
    message = callback.get("message") or {}
    chat_id = str((message.get("chat") or {}).get("id") or "").strip()
    user_id = str((callback.get("from") or {}).get("id") or "").strip()

    if not chat_id or not user_id:
        return BotResponse(callback_query_id=callback_id, callback_text="Invalid callback")

    if not _is_authorized(chat_id, user_id, ctx):
        return BotResponse(
            chat_id=chat_id,
            text="Not authorized.",
            callback_query_id=callback_id,
            callback_text="Not authorized",
        )

    if not data.startswith("sw:"):
        return BotResponse(callback_query_id=callback_id, callback_text="Unsupported action")

    state = _get_state(ctx, chat_id, user_id)
    key = data[3:]

    if key in {"add", "remove", "list"}:
        state.update({"action": key, "source_type": "", "awaiting_value": False, "draft_value": ""})
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
            return BotResponse(callback_query_id=callback_id, callback_text="Unknown source type")
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
                f"Send value for `{source_type}` now.\n"
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
            return BotResponse(callback_query_id=callback_id, callback_text="Nothing to confirm")
        try:
            if action == "add":
                created, canonical = add_source(ctx.sources_path, ctx.overlay_path, source_type, draft_value)
                msg = f"Added {source_type}: {canonical}" if created else f"Already tracked: {canonical}"
            else:
                removed, canonical = remove_source(ctx.sources_path, ctx.overlay_path, source_type, draft_value)
                msg = f"Removed {source_type}: {canonical}" if removed else f"Not found: {canonical}"
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


def _handle_wizard_value_input(chat_id: str, user_id: str, raw_value: str, ctx: CommandContext) -> BotResponse:
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
        text=(
            f"Confirm {action} for {source_type}:\n"
            f"`{canonical}`"
        ),
        reply_markup=_wizard_confirm_keyboard(),
    )


def _handle_source(args: list[str], ctx: CommandContext, chat_id: str, user_id: str) -> str:
    if not args:
        return "Usage: /source <add|remove|list|wizard> ..."

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
            return f"Usage: /source {action} <type> <value>"
        source_type = args[1]
        source_value = " ".join(args[2:]).strip()
        try:
            if action == "add":
                created, canonical = add_source(ctx.sources_path, ctx.overlay_path, source_type, source_value)
                if created:
                    return f"Added {source_type}: {canonical}"
                return f"Already tracked: {canonical}"
            removed, canonical = remove_source(ctx.sources_path, ctx.overlay_path, source_type, source_value)
            if removed:
                return f"Removed {source_type}: {canonical}"
            return f"Not found: {canonical}"
        except Exception as exc:
            return f"Source command failed: {exc}"

    return "Usage: /source <add|remove|list|wizard> ..."


def _render_source_list(rows: dict[str, list[str]]) -> str:
    lines = ["Tracked sources:"]
    for st in sorted(rows):
        vals = rows[st]
        lines.append(f"- {st}: {len(vals)}")
        for v in vals[:10]:
            lines.append(f"  - {v}")
        if len(vals) > 10:
            lines.append(f"  - ... (+{len(vals)-10} more)")
    return "\n".join(lines)


def _trigger_run(ctx: CommandContext, chat_id: str) -> str:
    run_id = uuid.uuid4().hex[:12]
    acquired, current = ctx.lock.acquire(run_id)
    if not acquired and current is not None:
        return f"Run already active: {current.run_id} (started {current.started_at})"

    def worker() -> None:
        try:
            profile = load_profile(ctx.profile_path)
            sources = load_effective_sources(ctx.sources_path, ctx.overlay_path)
            store = SQLiteStore(ctx.db_path)
            report = run_digest(
                sources,
                profile,
                store,
                use_last_completed_window=False,
                only_new=False,
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
    return f"Run started: {run_id}"


def _status_text(ctx: CommandContext) -> str:
    lock_state = ctx.lock.current()
    store = SQLiteStore(ctx.db_path)
    row = store.latest_run_summary()

    lines = []
    if lock_state is not None:
        lines.append(f"Active run: {lock_state.run_id} (started {lock_state.started_at})")
    else:
        lines.append("Active run: none")

    if row:
        lines.append(
            f"Last run: {row[0]} status={row[1]} started_at={row[2]} source_errors={row[3]} summary_errors={row[4]}"
        )
    else:
        lines.append("Last run: none")
    return "\n".join(lines)


def _help_text() -> str:
    types = ", ".join(supported_source_types())
    return (
        "Commands:\n"
        "/status\n"
        "/digest run\n"
        "/source wizard\n"
        "/source list [type]\n"
        "/source add <type> <value>\n"
        "/source remove <type> <value>\n"
        f"Supported source types: {types}"
    )


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
    rows.append([{"text": "Back", "callback_data": "sw:back"}, {"text": "Cancel", "callback_data": "sw:cancel"}])
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


def _is_authorized(chat_id: str, user_id: str, ctx: CommandContext) -> bool:
    return chat_id in ctx.admin_chat_ids and user_id in ctx.admin_user_ids


def _parse_command(text: str) -> tuple[str, list[str]]:
    tokens = text.strip().split()
    if not tokens:
        return "", []
    cmd = tokens[0].split("@", 1)[0].lower()
    args = [t.strip().lower() if i == 0 else t.strip() for i, t in enumerate(tokens[1:])]
    return cmd, args


def _get_state(ctx: CommandContext, chat_id: str, user_id: str) -> dict:
    key = (chat_id, user_id)
    state = ctx.wizard_state.get(key)
    if state is None:
        state = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
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
