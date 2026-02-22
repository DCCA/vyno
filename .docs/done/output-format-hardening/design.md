# Design: Output Format Hardening

## Obsidian renderer
- Use stable frontmatter ordering.
- Normalize item tags to kebab-case for better search consistency.
- Render Must-read as callout blocks for scannability.
- Use markdown links in all sections.

## Telegram renderer
- Build digest as ordered lines with short section headers.
- Split linewise with max chunk size (default 4000 chars) to stay under Telegram practical limits.
- Keep existing send API and message semantics.

## Runtime integration
- Replace single-message render call with multi-message render loop.
- Keep partial-failure handling unchanged.
