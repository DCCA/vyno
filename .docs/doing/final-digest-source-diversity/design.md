# Design: Final Digest Source Diversity

## Approach
- Reuse selection helpers rather than duplicating cap logic in quality repair.
- Validate repaired Must-read against both the existing Must-read cap and the final digest cap.
- Fall back to the original sections when repair output is invalid.
- Add a light ranking adjustment for paper-like items from research-heavy source families when they overpopulate the top non-video pool.

## Notes
- The current final digest cap remains `3`.
- The current Must-read cap remains controlled by `must_read_max_per_source`.
- The research-heavy penalty is intentionally bounded and applied before final selection, not as a blocklist.
