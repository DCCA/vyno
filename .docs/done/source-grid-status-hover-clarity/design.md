# Design: Source Grid Status Hover Clarity

## Approach
- Reduce desktop columns to the minimum triage set.
- Attach row diagnostic summary to the status affordance via hover/focus tooltip text.
- Remove sticky action column behavior and reduce width pressure.
- Keep mobile cards unchanged for explicit on-screen diagnostics.

## Accessibility Notes
- Status diagnostic detail is attached to a focusable element (`tabIndex=0`) and tooltip text (`title`) for mouse/keyboard discoverability.
- Badge labels continue to communicate health with text, not color alone.
