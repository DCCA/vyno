# Product

## Register

product

## Platform

web

## Users

One person: the operator-owner. A PM who runs this as their personal AI signal desk, locally. They read the daily digest in Telegram; they open the console only to tune sources, review runs, give feedback, and diagnose drift. There is no second audience - the operator, the reader, and the owner are the same person.

## Product Purpose

AI Daily Digest turns noisy AI-news sources (RSS, YouTube, X, GitHub) into one curated daily brief, scored and selected by LLM agents, delivered to Telegram and archived to Obsidian. Success is twofold: the digest is reliably high-signal enough to trust, and the console makes occasional tuning and diagnosis fast when something drifts. The console is a control room, not a destination - a good week is one where it was barely opened.

## Positioning

My taste, automated. The system learns from feedback and encodes the operator's editorial judgment, so every run makes the digest more theirs. Every screen quietly reinforces that the operator is training an editor, not browsing a feed.

## Brand Personality

Editorial, considered, refined. The console should feel like a well-run newsroom desk: typographic, deliberate, a bit elegant. Confidence comes from clarity and restraint, not from chrome or spectacle.

## Anti-references

- Generic SaaS dashboard: gradient heroes, vanity-metric cards, marketing chrome inside a tool.
- Crypto/trading terminal: neon-on-black, blinking numbers, urgency theatrics.
- News feed / social app: infinite scroll, engagement bait, algorithmic-feed vibes - the very thing this product exists to replace.

## Design Principles

1. **Control room, not destination.** Optimize every screen for fast diagnosis and exit, not time-on-page. The best session is a short one.
2. **Teach the editor everywhere.** Feedback is the product's fuel; giving it (on items, sources, runs) should be one gesture away on any surface that shows curated output.
3. **Newsroom desk over dashboard.** Hierarchy comes from typography and editorial structure, not metric cards. Numbers serve judgment; they are not the show.
4. **Quiet until something drifts.** Healthy state is calm and low-contrast; attention is spent only on anomalies (failed runs, degraded coverage, source errors), which must be unmissable.
5. **Legible judgment.** Where the system decided something (scores, selection, repair), the reasoning should be one step away, in the operator's language.

## Accessibility & Inclusion

Stricter than AA: aim AAA-ish. 7:1 contrast for body text where achievable, large hit targets, full keyboard parity across the console, visible focus states, and prefers-reduced-motion honored everywhere. Both light and dark themes must independently meet these bars.
