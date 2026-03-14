# Specification

### Requirement: Obsidian Vault Paths Expand User Home
The system SHALL resolve `~` in Obsidian vault paths before writing notes.

#### Scenario: Environment override uses home-relative path
- GIVEN `OBSIDIAN_VAULT_PATH` is set to `~/vault`
- WHEN the profile is loaded and a digest is delivered
- THEN the resolved vault path SHALL point inside the current user's home directory
- AND the runtime SHALL NOT treat `~/vault` as a literal relative repo path

#### Scenario: YAML profile uses home-relative path
- GIVEN `output.obsidian_vault_path` is set to `~/vault`
- WHEN the profile is loaded
- THEN the resolved vault path SHALL point inside the current user's home directory

### Requirement: Existing Absolute Paths Remain Stable
The system SHALL preserve existing absolute Obsidian vault paths.

#### Scenario: Docker mount path is already absolute
- GIVEN `OBSIDIAN_VAULT_PATH=/app/obsidian-vault`
- WHEN the profile is loaded and a digest is delivered
- THEN the runtime SHALL continue writing to `/app/obsidian-vault`
- AND no additional path rewriting SHALL occur

### Requirement: Repo-local Artifact Tree Is Ignored
The repository SHALL ignore the accidental root-level `~/` artifact directory.

#### Scenario: Literal repo-local tilde tree exists
- GIVEN a root-level `~/` directory exists in the repository working tree
- WHEN git status is evaluated
- THEN the directory SHALL be ignored by git
