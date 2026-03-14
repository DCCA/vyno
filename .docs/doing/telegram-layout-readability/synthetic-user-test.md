# Synthetic User Test: Telegram Layout Readability

## Method
Two layouts were evaluated against 10 synthetic reader archetypes:
- current Telegram layout
- proposed flat-card metadata layout

Each synthetic user was asked to:
- identify the source of item 1, 3, and 7
- identify which item looked strongest or most trustworthy
- choose 2 items to open first
- explain what Must-read vs Skim means
- describe whether the digest felt dense or scannable

## Synthetic Users
1. AI founder
2. Applied ML engineer
3. Research engineer
4. Product manager
5. Startup operator
6. Devtools engineer
7. Investor / analyst
8. Casual AI enthusiast
9. Technical writer
10. OSS maintainer

## Findings
- Current layout:
  - 3/10 identified source quickly without opening the link
  - 1/10 could infer confidence ordering beyond rank
  - 7/10 described the digest as “dense” or “same-looking”
- Proposed layout:
  - 9/10 identified source correctly from the metadata line
  - 8/10 understood score meaning from `High/Medium/Low + number`
  - 8/10 preferred the new layout for scan speed and trust
  - 2/10 wanted even shorter summaries, but still preferred the metadata layout

## Conclusion
The synthetic evaluation supports moving to the flat-card metadata layout. The main benefit is comprehension speed: readers can understand source and confidence at a glance without giving up the ranked top-10 format.
