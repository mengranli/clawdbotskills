# Ledger schema (Excel table)

Recommended: keep a *formatted Excel Table* (Insert → Table) so Graph can append rows reliably.

## Columns (suggested)

- `timestamp_utc` (ISO 8601, e.g. 2026-01-29T12:43:01Z)
- `timestamp_local` (optional)
- `submitted_by` (display name)
- `submitted_by_id` (telegram user id)
- `source` (e.g. telegram)
- `chat` (group name/id)
- `message_id`
- `raw_text`
- `vendor` (optional)
- `item` (string)
- `quantity` (number, optional)
- `unit_price` (number, optional)
- `total` (number, optional)
- `currency` (e.g. AUD)
- `category` (Lab consumables | Equipment | Chemicals & gases)
- `project_code` (DE | DE Est | KC8 CO2R | KC8 pH swing | ASG | DP | LP | Startup | Pursuit)
- `notes` (free text)
- `confidence` (0-1)
- `needs_clarification` (true/false)

## Normalization rules

- Always store the *raw message text*.
- Parse money amounts as numbers (no currency symbols).
- If multiple items are in one message, prefer one row per item; if that’s hard, create one row with `notes` explaining the split and ask the user to confirm.
