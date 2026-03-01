# Proposal: hardcode-hygiene-guardrails

## Problem
The repo had repeated runtime constants, mixed frontend/API runtime assumptions, and no automated security gate for secrets/static analysis. This increased drift risk and made regressions easy to reintroduce.

## Goals
- Centralize repeated constants in backend runtime code.
- Remove frontend/startup hardcoded API coupling where possible.
- Add a practical security gate that blocks critical regressions.

## Non-goals
- Rewriting existing connector/network stack.
- Enforcing zero Bandit medium/low findings in this change.

## Scope
- Add shared constants module and migrate repeated values.
- Harden local app startup and UI API base handling.
- Add `detect-secrets` baseline checks, Bandit high-severity checks, Ruff runtime/syntax checks, and Semgrep advisory in CI/local commands.
