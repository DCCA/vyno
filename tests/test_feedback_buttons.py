import tempfile
import urllib.error
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.delivery.telegram import (
    build_feedback_keyboard,
    render_telegram_messages,
    render_telegram_payloads,
)
from digest.models import DigestSections, Item, ItemType, Score, ScoredItem, Summary
from digest.ops.run_lock import RunLock
from digest.ops.telegram_commands import CommandContext, handle_update
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


def _scored(idx: int, kind: ItemType = "article") -> ScoredItem:
    item = Item(
        str(idx),
        f"https://x/{idx}",
        f"Title {idx}",
        "src",
        None,
        datetime.now(),
        kind,
        "body",
    )
    score = Score(str(idx), 1, 1, 1, 3, tags=["llm"])
    summary = Summary(tldr="TLDR", key_points=["kp"], why_it_matters="why")
    return ScoredItem(item=item, score=score, summary=summary)


class TestRenderPayloads(unittest.TestCase):
    def test_payload_texts_match_plain_renderer(self):
        sec = DigestSections(
            must_read=[_scored(1)], skim=[_scored(2)], videos=[_scored(3, "video")]
        )
        payloads = render_telegram_payloads("2026-02-21", sec)
        self.assertEqual(
            [text for text, _ in payloads],
            render_telegram_messages("2026-02-21", sec),
        )

    def test_item_ids_are_numbered_and_complete(self):
        sec = DigestSections(
            must_read=[_scored(1)], skim=[_scored(2)], videos=[_scored(3, "video")]
        )
        payloads = render_telegram_payloads("2026-02-21", sec)
        refs = [ref for _, refs in payloads for ref in refs]
        self.assertEqual([n for n, _ in refs], [1, 2, 3])
        self.assertEqual(sorted(i for _, i in refs), ["1", "2", "3"])

    def test_ids_stay_with_their_chunk_when_split(self):
        def _long(idx: int) -> ScoredItem:
            scored = _scored(idx)
            scored.item.title = f"Title {idx} " + "padding word " * 12
            return scored

        sec = DigestSections(
            must_read=[_long(1), _long(2), _long(3)], skim=[], videos=[]
        )
        payloads = render_telegram_payloads("2026-02-21", sec, max_len=256)
        self.assertGreater(len(payloads), 1)
        for text, refs in payloads:
            for number, item_id in refs:
                self.assertIn(f"Title {item_id}", text)


