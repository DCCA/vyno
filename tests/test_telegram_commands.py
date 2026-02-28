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
                patch("digest.ops.telegram_commands.run_digest", return_value=Report()),
            ):
                resp = handle_update(upd, ctx)
                self.assertIsNotNone(resp)
                assert resp is not None
                self.assertIn("Run started", resp.text or "")
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


if __name__ == "__main__":
    unittest.main()
