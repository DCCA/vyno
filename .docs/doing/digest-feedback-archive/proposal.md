# Proposal: Digest Feedback Archive

## Why
- Operators are receiving too many repeated sources in a single digest.
- Technical and research-heavy links are overrepresented for a general daily digest.
- The product cannot yet capture explicit user feedback on delivered items and sources.
- The system does not reliably preserve every delivered digest as a retrievable artifact for later review and personalization.

## Scope
- Add digest-wide source diversity controls beyond `must_read`.
- Add an explicit content-depth preference in the profile and ranking pipeline.
- Persist selected items and delivered artifacts for each non-preview run.
- Add source-level and item-level feedback APIs and UI actions.
- Surface archived digests and feedback controls in existing console surfaces.

## Non-Goals
- A new standalone archive workspace.
- Heavy ML personalization infrastructure beyond the existing local feedback-bias path.
- Breaking changes to the current run, timeline, or scheduler workflows.
