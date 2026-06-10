# Upgrade Vite Dev Audit Proposal

## Why

Production dependency audit is clean, but the full development audit still reports the Vite/esbuild development-server advisory. Resolving it requires a major Vite upgrade and should be isolated from docs and runtime refactors.

## Scope

- Upgrade Vite and the React plugin to compatible current versions.
- Refresh the web lockfile.
- Verify web tests, production build, and npm audit.

## Non-goals

- No application feature changes.
- No UI redesign.
- No backend behavior changes.
