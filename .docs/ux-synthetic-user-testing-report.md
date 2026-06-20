# Vyno — Synthetic User Testing Report

**Date:** 2026-06-20
**Method:** Persona-driven cognitive walkthrough. 10 independent synthetic users each walked their relevant flows against the *actual* rendered UI (desktop light/dark + mobile screenshots of all 8 routes) and the component/back-end source, scoring friction with Nielsen-style heuristics. Scope: whole product, admin panel → news feed.
**Build under test:** `master` @ post-emerald-revamp.

## Personas
1. Priya — first-time, non-technical user (onboarding)
2. Marco — daily power operator (dashboard / run loop)
3. Dana — source curator (Sources)
4. Sam — automation manager (Schedule)
5. Lena — quality tuner (Profile)
6. Raj — diagnostician (Timeline)
7. Tom — recovery user (failure → fix; rollback)
8. Aisha — news reader / digest consumer (the "feed")
9. Kenji — mobile user (all surfaces @ 390px)
10. Elena — accessibility / keyboard + screen-reader user
(+ Olu — returning generalist, information-architecture lens)

---

## Headline verdict

The product is **functionally solid and visually coherent** — zero console errors, all flows reachable, strong status signaling, good progressive disclosure, and a genuinely skimmable delivered digest. The gaps are **clarity and trust**, not breakage, with a handful of real defects. Three patterns dominate and were each flagged independently by 3+ personas:

- **"Did it save / take effect?"** — the change→save→run→observe loop is unclear everywhere.
- **Naming & information architecture drift** — the same thing has different names across the shell; some surfaces overlap.
- **Jargon on required paths** — internal vocabulary (preflight, cadence, strictness, backfill, snake_case modes) leaks to users who can't decode it.

---

## P0 — Critical (fix first)

| # | Issue | Personas | Location | Fix |
|---|-------|----------|----------|-----|
| 1 | **Source "Edit" loads the form but never opens the collapsed studio — edits appear to vanish.** Success notice shows, but no editable fields appear; there's also no real "Save edit" (it's change-value-then-Add). | Dana | `App.tsx` `editUnifiedSourceRow`; `SourcesPage.tsx` (`studioOpen` defaults false) | On Edit: open + scroll to studio, prefill, relabel action "Save changes", make it an actual update. |
| 2 | **Rollback fires with no confirmation** — one mis-click overwrites live config, irreversibly, from a 48-row ledger; button isn't even destructive-styled. (Delete *is* confirmed — inconsistent.) | Tom | `HistoryPage.tsx:65`; `App.tsx` `rollback()` | Wrap in the existing confirm dialog (destructive), name the snapshot; auto-snapshot before rollback. |
| 3 | **Command palette "Run digest now" doesn't run — it only navigates to /run.** Broken promise for the keyboard-first core loop. | Marco | `command-palette.tsx:96-104` | Wire to the real `runNow()`, close palette, surface the toast. |
| 4 | **Onboarding is unfinishable for a non-technical user**: no in-UI step for the OpenAI key (assumed in `.env`); the "connect an output" gate needs Telegram bot-token/chat-id or Obsidian vault-path with no help links or zero-config option. | Priya | `OnboardingPage.tsx` steps 1–2 | Add a guided "Connect AI provider" key field; add help links + a zero-config delivery option; clearer failure messages. |
| 5 | **Timeline event rows are not keyboard-operable** — `onClick` on a bare `<tr>`, no `tabIndex`/role/key handler. Keyboard & screen-reader users cannot inspect events (core diagnostic flow). | Elena | `TimelinePage.tsx:321-326` | Make the row a real button or add `tabIndex`, `role="button"`, `aria-pressed`, Enter/Space handler. |

## P1 — High

| # | Issue | Personas | Fix |
|---|-------|----------|-----|
| 6 | **Toggles look instant but are draft-only** (Schedule "Automation enabled"/"Quiet hours"); user can enable, see the badge flip, leave without saving. | Sam | Pending visual state until saved, or a sticky save bar near the toggles; consider auto-save for the enable toggle. |
| 7 | **No "applies on next run / run now" feedback after saving** Profile or Schedule changes — the iterate-and-observe loop has no closure. | Lena, Marco | Post-save toast "Saved — applies on your next run" + inline "Run now" link. |
| 8 | **"Automation enabled" vs "scheduler service running" are two unreconciled concepts** — user can fully enable automation and it still never runs if the background service is down, with no actionable signal. | Sam | One definitive "Will it run, and when?" verdict (ANDs both); actionable callout if the service is down. |
| 9 | **Warning-amber badge fails WCAG AA in light mode** (`--warning 32 92% 44%` + white ≈ 2.6:1) and **severity "error" renders amber, not red** (indistinguishable from "warn"). Status leans on low-contrast color. | Elena, Raj | Darken `--warning` (or dark foreground as in dark mode); add a `destructive` badge variant; map severity error→destructive + row accent. |
| 10 | **Page naming disagrees with itself**: top-bar `<h1>` (route-derived) vs body title — "Run" vs "Run Center", "Overview" vs "Dashboard", "Profile" vs "Profile Setup", within ~80px. | Olu | Drive top-bar h1, sidebar label, and WorkspaceHeader title from one label map. |
| 11 | **The "news feed" is a second-class citizen**: the delivered digest is only viewable as a raw monospace `<pre>` dump (literal HTML/markdown, links not clickable) inside the Timeline *ops console* — no reader-first rendered view. | Aisha | A dedicated "Today's Digest" route rendering formatted, clickable content; keep raw as "view source". |
| 12 | **Mobile data tables are crushed** (Timeline events 6 cols, History ledger) at 390px — squeezed instead of scrolling; the main diagnostic + rollback targets are the worst-rendered. Mode-override is also unreachable from the mobile header. | Kenji | Stacked cards below `sm` (or `min-w` for real horizontal scroll); expose mode override on mobile. |
| 13 | **Required onboarding path is jargon-first** ("preflight", "cadence", "strict", "backfill/catch-up", badge-count results with no plain verdict). | Priya, Lena | Plain-language labels + verdict sentences; preselect "Balanced (recommended)". |

