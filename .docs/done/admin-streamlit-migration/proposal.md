# Proposal: Migrate Admin Panel UI to Streamlit

## Why
The current HTML admin panel is functional but basic. Streamlit provides faster UX iteration and better admin ergonomics with minimal frontend overhead.

## Scope
- Add Streamlit admin UI that reuses existing `AdminService` backend logic.
- Add CLI command to launch Streamlit app with project config paths.
- Keep existing HTTP admin panel as fallback during transition.

## Out of Scope
- Removing old admin panel in this change.
- Multi-user auth provider integration.
