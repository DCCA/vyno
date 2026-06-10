# Quality Gate Repair Proposal

## Why

The repo has working backend/frontend tests, but quality gates are not trustworthy because the security workflow fails before later scanners run, Ruff finds one undefined-name path, and npm audit reports a moderate React Router advisory.

## Scope

Fix the current quality-gate blockers without changing product behavior:

- prevent detect-secrets from scanning `.secrets.baseline` itself;
- make the GitHub Security workflow run on the default `master` branch as well as `main`;
- fix the module-level feedback helper so Ruff passes;
- update React Router packages through npm audit fix;
- verify backend tests, frontend tests/build, security check, and npm audit.

## Non-goals

- No feature changes.
- No UI redesign.
- No large module refactors.
- No deployment changes.
