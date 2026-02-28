# Spec: web-live-run-incremental-defaults

### Requirement: Web live run defaults
Web-triggered live runs SHALL default to incremental scope.

#### Scenario: User clicks Run now or Activate in web app
- GIVEN a web-triggered live run is started
- WHEN runtime options are applied
- THEN `use_last_completed_window` SHALL be true
- AND `only_new` SHALL be true
- AND `allow_seen_fallback` SHALL be false

### Requirement: Preview safety remains unchanged
Onboarding preview runs SHALL keep existing preview semantics.

#### Scenario: User clicks Preview in onboarding
- GIVEN onboarding preview endpoint is called
- WHEN run is executed
- THEN preview mode behavior remains unchanged
- AND delivery side effects remain disabled
