# Proposal: Web API Secret Redaction and Authentication

## Why
The config web API currently exposes sensitive profile values and has no API-level authentication. This is a hardcoded security anti-pattern that can leak secrets and allow unintended config mutation.

## Scope
- Add token-based authentication middleware for `/api/*` routes (with health and preflight exceptions).
- Redact secret-like fields from profile API responses and config-history snapshots.
- Preserve profile save/validate/diff behavior by rehydrating redacted placeholders with current values.
- Update startup/docs so local usage remains simple while enforcing safer defaults.

## Non-goals
- No full user/session auth system.
- No reverse-proxy or cloud deployment redesign.
