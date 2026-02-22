# Proposal: Remove Admin Panels

## Why
The HTTP and Streamlit admin panels are not meeting UX and maintenance expectations. The project already has CLI and Telegram admin workflows that cover operational needs with lower maintenance overhead.

## Scope
- Remove HTTP admin panel implementation and entrypoints.
- Remove Streamlit admin UI/prototype implementation and entrypoints.
- Remove panel-specific dependencies, tests, and documentation.
- Keep CLI + Telegram operational workflows intact.

## Out of Scope
- Replacing removed panels with a new UI in this change.
