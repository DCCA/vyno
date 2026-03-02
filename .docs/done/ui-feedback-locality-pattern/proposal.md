# Proposal: UI Feedback Locality Pattern

## Why
The console currently renders a single global feedback alert near the top of the page. On long screens and dense surfaces, action feedback appears far from the user action that triggered it.

## Problem
- Users click controls inside deep cards/tables and must visually jump to a distant global banner.
- Recovery guidance is detached from the control that needs correction.
- Success feedback can be missed because it does not appear in the interaction context.

## Goal
Adopt a repo-wide UI pattern: feedback MUST appear adjacent to the action origin, with global banners reserved for global/system events.

## Non-Goals
- No backend API changes.
- No removal of existing loading states.
- No interruption of current workflows during migration.
