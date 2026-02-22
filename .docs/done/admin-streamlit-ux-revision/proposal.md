# Proposal: Admin Streamlit UX Revision

## Why
The Streamlit admin app had operational parity but still felt low-clarity for daily use. Admin workflows needed better information architecture, stronger source-management guidance, and more readable run/log/output surfaces.

## Scope
- Improve admin UI structure and visual hierarchy in `src/digest/admin_streamlit/app.py`.
- Add an overview dashboard for quick operational context.
- Make source add/remove flows more guided and safer.
- Improve table/preview readability for runs, logs, outputs, and feedback pages.

## Out of Scope
- New backend APIs or schema changes.
- Replacing Streamlit with another frontend stack.
- Removing legacy admin HTTP panel.

## Success Conditions
- Admin can complete daily operations faster with fewer input errors.
- Source add/remove actions are more discoverable and validation-guided.
- Existing tests remain green with no behavior regression in admin operations.
