# Design: Admin Streamlit Migration

## Architecture
- New module: `src/digest/admin_streamlit/app.py`
- Config helper: `src/digest/admin_streamlit/config.py`
- UI pages rendered from a single Streamlit app with sidebar navigation.

## Backend Reuse
- All mutations and reads flow through `AdminService`.
- No duplicate business logic in Streamlit layer.

## CLI Integration
- New subcommand: `admin-streamlit`
- Launches `streamlit run ...` subprocess with env-based path/config injection.

## Rollout
- Keep old `admin` command available.
- Document Streamlit as preferred UI and old panel as fallback.
