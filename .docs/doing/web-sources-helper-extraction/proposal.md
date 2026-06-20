# Web Sources Helper Extraction Proposal

## Why

`src/digest/web/app.py` is still the largest backend module. The source
health, preview, identity, and error-parsing helpers form a cohesive block that
builds the operator console's source payloads. They can move into a focused
module without changing API behavior, continuing the helper-extraction pattern
already applied for `digest.web.feedback`, `digest.web.schedule`, and
`digest.web.run_progress`.

## Scope

- Move the source helpers into a new `digest.web.sources` module:
  `_build_source_health_items`, `_apply_blocked_source_preference`,
  `_build_source_preview_rows`, `_host_from_url`, `_preview_summary_fallback`,
  `_source_identity`, `_parse_source_error`, `_split_once`, and `_error_hint`.
- Re-import the four route-facing names (`_apply_blocked_source_preference`,
  `_build_source_health_items`, `_build_source_preview_rows`,
  `_parse_source_error`) into `digest.web.app` so existing call sites and
  `from digest.web.app import ...` (used by `test_web_source_health`) keep
  working.
- Update the `test_web_source_previews` mock target to the new module path
  (`digest.web.sources.fetch_link_preview_metadata`), since the call site moved.
- Verify source-health/preview/preview-store tests and the full
  backend/security checks.

## Non-goals

- No source-health, preview, identity, or error-hint behavior changes.
- No API shape changes.
- No route or scheduler-loop changes.
- No frontend changes.

## Notes

- `WebSettings` is referenced only as a type annotation in two helpers, so it is
  imported under `TYPE_CHECKING` in the new module to avoid a circular import
  with `digest.web.app`.
- `_cleanup_preview_db`, `_dict_diff`, and the YAML helpers stay in
  `digest.web.app`; they are used by routes, not by the moved cluster.
