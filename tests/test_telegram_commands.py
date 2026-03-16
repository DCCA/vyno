import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from digest.ops.run_lock import RunLock
from digest.ops.telegram_commands import CommandContext, handle_update


class TestTelegramCommands(unittest.TestCase):
    def _ctx(self, tmp: str):
        sources = Path(tmp) / "sources.yaml"
        profile = Path(tmp) / "profile.yaml"
        db = Path(tmp) / "digest.db"
        overlay = Path(tmp) / "sources.local.yaml"
        profile_overlay = Path(tmp) / "profile.local.yaml"
        sources.write_text(
            "rss_feeds: ['https://example.com/rss.xml']\n", encoding="utf-8"
        )
        profile.write_text(
            "output:\n  telegram_bot_token: ''\n  telegram_chat_id: ''\n",
            encoding="utf-8",
        )
        sent: list[tuple[str, str, dict | None]] = []
        answered: list[tuple[str, str]] = []
        ctx = CommandContext(
            sources_path=str(sources),
            profile_path=str(profile),
            profile_overlay_path=str(profile_overlay),
            db_path=str(db),
            overlay_path=str(overlay),
            admin_chat_ids={"1"},
            admin_user_ids={"2"},
            lock=RunLock(str(Path(tmp) / "run.lock"), stale_seconds=3600),
            send_message=lambda chat_id, msg, markup=None: sent.append(
                (chat_id, msg, markup)
            ),
            answer_callback=lambda callback_id, text="": answered.append(
                (callback_id, text)
            ),
        )
        return ctx, sent, answered

    def test_unauthorized_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            upd = {
                "update_id": 1,
                "message": {"text": "/help", "chat": {"id": 99}, "from": {"id": 2}},
            }
            resp = handle_update(upd, ctx)
            self.assertIsNotNone(resp)
            assert resp is not None
            self.assertEqual(resp.chat_id, "99")
            self.assertIn("Not authorized", resp.text or "")

    def test_source_add_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            upd = {
                "update_id": 1,
                "message": {
                    "text": "/source add github_org https://github.com/vercel-labs",
                    "chat": {"id": 1},
                    "from": {"id": 2},
                },
            }
            resp = handle_update(upd, ctx)
            self.assertIsNotNone(resp)
            assert resp is not None
            self.assertIn("Added github_org: vercel-labs", resp.text or "")

    def test_status_command_reports_last_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            upd = {
                "update_id": 1,
                "message": {"text": "/status", "chat": {"id": 1}, "from": {"id": 2}},
            }
            resp = handle_update(upd, ctx)
            self.assertIsNotNone(resp)
            assert resp is not None
            self.assertIn("Active run", resp.text or "")
            self.assertIn("Last run", resp.text or "")

    def test_digest_run_command_starts_and_sends_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, sent, _ = self._ctx(tmp)
            upd = {
                "update_id": 1,
                "message": {
                    "text": "/digest run",
                    "chat": {"id": 1},
                    "from": {"id": 2},
                },
            }

            class Report:
                run_id = "abc123"
                status = "success"
                source_errors = []
                summary_errors = []

            with (
                patch("digest.ops.telegram_commands.load_effective_profile"),
                patch("digest.ops.telegram_commands.load_effective_sources"),
                patch(
                    "digest.ops.telegram_commands.run_digest", return_value=Report()
                ) as run_mock,
            ):
                resp = handle_update(upd, ctx)
                self.assertIsNotNone(resp)
                assert resp is not None
                self.assertIn("Run started", resp.text or "")
                for _ in range(50):
                    if run_mock.called:
                        break
                    time.sleep(0.01)
                self.assertTrue(run_mock.called)
                kwargs = run_mock.call_args.kwargs
                self.assertTrue(kwargs.get("use_last_completed_window"))
                self.assertTrue(kwargs.get("only_new"))
                self.assertFalse(kwargs.get("allow_seen_fallback", True))
                for _ in range(50):
                    if sent:
                        break
                    time.sleep(0.01)
                self.assertTrue(sent)
                self.assertIn("Run completed", sent[0][1])

    def test_source_wizard_buttons_and_callback_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)

            start = {
                "update_id": 1,
                "message": {
                    "text": "/source wizard",
                    "chat": {"id": 1},
                    "from": {"id": 2},
                },
            }
            resp1 = handle_update(start, ctx)
            self.assertIsNotNone(resp1)
            assert resp1 is not None
            self.assertIn("wizard", (resp1.text or "").lower())
            self.assertIsNotNone(resp1.reply_markup)

            cb_action = {
                "update_id": 2,
                "callback_query": {
                    "id": "cb1",
                    "data": "sw:add",
                    "from": {"id": 2},
                    "message": {"chat": {"id": 1}},
                },
            }
            resp2 = handle_update(cb_action, ctx)
            self.assertIsNotNone(resp2)
            assert resp2 is not None
            self.assertEqual(resp2.callback_query_id, "cb1")
            self.assertIn("Choose source type", resp2.text or "")

            cb_type = {
                "update_id": 3,
                "callback_query": {
                    "id": "cb2",
                    "data": "sw:t:github_org",
                    "from": {"id": 2},
                    "message": {"chat": {"id": 1}},
                },
            }
            resp3 = handle_update(cb_type, ctx)
            self.assertIsNotNone(resp3)
            assert resp3 is not None
            self.assertIn("Send value", resp3.text or "")

            value_msg = {
                "update_id": 4,
                "message": {
                    "text": "https://github.com/vercel-labs",
                    "chat": {"id": 1},
                    "from": {"id": 2},
                },
            }
            resp4 = handle_update(value_msg, ctx)
            self.assertIsNotNone(resp4)
            assert resp4 is not None
            self.assertIn("Confirm add", resp4.text or "")

            cb_ok = {
                "update_id": 5,
                "callback_query": {
                    "id": "cb3",
                    "data": "sw:ok",
                    "from": {"id": 2},
                    "message": {"chat": {"id": 1}},
                },
            }
            resp5 = handle_update(cb_ok, ctx)
            self.assertIsNotNone(resp5)
            assert resp5 is not None
            self.assertIn("Added github_org", resp5.text or "")


    # ── Schedule tests ──────────────────────────────────────────────

    def test_schedule_status_shows_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            upd = _msg("/schedule")
            resp = handle_update(upd, ctx)
            self.assertIsNotNone(resp)
            assert resp is not None
            self.assertIn("Schedule", resp.text or "")
            self.assertIn("Cadence", resp.text or "")
            self.assertIsNotNone(resp.reply_markup)

    def test_schedule_on_enables(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule on"), ctx)
            self.assertIn("enabled", resp.text or "")
            # Verify persisted
            overlay = Path(tmp) / "profile.local.yaml"
            self.assertTrue(overlay.exists())
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("enabled", content)

    def test_schedule_off_disables(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            handle_update(_msg("/schedule on"), ctx)
            resp = handle_update(_msg("/schedule off"), ctx)
            self.assertIn("disabled", resp.text or "")

    def test_schedule_time_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule time 14:30"), ctx)
            self.assertIn("14:30", resp.text or "")

    def test_schedule_time_invalid_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule time 25:00"), ctx)
            self.assertIn("Invalid time", resp.text or "")

    def test_schedule_cadence_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule cadence hourly"), ctx)
            self.assertIn("hourly", resp.text or "")

    def test_schedule_toggle_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            cb = _callback("sch:toggle")
            resp = handle_update(cb, ctx)
            self.assertIn("enabled", resp.text or "")
            self.assertIsNotNone(resp.edit_message_id)

    # ── History tests ────────────────────────────────────────────────

    def test_history_empty_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/history"), ctx)
            self.assertIn("No runs", resp.text or "")

    def test_history_last_no_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/history last"), ctx)
            self.assertIn("No completed runs", resp.text or "")

    # ── Doctor tests ─────────────────────────────────────────────────

    def test_doctor_runs_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/doctor"), ctx)
            self.assertIn("System Health", resp.text or "")
            self.assertIn("Result", resp.text or "")

    # ── Settings tests ───────────────────────────────────────────────

    def test_settings_shows_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings"), ctx)
            self.assertIn("Content depth", resp.text or "")
            self.assertIsNotNone(resp.reply_markup)

    def test_settings_depth_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings depth practical"), ctx)
            self.assertIn("practical", resp.text or "")
            overlay = Path(tmp) / "profile.local.yaml"
            self.assertTrue(overlay.exists())
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("practical", content)

    def test_settings_depth_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings depth foo"), ctx)
            self.assertIn("Invalid depth", resp.text or "")

    def test_settings_depth_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            cb = _callback("cfg:d:practical")
            resp = handle_update(cb, ctx)
            self.assertIn("practical", resp.text or "")
            self.assertIsNotNone(resp.edit_message_id)

    # ── Feedback tests ───────────────────────────────────────────────

    def test_feedback_mute_adds_to_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(
                _msg("/feedback mute rss https://example.com/rss"), ctx
            )
            self.assertIn("muted", resp.text or "")
            overlay = Path(tmp) / "profile.local.yaml"
            self.assertTrue(overlay.exists())
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("blocked_sources", content)

    def test_feedback_trust_adds_to_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(
                _msg("/feedback trust github_org vercel-labs"), ctx
            )
            self.assertIn("trusted", resp.text or "")
            overlay = Path(tmp) / "profile.local.yaml"
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("trusted_orgs_github", content)

    def test_feedback_summary_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/feedback summary"), ctx)
            self.assertIn("No feedback", resp.text or "")

    # ── Help tests ───────────────────────────────────────────────────

    def test_help_text_includes_new_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/help"), ctx)
            text = resp.text or ""
            for cmd in ["/schedule", "/history", "/doctor", "/settings", "/feedback"]:
                self.assertIn(cmd, text, f"Missing {cmd} in help text")

    # ── Multi-wizard state test ──────────────────────────────────────

    def test_starting_new_wizard_clears_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            # Start source wizard
            handle_update(_msg("/source wizard"), ctx)
            handle_update(_callback("sw:add"), ctx)
            # Now start schedule — should clear source state
            resp = handle_update(_msg("/schedule"), ctx)
            self.assertIn("Schedule", resp.text or "")
            # Source wizard state should not intercept text
            resp2 = handle_update(_msg("some text"), ctx)
            self.assertIn("Unknown command", resp2.text or "")

    # ── Mini App button test ─────────────────────────────────────────

    def test_web_public_url_adds_console_button(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            ctx.web_public_url = "https://digest.example.com"
            resp = handle_update(_msg("/status"), ctx)
            markup = resp.reply_markup or {}
            rows = markup.get("inline_keyboard", [])
            texts = [btn.get("text", "") for row in rows for btn in row]
            self.assertTrue(
                any("Console" in t for t in texts),
                "Expected 'Open Console' button when web_public_url is set",
            )

    # ── Run mode tests ─────────────────────────────────────────────

    def test_digest_run_with_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, sent, _ = self._ctx(tmp)

            class Report:
                run_id = "abc123"
                status = "success"
                source_errors = []
                summary_errors = []

            with (
                patch("digest.ops.telegram_commands.load_effective_profile"),
                patch("digest.ops.telegram_commands.load_effective_sources"),
                patch(
                    "digest.ops.telegram_commands.run_digest", return_value=Report()
                ) as run_mock,
            ):
                resp = handle_update(_msg("/digest run backfill"), ctx)
                self.assertIn("backfill", resp.text or "")
                for _ in range(50):
                    if run_mock.called:
                        break
                    time.sleep(0.01)
                self.assertTrue(run_mock.called)
                kwargs = run_mock.call_args.kwargs
                self.assertFalse(kwargs.get("use_last_completed_window"))
                self.assertFalse(kwargs.get("only_new"))

    def test_digest_run_invalid_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/digest run nonsense"), ctx)
            self.assertIn("Invalid mode", resp.text or "")

    def test_digest_run_default_mode_from_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, sent, _ = self._ctx(tmp)
            # Set default mode to balanced
            handle_update(_msg("/settings mode balanced"), ctx)

            class Report:
                run_id = "abc123"
                status = "success"
                source_errors = []
                summary_errors = []

            with (
                patch("digest.ops.telegram_commands.load_effective_profile"),
                patch("digest.ops.telegram_commands.load_effective_sources"),
                patch(
                    "digest.ops.telegram_commands.run_digest", return_value=Report()
                ) as run_mock,
            ):
                resp = handle_update(_msg("/digest run"), ctx)
                self.assertIn("balanced", resp.text or "")
                for _ in range(50):
                    if run_mock.called:
                        break
                    time.sleep(0.01)
                kwargs = run_mock.call_args.kwargs
                self.assertTrue(kwargs.get("allow_seen_fallback"))

    # ── Settings mode/llm/accumulation/exclusion tests ───────────

    def test_settings_mode_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings mode backfill"), ctx)
            self.assertIn("backfill", resp.text or "")
            overlay = Path(tmp) / "profile.local.yaml"
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("backfill", content)

    def test_settings_mode_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings mode nonsense"), ctx)
            self.assertIn("Invalid mode", resp.text or "")

    def test_settings_mode_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            cb = _callback("cfg:m:replay_recent")
            resp = handle_update(cb, ctx)
            self.assertIn("replay_recent", resp.text or "")
            self.assertIsNotNone(resp.edit_message_id)

    def test_settings_llm_toggle(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings llm on"), ctx)
            self.assertIn("enabled", resp.text or "")
            overlay = Path(tmp) / "profile.local.yaml"
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("llm_enabled", content)

    def test_settings_llm_callback_toggle(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            cb = _callback("cfg:llm")
            resp = handle_update(cb, ctx)
            # Default is off, so toggle should enable
            self.assertIn("enabled", resp.text or "")

    def test_settings_accumulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings accumulation 12"), ctx)
            self.assertIn("12h", resp.text or "")

    def test_settings_min_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings min-items 5"), ctx)
            self.assertIn("5", resp.text or "")

    def test_settings_exclusion_add(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings exclusion add crypto"), ctx)
            self.assertIn("crypto", resp.text or "")
            overlay = Path(tmp) / "profile.local.yaml"
            content = overlay.read_text(encoding="utf-8")
            self.assertIn("crypto", content)

    def test_settings_exclusion_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            handle_update(_msg("/settings exclusion add crypto"), ctx)
            resp = handle_update(_msg("/settings exclusion remove crypto"), ctx)
            self.assertIn("removed", resp.text or "")

    def test_settings_status_shows_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/settings"), ctx)
            text = resp.text or ""
            self.assertIn("Content depth", text)
            self.assertIn("Default run mode", text)
            self.assertIn("LLM scoring", text)
            self.assertIn("Accumulation", text)

    # ── Schedule quiet hours + timezone tests ────────────────────

    def test_schedule_quiet_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule quiet on"), ctx)
            self.assertIn("enabled", resp.text or "")

    def test_schedule_quiet_times(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule quiet 23:00 08:00"), ctx)
            self.assertIn("23:00", resp.text or "")
            self.assertIn("08:00", resp.text or "")

    def test_schedule_timezone(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule timezone America/New_York"), ctx)
            self.assertIn("America/New_York", resp.text or "")

    def test_schedule_timezone_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule timezone Fake/Zone"), ctx)
            self.assertIn("Invalid timezone", resp.text or "")

    def test_schedule_quiet_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            cb = _callback("sch:quiet")
            resp = handle_update(cb, ctx)
            self.assertIn("Quiet hours", resp.text or "")
            self.assertIsNotNone(resp.edit_message_id)

    def test_schedule_keyboard_shows_quiet_and_tz(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(_msg("/schedule"), ctx)
            markup = resp.reply_markup or {}
            rows = markup.get("inline_keyboard", [])
            texts = [btn.get("text", "") for row in rows for btn in row]
            self.assertTrue(any("Quiet" in t for t in texts))
            self.assertTrue(any("TZ" in t for t in texts))

    # ── HTML injection tests ────────────────────────────────────────

    def test_html_in_topic_is_escaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(
                _msg("/settings exclusion add <script>alert(1)</script>"), ctx
            )
            text = resp.text or ""
            self.assertNotIn("<script>", text)
            self.assertIn("&lt;script&gt;", text)

    def test_html_in_source_value_is_escaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            resp = handle_update(
                _msg("/feedback mute rss <b>bold</b>"), ctx
            )
            text = resp.text or ""
            self.assertNotIn("<b>bold</b>", text.replace("<b>muted", ""))
            self.assertIn("&lt;b&gt;", text)

    def test_no_console_button_without_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, _, _ = self._ctx(tmp)
            ctx.web_public_url = ""
            resp = handle_update(_msg("/status"), ctx)
            markup = resp.reply_markup or {}
            rows = markup.get("inline_keyboard", [])
            texts = [btn.get("text", "") for row in rows for btn in row]
            self.assertFalse(
                any("Console" in t for t in texts),
                "Should not have 'Open Console' button when web_public_url is empty",
            )


def _msg(text: str) -> dict:
    """Shortcut to build a Telegram message update."""
    return {
        "update_id": 1,
        "message": {"text": text, "chat": {"id": 1}, "from": {"id": 2}},
    }


def _callback(data: str, message_id: int = 100) -> dict:
    """Shortcut to build a Telegram callback query update."""
    return {
        "update_id": 1,
        "callback_query": {
            "id": "cb_test",
            "data": data,
            "from": {"id": 2},
            "message": {"chat": {"id": 1}, "message_id": message_id},
        },
    }


if __name__ == "__main__":
    unittest.main()
