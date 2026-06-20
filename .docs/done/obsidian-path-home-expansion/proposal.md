# Proposal

## Summary
Fix Obsidian vault path handling so `~/...` resolves to the user home directory instead of creating a literal repo-local `~/` tree.

## Why
- `.env` may contain `OBSIDIAN_VAULT_PATH=~/...`.
- The runtime currently treats that value as a literal relative path.
- This creates accidental files under the repo root and makes delivery paths misleading.

## Scope
- Normalize `~` in Obsidian vault path loading and path building.
- Ignore the accidental repo-root `~/` artifact directory.
- Add focused regression tests.
