# Tasks

- [x] Create `digest.web.sources` with the nine source helper functions,
      guarding `WebSettings` behind `TYPE_CHECKING`.
- [x] Remove the moved definitions from `digest.web.app` and import the four
      route-facing names back; drop now-unused imports.
- [x] Update the `test_web_source_previews` mock target to
      `digest.web.sources.fetch_link_preview_metadata`.
- [x] Confirm no circular import (`import digest.web.app` succeeds).
- [x] `ruff check src tests` is clean.
- [x] Full backend test suite passes (focus: `test_web_source_health`,
      `test_web_source_previews`, `test_source_preview_store`).

## Result

- `digest/web/app.py` shrank from 2259 to 1879 lines; new
  `digest/web/sources.py` holds the ~390-line helper module.
- Only the four route-facing helpers are re-imported into `app.py`; the five
  internal helpers (`_host_from_url`, `_preview_summary_fallback`,
  `_source_identity`, `_split_once`, `_error_hint`) live solely in
  `digest.web.sources`.