## P2 — Medium

- **IA overlap**: Dashboard, Schedule, and Run Center all answer "is it running and when?" in three voices. Consider Dashboard = read-only hub; merge Schedule + Run Center as **Automatic / Manual** tabs. (Olu)
- **Timeline vs History are confusable names** (both imply "the past"). Rename → "Run Diagnostics" and "Config History / Rollback". (Olu)
- **Filter funnel uses its own vocabulary** (Fetched/Window/Seen/Block/Selected) that doesn't match the pipeline stage names or restriction reasons; bars show survivors, not counts-dropped; not click-through to the matching stage filter. (Raj)
- **"Waiting for items" / "Preview ready"** conflate ingestion health with whether a thumbnail exists; a healthy source with no image looks broken. (Dana)
- **No Retry/Test action for a failing source** — only Mute or Delete, both feel like giving up; error messages are generic ("No hint available") and hard-truncated. (Tom)
- **Feedback label "Repeat source" is ambiguous** (more? or fewer?); item-feedback confirmation appears far from the tapped item; nothing says feedback steers future digests; ratings don't persist across reload. (Aisha)
- **Pending-changes is an opaque count** with two parallel trackers ("pending" vs "policy changes"); no plain list of what changed; no "Discard changes". (Lena)
- **Mute is destructive-styled but unconfirmed**, and the studio "Remove" path is unconfirmed while card "Delete" is — inconsistent destructive guardrails. (Dana, Tom)
- **Quiet-hours overnight windows / time-swallowed-by-quiet-hours** have no explanation or warning; timezone is unvalidated free text. (Sam)
- **"M/S/V", "Surface", raw snake_case modes** (`fresh_only`/`replay_recent`/`backfill`) appear unglossed in user-facing UI. (Raj, Olu)

## P3 — Low (polish)

- Onboarding "Activation milestones" tiles duplicate the numbered steps (two competing systems); preview/health steps show raw markdown / "n/a" with no friendly empty state. (Priya)
- Disabled controls during a run have no tooltip explaining why. (Marco)
- Card "..." overflow sits in different corners on compact vs preview cards; Prefer/Less lack tooltips & applied-state. (Dana)
- Event-detail JSON has no copy button / key surfacing; summary "badge soup" (8 same-color badges). (Raj)
- Touch targets (Prefer/Less, "...", per-row Rollback) below ~44px on mobile. (Kenji)
- Muted text near the AA floor for heavy 10–11px usage; command-palette dialog missing Title/Description (Radix warning). (Elena)
- No global keyboard shortcut for the run action. (Marco)
- ChoiceCard caveats only show once selected (can't compare before choosing). (Lena)

---

## What works well (validated across personas)

- **Functionally clean**: 8/8 routes render with zero console errors, failed requests, or broken images; selects, command palette, table selection, switches, deep-links all work; disabled-during-run states are correct.
- **Strong status signaling**: status ribbon + sidebar + header badge give a true <5s glance; new-user redirect to Guided Setup is the right call.
- **Good progressive disclosure**: Profile gates Expert/Maintenance; recommended defaults are badged; onboarding is a clear numbered path with progress.
- **The delivered digest is genuinely good**: skimmable, must-read/skim/video grouping, source diversification, noise-stripping, TL;DR + "why it matters" callouts.
- **Recovery surfacing + deep-link works**: dashboard alert → filtered Sources view lands correctly.
- **Accessibility foundation is real**: skip-link, consistent focus rings, reduced-motion respected, semantic landmarks, labeled icon buttons, proper confirm `alertdialog`.
- **Mobile nav is conventional and correct**: hamburger → off-canvas drawer, auto-close on route change, grids collapse to one column; no catastrophic page overflow.

---

## Recommended sequencing

1. **Fix the five P0 defects** — they are either real bugs (Edit, command-palette run), a data-loss risk (unconfirmed rollback), an adoption blocker (onboarding for non-technical users), or an accessibility blocker (keyboard rows). Small, high-confidence diffs.
2. **Close the "save / took effect" loop** (P1 #6–8) — pending-state toggles, post-save "applies next run + Run now", and one honest "will it run?" verdict. This is the single most-repeated friction across personas.
3. **Status color + contrast pass** (P1 #9) — darken warning, add destructive variant, error→red. One token+component change fixes contrast and use-of-color everywhere.
4. **Unify naming & tame jargon** (P1 #10, #13; P2 IA) — single label source of truth, gloss/title-case modes, rename Timeline/History.
5. **Give the news feed a first-class reader view** (P1 #11) and **fix mobile tables** (P1 #12).
6. Work down P2/P3 as polish.
