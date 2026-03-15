# Jobs To Be Done — AI Daily Digest

Five core jobs ranked by importance. Each job follows: **Situation** (when/where the struggle happens), **Motivation** (why it matters), **Desired Outcome** (what success looks like).

---

## 1. Stay current on AI without drowning in noise

> **Job statement**: When I'm following dozens of AI sources across RSS, YouTube, GitHub, and X, help me surface only what matters so I can stay informed in minutes, not hours.

**Situation**: You follow 50-100+ sources. Every morning the firehose delivers hundreds of items — blog posts, papers, repo releases, video drops, threads. Skimming takes an hour. Missing something important feels worse.

**Motivation**: Your job depends on knowing what's happening in AI. But the volume-to-signal ratio is brutal, and time spent triaging is time not spent building.

**Desired Outcome**: A single daily brief with the 10-15 items that actually matter, scored, ranked, and delivered where you already are.

**Product proof**:

| Feature | Benefit |
|---------|---------|
| Four native connectors (RSS, YouTube, GitHub, X) | One tool replaces four tabs |
| Dedup pipeline with token-based merging | Same story from 5 sources = 1 entry |
| Rules + LLM scoring (relevance, quality, novelty) | Items ranked by what matters to *you* |
| Diversity-controlled selection (per-source caps) | No single source dominates your digest |
| Telegram + Obsidian delivery | Brief shows up where you already look |

**Target persona**: AI engineers, ML researchers, technical founders, CTOs tracking the AI landscape.

---

## 2. Full control over what I see — no black-box algorithm

> **Job statement**: When I can't see why my feed shows me certain items, give me transparent scoring with knobs I can tune so I trust what I'm reading and what I'm skipping.

**Situation**: Newsletters and social feeds use opaque algorithms. You can't tell why something appeared or what you're missing. Tuning means "liking" things and hoping the model adjusts.

**Motivation**: You want to make your own editorial decisions. You need to trust that your information diet isn't shaped by engagement optimization.

**Desired Outcome**: Every item shows its score and why. You can adjust topics, entities, trusted sources, and content-depth preferences. Your feedback visibly shifts future results.

**Product proof**:

| Feature | Benefit |
|---------|---------|
| Score breakdown per item (raw total, adjustments, reason string) | See exactly why each item ranked where it did |
| YAML-editable profile with 60+ configurable fields | Tune topics, entities, exclusions, source weights |
| Web UI for profile management with validation and diff preview | Change settings without touching config files |
| Feedback loop with half-life decay (default 14 days) | Your thumbs-up/down shifts scoring — recent feedback counts more |
| Config history with rollback | Undo any settings change instantly |

**Target persona**: Power users, researchers, anyone who's been burned by algorithmic feeds they can't control.

---

## 3. Keep my data local — no SaaS lock-in

> **Job statement**: When I don't want another SaaS owning my reading habits and information sources, let me self-host everything so my data stays mine.

**Situation**: SaaS digest tools own your data. They can change pricing, shut down, or sell your reading patterns. Your curated source list and reading history live on someone else's server.

**Motivation**: You want full data ownership. You don't want to rebuild from scratch when a service pivots or sunsets.

**Desired Outcome**: Everything runs on your machine. Your database, your archive, your config. Zero cloud dependency beyond the AI APIs you choose to use.

**Product proof**:

| Feature | Benefit |
|---------|---------|
| Runs locally via Docker or bare Python | No cloud service to depend on |
| SQLite database stores all state | Your data is a single portable file |
| Obsidian vault delivery with structured markdown | Archive lives in your file system, version-controlled if you want |
| Config in plain YAML files with local overlays | Human-readable, diffable, backed up with your dotfiles |
| Docker Compose with two services (bot + scheduler) | One `docker compose up` to run everything |

**Target persona**: Privacy-conscious professionals, Obsidian power users, self-hosting enthusiasts.

---

## 4. Manage my digest from my phone without touching config files

> **Job statement**: When I want to add a source, tweak a setting, or trigger a run while away from my desk, let me do it from my phone without SSHing into anything.

**Situation**: You've set up your digest and it runs daily. But you spot a new blog to track, or want to trigger a run before a meeting. You're on your phone. SSH is not happening.

**Motivation**: You want "set and forget" that still lets you make quick adjustments when inspiration strikes.

**Desired Outcome**: A mobile-friendly control plane that covers the 80% of management tasks you'd ever do on the go.

**Product proof**:

| Feature | Benefit |
|---------|---------|
| Telegram bot commands (`/source add`, `/source list`, `/digest run`, `/status`) | Manage from any Telegram client |
| Interactive source wizard via Telegram (`/source wizard`) | Guided source setup without memorizing syntax |
| Web console with full management UI | Browser-based control from any device |
| Onboarding wizard with source packs | Get started in minutes, not hours |
| Preflight checks via `/doctor` and health endpoints | Verify your setup is healthy without reading logs |

**Target persona**: Operators who want low-maintenance tooling with occasional mobile tuning.

---

## 5. Build a searchable knowledge archive of AI developments

> **Job statement**: When past discoveries and digests disappear into chat history, give me a structured archive I can search and reference months later.

**Situation**: You read something two weeks ago that's now relevant to a decision. It was in a Telegram message, or maybe an email newsletter. You can't find it. The insight is gone.

**Motivation**: AI moves fast. Patterns only become visible over time. You need to look back to see forward.

**Desired Outcome**: Every digest automatically archived with structure — date, tags, run ID — in a format you can search, link, and build on.

**Product proof**:

| Feature | Benefit |
|---------|---------|
| Obsidian markdown notes with YAML frontmatter (date, run_id, tags) | Every digest is a searchable, linkable document |
| Timeline view in web console with run history | Visual history of every digest run |
| Timeline notes and export | Annotate runs and export full history |
| Full artifact archiving (Telegram payload + Obsidian note) | Nothing gets lost between delivery channels |
| Funnel stats per run (fetched, deduped, scored, selected) | Understand what was filtered and why |

**Target persona**: Researchers, analysts writing reports, anyone who revisits past content to spot trends.
