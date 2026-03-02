# Spec: UI Feedback Locality Pattern

### Requirement: Action-Local Feedback
UI surfaces SHALL present success/error feedback in the same card/section as the triggering control.

#### Scenario: Source add/remove
- GIVEN a user clicks `Add` or `Remove` in Sources
- WHEN the API returns success or error
- THEN feedback appears within the Sources card near source controls
- AND the message references the exact affected source.

#### Scenario: Timeline note save
- GIVEN a user saves a timeline note
- WHEN the save completes or fails
- THEN feedback appears near the note input/actions.

### Requirement: Global Feedback Scope
Global top-of-page feedback SHALL be used only for global/system events.

#### Scenario: App bootstrap failure
- GIVEN initial app bootstrap fails
- WHEN no local interaction context exists
- THEN a global error banner is shown.

### Requirement: Deterministic Feedback Lifecycles
Feedback SHALL include clear lifecycle behavior by severity.

#### Scenario: Message dismissal
- GIVEN a success message
- WHEN shown
- THEN it auto-dismisses after a short timeout unless user hovers/focuses it.
- AND error messages persist until corrected, retried, or dismissed.

### Requirement: Accessibility and Non-Color Cues
Feedback SHALL remain accessible and understandable without color-only signaling.

#### Scenario: Screen reader announcement
- GIVEN feedback appears
- WHEN it is success/info
- THEN it announces via polite live region.
- AND error/blocked feedback announces via assertive live region.
