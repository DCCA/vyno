# Proposal: Telegram Source Wizard (Inline Buttons)

## Why
Text commands work but are error-prone for source type/value input. A guided button flow lowers operator mistakes.

## Scope
- Add `/source wizard` guided flow with inline keyboard buttons.
- Add callback query handling and callback acknowledgments.
- Keep existing text commands backward-compatible.

## Out of Scope
- Native dropdown controls (not available in Telegram Bot API).
- Webhook runtime mode.
