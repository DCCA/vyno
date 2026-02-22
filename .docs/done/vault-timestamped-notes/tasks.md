# Tasks: Timestamped Obsidian Notes Per Run

- [x] 1.1 Add config key `output.obsidian_naming` with values `timestamped|daily`.
- [x] 1.2 Default naming mode to `timestamped`.
- [x] 1.3 Add validation for unsupported naming values.

- [x] 2.1 Update runtime to pass `run_id` and UTC run timestamp to Obsidian writer.
- [x] 2.2 Update Obsidian writer to generate timestamped path structure.
- [x] 2.3 Preserve legacy daily path when `obsidian_naming: daily`.

- [x] 3.1 Extend note frontmatter with `run_id` and `generated_at_utc`.
- [x] 3.2 Keep existing `date`, `tags`, and `source_count` fields.

- [x] 4.1 Add unit test: two same-day runs create distinct files.
- [x] 4.2 Add unit test: UTC midnight boundary yields different date folders.
- [x] 4.3 Add unit test: legacy daily mode keeps old filename behavior.

- [x] 5.1 Update README with naming modes and examples.
- [x] 5.2 Run full test suite and verify no regressions.
- [x] 5.3 Add completion summary and move folder to `.docs/done/` when all done criteria pass.
