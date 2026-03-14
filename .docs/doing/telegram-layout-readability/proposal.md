# Proposal: Telegram Layout Readability

## Why
The current Telegram digest makes users work too hard to answer three basic questions:
- what is this item about?
- where did it come from?
- why should I trust it over the others?

The renderer currently shows only a title link and summary text, so source and score are hidden even though the runtime already has both values.

## Scope
- Redesign Telegram item blocks for better scanability.
- Show normalized source labels, section labels, and score metadata for each item.
- Validate the redesign with a synthetic 10-user readability test and a real archived Telegram artifact.

## Out of Scope
- Changing ranking or selection logic.
- Redesigning Obsidian output.
- Adding a new user-facing setting for Telegram layout variants.
