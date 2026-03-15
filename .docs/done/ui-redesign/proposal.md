# UI Redesign: Modern SaaS Inspirations

## Design Direction

Synthesize 5 SaaS inspirations:

1. **Vercel** — performance, clarity, CSS-first animations, whitespace-heavy minimalism
2. **Linear** — monochrome + 2-3 accents, dark-first, strategic minimalism
3. **Supabase** — command palette (cmdk), collapsible panels, dense-but-clear (same stack: Radix + Tailwind)
4. **PostHog** — real-time metrics, fade-in data, saved views
5. **Raycast** — keyboard discovery bar, micro-interactions, icon consistency

## Color Shift

FROM: Warm beige/navy with orange-red accent, gradient backgrounds
TO: Monochrome base (neutral grays) with 2-3 semantic accents, clean backgrounds

## Animation Stack

- **Motion (Framer Motion)** for layout animations, page transitions, gestures
- **CSS-first** for hover/focus/transition effects
- **View Transitions API** as progressive enhancement
- Respect `prefers-reduced-motion`

## Key Additions

- Command palette (cmdk) — Cmd+K quick access
- Keyboard shortcut discovery bar
- Purposeful page/layout animations via Motion
- New color tokens (monochrome + semantic accents)
