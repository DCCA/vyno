# Design: YouTube Noise Sanitization

## Cleaning stage
Add `clean_youtube_text` in pipeline utilities and apply it to video items during normalization.

## Summary guardrail
Add `is_low_signal_summary` checks in `FallbackSummarizer`:
- excessive URLs
- sponsor/patreon phrases
- hashtag spam
- overlong single-line dumps

When invalid, fallback summarizer output is used and reason is returned.

## Renderer bounds
Add channel-safe text utilities:
- phrase cleanup for sponsor tokens
- max length caps for title and summary lines

## Backward compatibility
- Non-video items remain unchanged by cleaner.
- Existing render entrypoints remain available.
