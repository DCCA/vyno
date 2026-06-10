# Web Feedback Helper Extraction Proposal

## Why

`src/digest/web/app.py` is very large. Feedback feature extraction and rating logic is pure helper code and can move out of the route module without changing API behavior.

## Scope

- Move feedback rating/feature helper functions into `digest.web.feedback`.
- Keep existing imports from `digest.web.app` working by importing the helper names there.
- Run focused web helper tests and the full backend/security checks.

## Non-goals

- No route behavior changes.
- No API shape changes.
- No frontend changes.
