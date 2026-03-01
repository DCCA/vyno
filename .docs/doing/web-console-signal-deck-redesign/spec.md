# Spec: Web Console Signal Deck Redesign

## Scope
Frontend-only redesign of the existing web console (`web/src/App.tsx` + styles/components) with full functional parity.

### Requirement: Feature Parity Preservation
The redesign SHALL preserve all currently shipped user flows, data operations, and control surfaces.

#### Scenario: Existing flow remains available
- GIVEN a user can perform run, onboarding, source management, profile edit, review, timeline, and history operations today
- WHEN the redesigned UI is deployed
- THEN each operation remains available with equivalent outcome
- AND no API endpoint usage is removed

### Requirement: Loading and Transition Integrity
The redesign SHALL retain and improve loading affordances for global and section-level actions.

#### Scenario: Action in progress
- GIVEN an operator triggers run start, source mutation, profile save, timeline refresh, or onboarding action
- WHEN the request is pending
- THEN the UI shows explicit loading feedback tied to the specific action
- AND progress/blocked states prevent ambiguous duplicate actions

### Requirement: Visual Hierarchy and Density Control
The redesign SHALL provide clear priority hierarchy and reduce perceived clutter on primary surfaces.

#### Scenario: Dashboard scan
- GIVEN the operator lands on dashboard during active or recent run activity
- WHEN content renders
- THEN run state, errors, and next recommended action are visible above dense detail tables
- AND secondary detail remains accessible without removing information

### Requirement: Source Health Clarity
The redesign SHALL elevate source health visibility and improve issue triage ergonomics.

#### Scenario: Broken source triage
- GIVEN one or more sources fail repeatedly
- WHEN operator opens Sources health view
- THEN failures, recency, and hint text are presented in a scan-friendly layout
- AND filtering/search remain available

### Requirement: Responsive Quality
The redesign SHALL support desktop, tablet, and mobile with intentional layout adaptation.

#### Scenario: Mobile access
- GIVEN operator opens console on mobile viewport
- WHEN navigating setup and manage surfaces
- THEN navigation, status cards, and controls remain usable without horizontal overflow
- AND primary actions remain reachable within standard thumb scroll patterns

### Requirement: Animation Semantics
The redesign SHALL use motion to clarify state and hierarchy, not decorative noise.

#### Scenario: Surface transition
- GIVEN operator switches between surfaces or tabs
- WHEN view changes
- THEN the UI applies short, consistent transitions that preserve orientation
- AND reduced-motion preferences are respected

### Requirement: Accessibility Baseline
The redesign SHALL preserve keyboard accessibility and semantic labeling for interactive elements.

#### Scenario: Keyboard navigation
- GIVEN a keyboard-only operator
- WHEN traversing primary actions and form controls
- THEN focus order remains logical and visible
- AND controls retain accessible labels and disabled/loading semantics

### Requirement: Contrast and Non-Color Communication
The redesign SHALL ensure information is not conveyed by color alone and SHALL preserve readable contrast for text and controls.

#### Scenario: Status communication
- GIVEN run status and health indicators are displayed
- WHEN a user views statuses under normal and color-vision-constrained conditions
- THEN each status includes non-color cues (text/icon/badge label)
- AND critical text and controls remain readable against their backgrounds

### Requirement: Touch Target and Input Ergonomics
The redesign SHALL preserve safe target sizes and form ergonomics across pointer and touch devices.

#### Scenario: Mobile action taps
- GIVEN an operator uses mobile to trigger primary actions and toggles
- WHEN tapping controls in dashboard and sources views
- THEN actionable targets are sized for touch use and spaced to prevent accidental taps
- AND key forms retain labels and appropriate input hints

### Requirement: URL-Addressable UI State
The redesign SHOULD preserve URL-addressable state for primary surface context to improve shareability and return-to-context flows.

#### Scenario: Context restore
- GIVEN an operator opens a specific manage surface
- WHEN they refresh or share the page URL
- THEN the console restores the same primary surface context where feasible

### Requirement: Layout Stability and Perceived Performance
The redesign SHALL minimize layout shift and keep loading placeholders structurally aligned with final content.

#### Scenario: Data hydration
- GIVEN dashboard and source views load asynchronously
- WHEN data transitions from loading to ready
- THEN placeholder shapes match final content structure
- AND unexpected layout jumps are minimized
