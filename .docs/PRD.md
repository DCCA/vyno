# AI Daily Digest — Telegram + Obsidian (PRD / Spec)

## User story
As a user, I want to receive every morning a list of the most relevant and good AI content on my **Telegram** and saved in my **Obsidian**, so I stay updated with minimal noise.

---

## Goals
- Deliver a **daily AI digest** at a fixed time (morning).
- Support **manual execution** on demand.
- Include only **high-signal** content (relevance + quality + novelty).
- Save an **archived Markdown note** into Obsidian.

## Non-goals (MVP)
- Fully automated X ingestion (API/ToS complexity). Start with RSS + YouTube; add X via manual link drops later.
- Perfect personalization from day 1 (start rules-based + feedback loop later).

---

## Inputs (sources)
### MVP
- **RSS feeds** (blogs/newsletters/sites)
- **YouTube** (channels + keyword searches)

### Later
- **X posts**
  - MVP approach: user drops links into an “inbox” (Telegram message or file)
  - Full automation: requires API/paid or aggregator

---

## Outputs (delivery)
### Telegram (daily message)
- Short + skimmable
- Contains:
  - **Must-read (Top 5)**
  - **Skim (Next 10)**
  - **Videos (Top 3–5)**
  - **Themes today (optional, 3 bullets)**

### Obsidian (daily note)
- Save as Markdown:
  - `AI Digest/YYYY-MM-DD.md`
- Same content as Telegram, plus:
  - More detailed summaries
  - Scores + tags (optional)
  - “Discarded” section (optional, for audit)

---

## Scheduling & execution
- **Daily schedule**: e.g., 07:00 `America/Sao_Paulo`
- **Manual command**: `digest run`

---

## Smartness (ranking system)

### Scoring overview
Total score = **Relevance (0–60)** + **Quality (0–30)** + **Novelty (0–10)**

#### Relevance (0–60)
- Matches AI topics/entities in:
  - title / description (high weight)
  - body / transcript (medium)
- Boost:
  - LLMs, agents, evals, RAG, tooling, infra, safety, product AI, research
- Penalize:
  - generic hype, low-signal “trend” content (configurable)

#### Quality (0–30)
- Boost:
  - primary sources (docs/papers/official blogs)
  - deep/technical analysis
  - reputable authors/sites
- Penalize:
  - clickbait patterns (e.g., “insane”, “shocking”, “10x”, “secret”)
  - thin content (very short, low info)
  - low-reputation sources (configurable)

#### Novelty (0–10)
- Dedupe exact duplicates by URL/hash
- Cluster similar stories (semantic similarity)
- Penalize near-duplicates covered recently

### Selection policy
- Max items per digest: **<= 20**
  - Must-read: 5
  - Skim: 10
  - Videos: 3–5

---

## Pipeline (end-to-end)
1. **Fetch**
   - Pull new items from RSS + YouTube since last run (or last 24h)
2. **Extract**
   - Articles: readable text extraction
   - YouTube: transcript if available + description fallback
3. **Normalize**
   - Convert all items into a single schema
4. **Dedupe + cluster**
   - Remove duplicates; group similar items
5. **Score**
   - Compute relevance/quality/novelty + total
6. **Summarize**
   - TL;DR + bullets + “why it matters”
7. **Deliver**
   - Send Telegram message
   - Write Obsidian Markdown note
8. **Archive**
   - Store items, scores, and run metadata for audit/debug

---

## Data model (minimal)
Use SQLite (local) or Postgres (later).

### Tables
- `items`
  - `id, url, title, source, author, published_at, type, raw_text, hash`
- `runs`
  - `run_id, started_at, window_start, window_end, status`
- `scores`
  - `run_id, item_id, relevance, quality, novelty, total, reason (optional)`
- `seen`
  - `hash/url, first_seen_at`

---

## Configuration
### `sources.yaml`
- RSS feed URLs
- YouTube channel IDs/URLs
- YouTube keyword searches (optional)

### `profile.yaml`
- Topics (positive)
- Entities (positive)
- Exclusions (negative keywords/topics)
- Trusted sources (boost list)
- Blocked sources (deny list)
- Output settings:
  - Telegram chat id
  - Obsidian vault path + folder

---

## Telegram message format (MVP)
**AI Digest — YYYY-MM-DD**

**Must-read**
1. Title — TL;DR (link)
2. ...
3. ...

**Skim**
- Title (link)
- ...

**Videos**
- Title — key takeaway (link)

**Themes**
- Bullet
- Bullet
- Bullet

---

## Obsidian note format (MVP)
```yaml
---
date: YYYY-MM-DD
tags: [ai, digest]
source_count: N
---

