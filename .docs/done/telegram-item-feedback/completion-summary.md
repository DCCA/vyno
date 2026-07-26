# Completion Summary: telegram-item-feedback

**Shipped:** 2026-07-26 (spec PR #34, implementation PR #35).

Restored item-level feedback after the web console retirement. Delivered digest chunks now carry a per-item thumbs-up/down inline keyboard (`render_telegram_payloads` threads item ids through the chunker; `build_feedback_keyboard` builds the rows). The bot's new `fb:` callback handler writes feedback rows - thumbs-up `rating=5 / more_like_this`, thumbs-down `rating=1 / not_relevant`, `target_kind="item"` - pinned to `feedback_feature_bias` semantics (`(rating-3)/2`), so taps bias future ranking exactly like the old web reactions did. Delivery fails open: a rejected keyboard falls back to a plain send and never loses the digest. Admin gating reuses the existing callback auth. TDD throughout (renderer payload mapping, keyboard shape, callback writes, malformed payloads, fail-open delivery).

Deliberately out (YAGNI): vote dedup, comment capture, post-vote keyboard edits, multi-level ratings.
