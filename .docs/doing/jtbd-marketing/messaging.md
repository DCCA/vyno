# Customer-Facing Messaging — AI Daily Digest

Copy blocks derived from validated JTBD. Every claim maps to a shipped feature.

---

## Tagline

**AI Daily Digest — Your AI news, your rules, your machine.**

Alternative options:
- "Cut through the AI noise. Keep the signal."
- "The self-hosted AI brief that respects your time and your data."

---

## Hero Headline + Subhead

### Headline
**Stop drowning in AI news. Start reading what matters.**

### Subhead
AI Daily Digest pulls from RSS, YouTube, GitHub, and X — deduplicates, scores, and delivers a ranked daily brief to Telegram and Obsidian. Self-hosted. Fully transparent. Yours.

---

## Value Propositions

### 1. One brief, every source
Ingest from RSS feeds, YouTube channels, GitHub repos, and X — all in one pipeline. Deduplication merges the same story from five sources into one entry. You get 10-15 items, not 200.

### 2. Transparent scoring you control
Every item shows its score and why it ranked where it did. Tune topics, entities, trusted sources, and content depth through the web UI or YAML config. Your feedback shifts future results with a half-life decay — recent input counts most.

### 3. Self-hosted, local-first
Runs on your machine with Docker or bare Python. SQLite database, Obsidian vault, YAML config — all yours. No SaaS dependency, no data harvesting, no surprise pricing changes.

### 4. Manage from anywhere
Telegram bot commands let you add sources, trigger runs, and check status from your phone. The web console handles everything else. An onboarding wizard with curated source packs gets you running in minutes.

### 5. Your AI knowledge archive
Every digest is saved as structured Obsidian markdown with date, tags, and run ID. Timeline view in the web console lets you trace what you read and when. Search, link, and build on months of AI developments.

---

## How It Works

### Step 1: Connect your sources
Add RSS feeds, YouTube channels, GitHub repos and topics, and X accounts. Start with a curated source pack or bring your own list. Configure via Telegram, the web UI, or YAML.

### Step 2: Let the pipeline run
On your schedule (cron, manual trigger, or Telegram command), the engine fetches, deduplicates, and scores every item against your profile — topics you care about, entities you track, quality and novelty signals.

### Step 3: Read your brief
A ranked digest lands in Telegram and Obsidian. Must-reads at the top, skim-worthy below, videos separated. Every item shows its score. Every run is archived and searchable.

---

## Differentiators

### vs. AI Newsletters (Ben's Bites, TLDR AI, The Batch)
Newsletters are one-size-fits-all. You can't choose the sources, tune the ranking, or control the delivery format. AI Daily Digest lets you define exactly what you follow, how it's scored, and where it's delivered — and you own every byte.

### vs. RSS Readers (Feedly, Inoreader)
RSS readers show you everything and leave prioritization to you. They don't score, deduplicate, or summarize. AI Daily Digest adds an intelligence layer: LLM + rules scoring, dedup across all source types (not just RSS), and a curated brief instead of a feed.

### vs. Automation Workflows (Zapier, n8n + ChatGPT)
You *could* build this with Zapier and GPT calls. You'd spend weeks on plumbing, pay per-zap fees, and maintain fragile multi-step automations. AI Daily Digest is purpose-built: one install, one config, battle-tested pipeline with dedup, scoring, diversity controls, feedback loops, and quality learning out of the box.

### vs. Social Feed Algorithms (X, LinkedIn, Reddit)
Platform algorithms optimize for engagement, not your information needs. You can't see the scoring, can't tune it, and can't export your history. AI Daily Digest optimizes for *your* stated preferences with full transparency and a portable archive.

---

## Proof Points (for landing pages, decks, teardowns)

- **4 source types**: RSS, YouTube, GitHub, X — in a single pipeline
- **Dedup**: Token-based merging eliminates cross-source duplicates
- **3-axis scoring**: Relevance (0-60) + Quality (0-30) + Novelty (0-10) with full breakdown
- **60+ profile settings**: Topics, entities, exclusions, source weights, content depth, schedule
- **Feedback with memory**: Half-life decay (default 14 days) ensures recent feedback outweighs stale signals
- **2 delivery channels**: Telegram (instant) + Obsidian (archival)
- **8-step onboarding wizard** with 3 curated source packs (Quickstart Core, AI Engineering, Research Signals)
- **Full Telegram bot**: `/source add`, `/source list`, `/digest run`, `/status`, `/source wizard`
- **Config history + rollback**: Every settings change tracked, any snapshot restorable
- **Timeline + export**: Every run archived with notes, searchable in the web console
- **Docker deploy**: Two services, one `docker compose up`, healthchecks included
- **Zero SaaS dependency**: SQLite + Obsidian + YAML — all local, all portable
