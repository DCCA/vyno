---
name: AI Daily Digest Console
description: An editor's desk for a personal AI signal digest - editorial, considered, refined
colors:
  pressroom-green: "hsl(162 84% 28%)"
  pressroom-green-dark: "hsl(158 64% 45%)"
  overcast-bg: "hsl(200 16% 99%)"
  overcast-ink: "hsl(200 12% 10%)"
  overcast-card: "hsl(0 0% 100%)"
  overcast-secondary: "hsl(200 14% 96%)"
  overcast-muted: "hsl(200 12% 95.5%)"
  overcast-muted-ink: "hsl(200 7% 44%)"
  overcast-border: "hsl(200 12% 90%)"
  ink-button: "hsl(200 12% 11%)"
  destructive-red: "hsl(0 72% 47%)"
  success-green: "hsl(158 74% 34%)"
  warning-amber: "hsl(28 90% 36%)"
typography:
  display:
    fontFamily: "Archivo, Public Sans, ui-sans-serif, system-ui"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Public Sans, ui-sans-serif, system-ui"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Public Sans, ui-sans-serif, system-ui"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Public Sans, ui-sans-serif, system-ui"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.4
  data:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  sm: "8px"
  md: "10px"
  lg: "12px"
spacing:
  sm: "8px"
  md: "12px"
  lg: "20px"
components:
  button-primary:
    backgroundColor: "{colors.ink-button}"
    textColor: "hsl(0 0% 100%)"
    rounded: "{rounded.lg}"
    height: "36px"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "hsl(200 12% 11% / 0.9)"
  button-secondary:
    backgroundColor: "{colors.overcast-card}"
    textColor: "hsl(200 10% 22%)"
    rounded: "{rounded.lg}"
    height: "36px"
    padding: "8px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.overcast-secondary}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.overcast-ink}"
    rounded: "{rounded.lg}"
    height: "36px"
    padding: "8px 16px"
  button-ghost-hover:
    backgroundColor: "{colors.overcast-muted}"
  button-destructive:
    backgroundColor: "{colors.destructive-red}"
    textColor: "hsl(0 0% 100%)"
    rounded: "{rounded.lg}"
    height: "36px"
    padding: "8px 16px"
  input-default:
    backgroundColor: "{colors.overcast-bg}"
    textColor: "{colors.overcast-ink}"
    rounded: "{rounded.md}"
    height: "36px"
    padding: "8px 12px"
  card-default:
    backgroundColor: "{colors.overcast-card}"
    textColor: "{colors.overcast-ink}"
    rounded: "{rounded.lg}"
    padding: "20px"
---

# Design System: AI Daily Digest Console

## Overview

**Creative North Star: "The Editor's Desk"**

This console is a working editor's desk, not a dashboard. One person sits here to tune sources, review runs, and teach the system their taste; the interface projects the calm of a well-run newsroom desk: editorial, considered, refined. Hierarchy is typographic before it is chromatic. Density is welcome where judgment happens (tables, timelines, source lists), and the surface stays quiet until something drifts.

The palette is a single cool-slate neutral family with one working accent. Depth is drawn, not cast: hairline borders structure the page while shadows only whisper. Components are tactile and confident, but their tactility comes from state response (pressed scale, border and color shifts), never from decoration. Both light and dark themes are first-class and independently tuned.

**Key Characteristics:**
- One neutral hue (200), one accent, no gradients
- Typographic hierarchy first; color signals state, not importance
- Hairline borders structure; shadows at most 6px blur, slate-tinted
- Monospace tabular numerals wherever data aligns in columns
- Motion conveys state in 150-280ms; reduced motion always honored

## Colors

One cool-slate neutral family plus a single editorial green; every other color is a semantic state voice.

### Primary
- **Pressroom Green** (hsl(162 84% 28%) light / hsl(158 64% 45%) dark): the only voice of emphasis. Marks primary selection, focus rings, active state, and signal (what the system picked). On dark surfaces it brightens and flips to a deep green foreground (hsl(160 90% 12%)) for legible filled controls.

### Neutral
- **Overcast Slate family** (all hue 200): page background hsl(200 16% 99%), ink hsl(200 12% 10%), card white, secondary surface hsl(200 14% 96%), muted surface hsl(200 12% 95.5%), muted ink hsl(200 7% 44%), border hsl(200 12% 90%). Dark theme: background hsl(200 14% 7%), card hsl(200 12% 10%), ink hsl(200 10% 95%), border hsl(200 10% 18%).
- **Ink Button** (hsl(200 12% 11%)): the primary action color is the ink itself, not the accent; a dark near-black button reads as the desk's confident default action.

### State voices
- **Destructive Red** (hsl(0 72% 47%) light / hsl(0 65% 58%) dark): errors and irreversible actions only.
- **Success Green** (hsl(158 74% 34%) light / hsl(156 60% 46%) dark): confirmations and healthy status.
- **Warning Amber** (hsl(28 90% 36%) light / hsl(35 90% 55%) dark): degraded states, attention without alarm.

### Named Rules
**The One Accent Rule.** Pressroom Green is the only emphasis color and never exceeds roughly 10% of a screen. No gradients, anywhere; the legacy `gradient-accent` class renders flat accent by design.

**The One Hue Rule.** Every neutral shares hue 200. A gray from another hue family is a bug.

## Typography

**Display Font:** Archivo (with Public Sans, system-ui fallback)
**Body Font:** Public Sans (with system-ui fallback)
**Data Font:** IBM Plex Mono (with ui-monospace fallback)

