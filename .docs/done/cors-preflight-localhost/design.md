# Design: CORS Preflight Localhost Fix

## Approach
- Add CORS helper functions in `src/digest/web/app.py`:
  - `_cors_allowed_origins()` for explicit fixed defaults plus optional env override
  - `_cors_allow_origin_regex()` for localhost/private-network origins with any port
- Wire helpers into `CORSMiddleware`:
  - `allow_origins=_cors_allowed_origins()`
  - `allow_origin_regex=_cors_allow_origin_regex()`
- Preserve existing permissive method/header settings used by current UI.

## Defaults
- Explicit allow-origins keep known frontend dev/prod preview defaults.
- Regex allows:
  - `localhost`, `127.0.0.1`, `0.0.0.0`
  - RFC1918 private networks (`10.*`, `192.168.*`, `172.16-31.*`)
  - any port

## Validation
- Add unit tests in `tests/test_web_cors.py` for:
  - regex acceptance/rejection behavior
  - middleware receiving configured regex and origins
