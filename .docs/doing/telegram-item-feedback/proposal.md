# Proposal: telegram-item-feedback

**Status:** SPEC - awaiting approval before implementation.
**Date:** 2026-07-26

## Problem

Retiring the web console (factory-simplification, PR #31) removed the only input surface for item-level feedback. The quality loop - `feedback_feature_bias` (45-day lookback) feeding rank offsets - now hears only source-level `/feedback mute|trust`. Per-item reactions are the highest-value training signal the factory can collect, and today there is no way to give them.

## Design

Inline thumbs on delivered digest messages.

- **Delivery:** the digest is already sent as chunked messages with numbered item blocks. Each chunk gains an inline keyboard: one row per item in that chunk, two buttons - `👍 n` and `👎 n` (n = the item number already printed in the text). `render_telegram_messages` currently returns text chunks only; it (or a sibling builder) must also expose the per-chunk item ids so delivery can build the keyboard.
- **Callback:** data `fb:<run_id>:<item_id>:<rating>` (12-hex run + 16-hex item + prefix ≈ 36 chars, inside Telegram's 64-byte limit). The bot already routes `sw:` and `hist:` callbacks; an `fb:` handler writes `SQLiteStore.add_feedback(run_id, item_id, rating, label, target_kind="item", actor=user_id)` and answers the callback with a short toast ("Noted").
- **Rating mapping** (pinned by `feedback_feature_bias` semantics, `centered = (rating - 3) / 2`): thumbs-up MUST write `rating=5`, `label="more_like_this"`; thumbs-down MUST write `rating=1`, `label="not_relevant"`.
- **Cross-container:** the scheduler container delivers; the bot container receives callbacks; both bind-mount `digest-live.db`. No new plumbing.
- Repeat taps append additional rows; the bias averages over counts. (ponytail: no vote dedup in v1 - add a per-user-per-item upsert if double-voting ever skews the bias.)

## Requirements

- **R1** - Delivered digest messages MUST carry per-item thumbs-up/down inline buttons for exactly the items rendered in that message, without altering the rendered text.
- **R2** - A tap MUST write exactly one feedback row (rating 5 or 1, `target_kind="item"`, linked run and item ids) and MUST answer the callback query.
- **R3** - Taps MUST be accepted only from the admin chat/user ids (same gate as commands); others get "Not authorized." and no row.
- **R4** - Delivery MUST fail open: if keyboard construction or attachment fails, the digest is sent without buttons and the run does not fail.

## Scenarios

- Given a delivered chunk with items 1-3, when the reader taps `👍 2`, then a feedback row (rating=5, item 2's id, the run's id) exists and the next run's rank offsets reflect it via `feedback_feature_bias`.
- Given a callback from a non-admin id, when it arrives, then no row is written and the callback is answered "Not authorized."
- Given Telegram rejects the reply_markup, when delivering, then the digest arrives without buttons and the run completes normally.

## Out of scope (YAGNI)

Multi-level ratings, comment capture, editing keyboards after votes, vote dedup, backfilling past runs.

## Estimate

~120-180 LOC + tests: keyboard builder alongside the renderer, `fb:` callback handler, integration coverage through the existing fake-transport harness in `tests/test_telegram_commands.py`.
