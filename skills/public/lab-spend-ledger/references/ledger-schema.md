# Ledger schema (Excel table)

Recommended: keep a *formatted Excel Table* (Insert → Table) so Graph can append rows reliably.

## Columns (your current headers)

Your spreadsheet headers (in order) are:

- `ts_iso`
- `chat_id`
- `message_id`
- `author_id`
- `author_name`
- `item`
- `price`
- `currency`
- `category`
- `project_code`
- `notes`
- `raw_text`

## Notes

- `ts_iso`: store ISO-8601 timestamp (prefer UTC, e.g. `2026-01-29T12:43:01Z`).
- Always store the *raw message text* in `raw_text`.
- Parse money amounts into numeric `price` (no currency symbols).
- If a single message includes multiple items, prefer one row per item; otherwise log one row and put the split details in `notes`, then ask the sender to confirm.

## Normalization rules

- Always store the *raw message text*.
- Parse money amounts as numbers (no currency symbols).
- If multiple items are in one message, prefer one row per item; if that’s hard, create one row with `notes` explaining the split and ask the user to confirm.
