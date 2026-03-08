# Proposal: source-identity-cards

## Why
The first card redesign still behaved like an annotated configuration list. The product goal is stronger: each source should feel like a pasted link preview, similar to Notion, so the operator can recognize the latest content behind a source at a glance through image, title, and summary.

## Scope
- Add explicit source-to-item linkage in storage/runtime.
- Add cached link-preview metadata retrieval in the web API.
- Expose a source preview endpoint for the Sources surface.
- Redesign the Sources library as latest-item preview cards while preserving local source actions.
- Refine the preview card UI to follow stronger card hierarchy, accessibility, and action-locality best practices.

## Non-Goals
- Replacing source add/remove flows.
- Requiring a new digest run before previews can ever resolve cached metadata.
- Introducing new source types or changing existing source validation rules.