class TestFeedbackKeyboard(unittest.TestCase):
    def test_keyboard_shape_and_callback_data(self):
        kb = build_feedback_keyboard("run123", [(1, "itemA"), (2, "itemB")])
        rows = kb["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0]["callback_data"], "fb:run123:itemA:5")
        self.assertEqual(rows[0][1]["callback_data"], "fb:run123:itemA:1")
        self.assertIn("1", rows[0][0]["text"])
        self.assertEqual(rows[1][0]["callback_data"], "fb:run123:itemB:5")

    def test_empty_items_gives_none(self):
        self.assertIsNone(build_feedback_keyboard("run123", []))


class TestFeedbackCallback(unittest.TestCase):
    def _ctx(self, tmp: str):
        sent: list = []
        answered: list = []
        (Path(tmp) / "sources.yaml").write_text(
            "rss_feeds:\n  - https://example.com/rss.xml\n", encoding="utf-8"
        )
        (Path(tmp) / "profile.yaml").write_text("topics: []\n", encoding="utf-8")
        ctx = CommandContext(
            sources_path=str(Path(tmp) / "sources.yaml"),
            profile_path=str(Path(tmp) / "profile.yaml"),
            profile_overlay_path=str(Path(tmp) / "profile.local.yaml"),
            db_path=str(Path(tmp) / "digest.db"),
            overlay_path=str(Path(tmp) / "sources.local.yaml"),
            admin_chat_ids={"1"},
            admin_user_ids={"2"},
            lock=RunLock(str(Path(tmp) / "run.lock"), stale_seconds=3600),
            send_message=lambda chat_id, msg, markup=None: sent.append(
                (chat_id, msg, markup)
            ),
            answer_callback=lambda cb, text="": answered.append((cb, text)),
        )
        return ctx, sent, answered

    def _cb(self, data: str) -> dict:
        return {
            "update_id": 1,
            "callback_query": {
                "id": "cb1",
                "data": data,
                "from": {"id": 2},
                "message": {"message_id": 7, "chat": {"id": 1}},
            },
        }

    def test_thumbs_up_writes_feedback_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, sent, answered = self._ctx(tmp)
            resp = handle_update(self._cb("fb:run123:itemA:5"), ctx)
            self.assertEqual(resp.callback_text, "Noted")
            rows = SQLiteStore(ctx.db_path).list_feedback()
            self.assertEqual(len(rows), 1)
            _, run_id, item_id, rating, label, _, _, target_kind, _, _, actor = rows[0]
            self.assertEqual((run_id, item_id, rating), ("run123", "itemA", 5))
            self.assertEqual(label, "more_like_this")
            self.assertEqual(target_kind, "item")
            self.assertEqual(actor, "2")

    def test_thumbs_down_writes_negative_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, sent, answered = self._ctx(tmp)
            handle_update(self._cb("fb:run123:itemA:1"), ctx)
            rows = SQLiteStore(ctx.db_path).list_feedback()
            self.assertEqual(rows[0][3], 1)
            self.assertEqual(rows[0][4], "not_relevant")

    def test_malformed_payload_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, sent, answered = self._ctx(tmp)
            resp = handle_update(self._cb("fb:bogus"), ctx)
            self.assertEqual(resp.callback_text, "Invalid feedback")
            self.assertEqual(SQLiteStore(ctx.db_path).list_feedback(), [])


class TestDeliveryFailOpen(unittest.TestCase):
    def test_keyboard_rejection_falls_back_to_plain_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(rss_feeds=["fixture"])
            profile = ProfileConfig(
                output=OutputSettings(
                    telegram_bot_token="token",
                    telegram_chat_id="chat",
                    obsidian_vault_path=str(Path(tmp) / "vault"),
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
            )
            fixture_item = Item(
                id="fixture1",
                url="https://example.com/fixture1",
                title="OpenAI evals update",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="Detailed ai evals coverage.",
                hash="fixturehash1",
            )

            calls: list = []

            def fake_send(token, chat_id, message, reply_markup=None):
                calls.append(reply_markup)
                if reply_markup is not None:
                    raise urllib.error.HTTPError(
                        "https://api.telegram.org", 400, "Bad Request", None, None
                    )
                return 1

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.send_telegram_message", side_effect=fake_send),
                patch("digest.runtime.write_obsidian_note"),
                patch("digest.runtime._write_latest_telegram_artifact"),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertIn(report.status, {"success", "partial"})
            self.assertIn(None, calls)
            self.assertTrue(any(markup is not None for markup in calls))

    def test_ambiguous_send_failure_is_not_retried(self):
        # A timeout may have delivered the message; retrying would double-send.
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(rss_feeds=["fixture"])
            profile = ProfileConfig(
                output=OutputSettings(
                    telegram_bot_token="token",
                    telegram_chat_id="chat",
                    obsidian_vault_path=str(Path(tmp) / "vault"),
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
            )
            fixture_item = Item(
                id="fixture1",
                url="https://example.com/fixture1",
                title="OpenAI evals update",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="Detailed ai evals coverage.",
                hash="fixturehash1",
            )

            calls: list = []

            def fake_send(token, chat_id, message, reply_markup=None):
                calls.append(reply_markup)
                raise TimeoutError("timed out")

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.send_telegram_message", side_effect=fake_send),
                patch("digest.runtime.write_obsidian_note"),
                patch("digest.runtime._write_latest_telegram_artifact"),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(len(calls), 1)
            self.assertIsNotNone(calls[0])
            self.assertTrue(
                any("telegram" in str(e).lower() for e in report.summary_errors)
                or report.status in {"partial", "failed"}
            )


if __name__ == "__main__":
    unittest.main()
