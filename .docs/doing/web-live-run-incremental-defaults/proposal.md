# Proposal: web-live-run-incremental-defaults

## Why
Live runs started from the web console still use broad scope (`only_new=false`, no last-window reuse), which can create unnecessary LLM load and longer completion times.

## Scope
- Switch web-triggered live runs to incremental defaults.
- Keep onboarding preview behavior unchanged.
- Add test coverage for the web run option mapping.

## Out of scope
- Changing preview mode semantics.
- Changing CLI `run` behavior.
