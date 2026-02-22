# Design: Telegram Source Wizard (Inline Buttons)

## Bot API approach
Use Telegram Bot API inline keyboards and callback queries:
- `sendMessage` with `reply_markup.inline_keyboard`
- `getUpdates` callback query ingestion
- `answerCallbackQuery` for button tap acknowledgment

## State model
Track wizard state per `(chat_id, user_id)` with TTL:
- `action` (`add|remove|list`)
- `source_type`
- `awaiting_value`
- `draft_value`

## Callback data
Use compact callback data (<64 bytes):
- `sw:add|sw:remove|sw:list`
- `sw:t:<source_type>`
- `sw:ok|sw:back|sw:cancel`

## Compatibility
Keep text command handler as-is and layer wizard logic on top.
