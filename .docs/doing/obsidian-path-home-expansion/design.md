# Design

## Approach
- Add a small config helper that trims and `expanduser()`-normalizes path strings.
- Apply it to the env and YAML sources for `output.obsidian_vault_path`.
- Keep a defensive `expanduser()` in the Obsidian path builder so direct callers are also safe.
- Add a root-anchored `.gitignore` entry for `/~/`.

## Compatibility
- Absolute paths remain unchanged.
- Relative non-home paths remain relative.
- Docker continues using `/app/obsidian-vault` unchanged.
