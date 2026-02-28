# Spec: reduce-llm-call-volume

### Requirement: Final-item LLM summarization
The runtime SHALL call the LLM summarizer only for final digest items selected for delivery, not for every scored candidate.

#### Scenario: Candidate pool is large
- GIVEN a run with hundreds of scored candidates
- WHEN section selection finishes
- THEN LLM summarization is attempted only on selected digest items
- AND non-selected items SHALL NOT trigger LLM summary requests

### Requirement: Per-run LLM request budget
The runtime SHALL enforce a configurable per-run LLM request budget across scoring, summarization, and quality-repair calls.

#### Scenario: Budget is exhausted
- GIVEN a run where prior LLM operations consume the configured budget
- WHEN a subsequent LLM operation is about to start
- THEN the runtime SHALL skip that LLM operation
- AND SHALL fail open to non-LLM behavior when possible

### Requirement: Interactive run scope defaults
Bot-triggered live runs SHALL default to incremental scope.

#### Scenario: Interactive run starts from bot
- GIVEN a user starts a live run from bot
- WHEN runtime options are applied
- THEN the run SHALL use last completed window
- AND SHALL process only new items by default

### Requirement: Seen-item fallback control
The runtime SHALL support disabling the fallback that re-expands to seen items when no new items are found.

#### Scenario: Interactive incremental run with no new items
- GIVEN only_new mode and no unseen candidates
- WHEN fallback-to-seen is disabled
- THEN the run SHALL continue with zero candidates
- AND SHALL complete without broad reprocessing
