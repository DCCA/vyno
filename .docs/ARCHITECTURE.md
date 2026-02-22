# AI Daily Digest Architecture (ASCII)

```text
                              +----------------------+
                              |   profile.yaml        |
                              | topics/entities +/-   |
                              | trusted/blocked src   |
                              +----------+-----------+
                                         |
                                         v
+------------------+         +-----------+------------+         +------------------+
|   sources.yaml   |-------> |   Source Harvester     | <------ | Manual Inbox     |
| RSS feeds        |         | (RSS + YouTube fetch)  |         | (future X links) |
| YouTube channels |         +-----------+------------+         +------------------+
| YouTube queries  |                     |
+------------------+                     v
                                 +-------+--------+
                                 | Content Extract |
                                 | article text    |
                                 | yt transcript   |
                                 +-------+--------+
                                         |
                                         v
                                 +-------+--------+
                                 | Normalizer      |
                                 | canonical item  |
                                 | schema          |
                                 +-------+--------+
                                         |
                                         v
                                 +-------+--------+
                                 | Dedupe/Cluster  |
                                 | URL/hash + sim  |
                                 +-------+--------+
                                         |
                                         v
                           +-------------+-------------+
                           | Scoring Engine            |
                           | relevance + quality +     |
                           | novelty (rules + optional |
                           | LLM summarizer)           |
                           +-------------+-------------+
                                         |
                                         v
                                 +-------+--------+
                                 | Selector        |
                                 | Top5 / Next10 / |
                                 | Videos 3-5      |
                                 +-------+--------+
                                         |
                    +--------------------+--------------------+
                    |                                         |
                    v                                         v
          +---------+---------+                     +---------+---------+
          | Telegram Renderer |                     | Obsidian Renderer |
          | digest message    |                     | markdown note     |
          +---------+---------+                     +---------+---------+
                    |                                         |
                    v                                         v
          +---------+---------+                     +---------+---------+
          | Telegram Bot API  |                     | Vault Writer      |
          | Daily + Manual    |                     | AI Digest/YYYY... |
          +-------------------+                     +-------------------+

                           +-------------------------+
                           | Storage (SQLite)        |
                           | items, scores, seen,    |
                           | runs, audit metadata    |
                           +-----------+-------------+
                                       ^
                                       |
                        +--------------+--------------+
                        | Runtime                    |
                        | - Scheduler (daily 07:00) |
                        | - CLI: digest run         |
                        +---------------------------+
```

## Value Path
1. Ingest broadly from configured sources.
2. Filter/rank by user topics + quality + novelty.
3. Deliver concise Telegram digest.
4. Archive full digest in Obsidian for long-term retrieval.
