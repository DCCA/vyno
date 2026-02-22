# Design: Admin Streamlit UX Revision

## Approach
- Keep the architecture unchanged: Streamlit UI -> `AdminService`.
- Implement UX improvements only in `src/digest/admin_streamlit/app.py`.
- Introduce lightweight local CSS for hierarchy, spacing, and status affordances.

## Key Decisions
- Add `Overview` as first navigation destination for daily operator flow.
- Replace free-text source type entry with select-based type control.
- Add type metadata map (`label`, `hint`, `placeholder`) to reduce input errors.
- Show canonicalization preview by calling `canonicalize_source_value` pre-submit.
- Convert log and run pages to table-first views for faster scanning.
- Split outputs into tabs to avoid mixed-channel preview clutter.

## Risk and Mitigation
- Risk: UI-only refactor can accidentally break existing controls.
  - Mitigation: keep all mutations delegated to `AdminService`; no business-logic duplication.
- Risk: styling injection could reduce Streamlit default readability.
  - Mitigation: keep CSS minimal and preserve native widgets.

## Verification Plan
- Automated: run full test suite (`make test`).
- Manual: run `digest admin-streamlit` and validate key flows:
  - login
  - run now
  - add/remove source
  - logs filter
  - output preview tabs
