# Runtime Support Helper Extraction Proposal

## Why

`src/digest/runtime.py` is a large orchestration module. Progress emission and source-link recording are small support concerns that can move into a focused helper module without changing run behavior.

## Scope

- Extract progress callback payload emission into `RunProgressEmitter`.
- Extract source-link recording into `SourceLinkRecorder`.
- Keep `run_digest` orchestration behavior unchanged.
- Verify runtime progress/integration tests and full backend/security checks.

## Non-goals

- No scoring, ingestion, selection, delivery, or storage behavior changes.
- No dependency changes.
