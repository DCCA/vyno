# Tasks: telegram-item-feedback

Spec approved? Then, TDD throughout:

- [ ] Renderer: expose per-chunk item ids alongside text chunks (no text change)
- [ ] Delivery: build per-item 👍/👎 keyboard per chunk; fail-open on attach errors
- [ ] Bot: `fb:` callback handler -> `add_feedback` (rating 5/1, target_kind="item"), admin-gated, callback answered
- [ ] Tests: keyboard shape, callback write path, non-admin rejection, fail-open delivery
- [ ] Docs: README Telegram commands section + ARCHITECTURE feedback flow
- [ ] Validate, review, PR, CI green, merge; move folder to .docs/done/
