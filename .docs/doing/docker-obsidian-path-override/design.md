# Design: Docker Obsidian Path Override

## Approach
- Change only `output.obsidian_vault_path` precedence so `OBSIDIAN_VAULT_PATH` can override the YAML value when present.
- Leave all other output fields on their current precedence rules.
- Add the env var in Compose for both services so the override is explicit and local runs remain unchanged.

## Notes
- This keeps [config/profile.yaml](../../../../config/profile.yaml) unchanged.
- The mounted Docker path stays `/app/obsidian-vault`.
- Verification must include a real containerized digest run, not just unit tests.