**Character:** A grotesque pairing with newsroom pragmatism: Archivo carries page titles with quiet authority, Public Sans does everything else without drawing attention, and IBM Plex Mono gives data a typeset, wire-copy voice.

### Hierarchy
- **Display** (700, 1.5rem, 1.2, -0.01em): page titles and section headers via Archivo. Fixed rem sizes, never fluid clamp.
- **Title** (600, 1rem, 1.25, -0.01em): card and panel titles.
- **Body** (400, 0.875rem, 1.5): default console text. Prose runs at 65-75ch max; tables and dense UI may run wider.
- **Label** (500, 0.8125rem): buttons, form labels, small UI text.
- **Data** (500, 0.875rem, IBM Plex Mono): metrics, counts, timestamps, ids.

### Named Rules
**The Tabular Rule.** Any number that can appear in a column is set in IBM Plex Mono with `font-variant-numeric: tabular-nums` so digits align.

## Layout

App-shell console: a navigation rail plus a content region of stacked panels. Cards use 20px internal padding (p-5) with 12px vertical rhythm between related elements. Controls sit on a 36px height line (buttons, inputs, selects all h-9). Density is structural: tables and lists compress comfortably; whitespace is spent on separating judgments, not decorating them. Responsive behavior is structural (rail collapse, table adaptation), not fluid typography.

## Elevation & Depth

Borders structure, shadows whisper. Structure comes from hairline (1px) borders in the slate family; shadows exist only to lift panels a breath off the page, are always tinted to the neutral hue (hsl(200 30% 12%)), never exceed 6px blur, and imply a single top-down light source. Overlays (dialogs, command palette) may use the larger panel shadow, nothing stronger.

### Shadow Vocabulary
- **Panel** (`box-shadow: 0 1px 3px 0 hsl(200 30% 12% / 0.08), 0 1px 2px -1px hsl(200 30% 12% / 0.08)`): resting cards and panels.
- **Panel large** (`box-shadow: 0 4px 6px -1px hsl(200 30% 12% / 0.07), 0 2px 4px -2px hsl(200 30% 12% / 0.07)`): overlays and raised moments.

### Named Rules
**The Whisper Rule.** If a shadow is noticeable before you look for it, it is too strong. Depth beyond these two tokens comes from borders and surface tone.

## Shapes

Soft rectangles, consistently. The radius scale is 8 / 10 / 12px from a single `--radius: 0.75rem` token: cards and buttons at 12px, inputs at 10px, small elements at 8px. Full-pill shapes are reserved for badges and status dots. Nothing exceeds 12px; over-rounding reads as consumer-app, not editor's desk. Borders are always 1px; no decorative thick borders, no side-stripe accents.

## Components

Tactile and confident: components respond firmly to touch (active scale 0.98, 150ms transitions, visible focus rings) while staying visually quiet at rest. Every interactive component ships default, hover, focus-visible, active, and disabled states; async surfaces add skeleton loading (shimmer) and empty states that teach.

### Buttons
- **Shape:** soft rectangle (12px radius), 36px height, 500 weight label
- **Primary:** Ink Button background (hsl(200 12% 11%)) with white text; hover eases to 90% opacity
- **Secondary:** white card surface with hairline border; hover fills with secondary slate
- **Ghost:** transparent; hover fills with muted slate
- **Destructive:** Destructive Red fill, white text
- **Hover / Focus / Active:** 150ms color transitions, `focus-visible` ring in Pressroom Green with 2px offset, active scale 0.98 (suppressed under reduced motion)

### Cards / Containers
- **Corner Style:** 12px radius
- **Background:** card white (light) / hsl(200 12% 10%) (dark)
- **Shadow Strategy:** Panel shadow only (see Elevation)
- **Border:** 1px Overcast border, always present
- **Internal Padding:** 20px, header stacked with 6px gap

### Inputs / Fields
- **Style:** 1px border on page background, 10px radius, 36px height, 14px text
- **Focus:** 2px Pressroom Green ring via `focus-visible`, no border color change
- **Placeholder:** muted ink
- **Disabled:** 50% opacity, not-allowed cursor

### Navigation
- Console rail with quiet typographic items; active item carries the accent voice. In dark theme the rail gets a faint top emerald wash (5% alpha fading to slate by 120px), the one permitted atmospheric touch.

### Signature: Status feedback
Feedback renders next to the control that triggered it (same card or row), never as a global banner; success auto-dismisses, errors persist, both carry non-color cues and `aria-live` semantics. This locality pattern is a tested invariant of the product.

## Do's and Don'ts

### Do:
- **Do** keep Pressroom Green under roughly 10% of any screen; its rarity is what makes state legible.
- **Do** set columnar numbers in IBM Plex Mono with tabular figures.
- **Do** ship every interactive state (hover, focus-visible, active, disabled, loading skeleton, empty) before calling a component done.
- **Do** tune light and dark independently; both themes target stronger-than-AA contrast (7:1 for body text where achievable).
- **Do** express tactility through state response: pressed scale, border and fill shifts, 150ms eases.

### Don't:
- **Don't** use gradients; the flat single accent is a committed decision recorded in the code.
- **Don't** introduce grays outside hue 200 or shadows outside the two panel tokens.
- **Don't** exceed 12px radius on any container or control.
- **Don't** animate for decoration; motion conveys state in 150-280ms and always honors `prefers-reduced-motion`.
- **Don't** style the console toward metric-card dashboards, neon terminal aesthetics, or feed-like surfaces; the desk stays editorial and calm.
