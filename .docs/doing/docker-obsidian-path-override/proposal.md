# Proposal: Docker Obsidian Path Override

## Why
Docker runs currently attempt to write Obsidian notes, but the active profile points to a host-only path. Inside the container, that path is not the mounted vault path, so notes do not persist into the host `obsidian-vault/` directory.

## Scope
- Let Docker override `output.obsidian_vault_path` with `/app/obsidian-vault`.
- Keep the current local non-Docker configuration working as-is.
- Verify the fix with a real Docker-backed digest run.

## Out of Scope
- General config-precedence redesign for all profile fields.
- Reworking the local profile or UI profile editor.
