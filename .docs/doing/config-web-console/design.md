# Design: Config Web Console

## Architecture
- Frontend: Vite React app (`web/`) using shadcn/ui + Tailwind.
- Backend: FastAPI app (`src/digest/web/app.py`) with JSON endpoints.
- Domain reuse:
  - source operations via `source_registry`
  - profile parsing/validation via `parse_profile_dict`
  - runtime execution via `run_digest`

## Data Model
- Sources overlay: `data/sources.local.yaml` (existing).
- Profile overlay: `data/profile.local.yaml` (new overlay target).
- Snapshot history: `.runtime/config-history/*.json`.

## UX Flow
1. Sources tab: type select + add/remove + effective list table.
2. Profile tab: grouped controls + advanced JSON editor.
3. Review tab: validate, diff, save overlay.
4. History tab: snapshot list + rollback action.
5. Header actions: refresh + run now + active/latest run badges.

## API Endpoints
- `GET /api/config/source-types`
- `GET /api/config/sources`
- `POST /api/config/sources/add`
- `POST /api/config/sources/remove`
- `GET /api/config/profile`
- `POST /api/config/profile/validate`
- `POST /api/config/profile/diff`
- `POST /api/config/profile/save`
- `GET /api/config/effective`
- `GET /api/config/history`
- `POST /api/config/rollback`
- `POST /api/run-now`
- `GET /api/run-status`

## Safety
- Overlay-first writes for profile and source edits.
- Snapshot on each mutating action for rollback.
- Run-now guarded by run lock.
