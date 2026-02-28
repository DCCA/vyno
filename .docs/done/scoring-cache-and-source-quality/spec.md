# Spec: Scoring Cache and Source Quality Filters

### Requirement: Agent Scores SHALL Be Cacheable for 24h
The system SHALL reuse prior agent scoring output for unchanged items keyed by `item.hash` and `openai_model` when cache age is <= 24 hours.

#### Scenario: Cache hit avoids API call
- GIVEN an item hash and model with a cached score younger than 24h
- WHEN the digest run evaluates that item for agent scoring
- THEN the runtime SHALL use the cached score metadata
- AND the runtime SHALL skip the agent API call for that item

#### Scenario: Cache miss falls back to normal scoring flow
- GIVEN no valid cached score for the item hash and model
- WHEN the digest run evaluates that item for agent scoring
- THEN the runtime SHALL attempt live agent scoring
- AND on success SHALL write/update the cache entry

### Requirement: Agent Scoring Cap SHALL Be Enforced Per Run
The system SHALL limit live agent-scored items using `max_agent_items_per_run` and SHALL score overflow items with rules.

#### Scenario: Overflow items use policy fallback
- GIVEN more eligible items than `max_agent_items_per_run`
- WHEN the runtime selects agent-scoring candidates
- THEN only the top capped subset SHALL attempt cached/live agent scoring
- AND remaining eligible items SHALL use rules scoring

#### Scenario: Coverage policy excludes cap overflow
- GIVEN cap overflow occurs without agent errors
- WHEN coverage thresholds are evaluated
- THEN overflow items SHALL NOT count as agent failure fallback
- AND run status SHALL remain unaffected by overflow alone

### Requirement: GitHub Inputs SHALL Respect Quality Filters
The system SHALL apply configurable quality filters for GitHub items using stars and recency windows.

#### Scenario: Stale or under-threshold GitHub items are excluded
- GIVEN GitHub items older than configured windows or repos below star thresholds
- WHEN ingestion maps GitHub API responses into digest items
- THEN those items SHALL be excluded from candidate outputs

### Requirement: X Inbox Inputs SHALL Be Sanitized
The system SHALL normalize, deduplicate, and filter low-signal X inbox lines before item creation.

#### Scenario: Duplicate and noisy lines are filtered
- GIVEN repeated URLs and promotional/noise comments in the inbox file
- WHEN inbox lines are parsed
- THEN duplicate URLs SHALL yield a single item
- AND low-signal comment lines SHALL be excluded
