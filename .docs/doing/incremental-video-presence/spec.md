# Spec: incremental-video-presence

### Requirement: Incremental runs preserve video section when possible
When incremental mode is active without broad seen fallback, the runtime SHALL supplement candidates with recent seen video items if there are no new video candidates.

#### Scenario: New non-video items, no new videos
- GIVEN `only_new=true` and `allow_seen_fallback=false`
- AND the unseen candidate set contains zero video items
- WHEN the runtime finalizes candidate selection
- THEN it SHALL include a small supplemental set of seen video candidates from the same window
- AND SHALL keep broad seen fallback disabled

#### Scenario: No available seen videos
- GIVEN `only_new=true` and `allow_seen_fallback=false`
- AND no seen video items are available in the window
- WHEN candidate selection completes
- THEN runtime behavior remains unchanged (no forced video insertion)
