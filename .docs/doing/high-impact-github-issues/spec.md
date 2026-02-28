# Spec: high-impact-github-issues

### Requirement: Trusted-org issue gate
Runtime SHALL keep `github_issue` items only when they come from a trusted GitHub org and include at least one medium-severity keyword.

#### Scenario: Trusted org issue with medium-severity signal
- GIVEN an item with type `github_issue`
- AND source owner is in `trusted_orgs_github`
- AND issue text includes a medium-severity keyword
- WHEN runtime performs candidate filtering
- THEN the issue SHALL remain eligible

#### Scenario: Missing trusted org or medium-severity signal
- GIVEN an item with type `github_issue`
- AND either owner is not trusted OR text has no medium-severity keyword
- WHEN runtime performs candidate filtering
- THEN the issue SHALL be excluded from candidates

### Requirement: Non-issue items unaffected
Runtime SHALL not apply this gate to non-`github_issue` item types.

#### Scenario: Article or video candidate
- GIVEN a candidate item with type not equal to `github_issue`
- WHEN runtime performs candidate filtering
- THEN the item SHALL follow existing logic unchanged
