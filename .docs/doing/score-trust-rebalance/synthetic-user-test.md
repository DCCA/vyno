# Synthetic User Test

Synthetic users:
1. AI founder
2. Applied ML engineer
3. Research engineer
4. Product manager
5. Startup operator
6. Devtools engineer
7. Investor/analyst
8. Casual AI enthusiast
9. Technical writer
10. OSS maintainer

Findings:
- 8/10 interpreted `trusted sources` as "these sources should outrank others".
- 7/10 interpreted the Telegram score as an absolute quality score, not a final policy-adjusted score.
- 9/10 preferred item merit over unconditional source reputation.
- 8/10 preferred a small source tie-breaker to outright removal of source preference.
- 9/10 wanted explanation detail in the app, not inside the Telegram message.

Implications:
- change wording from `trusted` to `preferred reliable`
- show adjusted final score in user-facing surfaces
- persist adjustment breakdown for Timeline review
