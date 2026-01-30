---
name: lab-spend-ledger
description: "Parse unstructured chat messages about lab purchases/spend into a structured spend ledger (item, amount, category, project code, timestamp, sender) and append rows into a shared Excel workbook (OneDrive) via Microsoft Graph. Use when operating in Telegram DMs or group chats where members report purchases in short messages and you must (1) extract fields, (2) ask minimal clarification questions when needed, and (3) record each expense into the lab’s Excel ledger."
---

# Lab Spend Ledger

Maintain a shared spend ledger from unstructured chat messages (Telegram now; extendable to other channels). Extract details, ask for clarification when necessary, then append a row to an Excel *Table* in a OneDrive workbook using Microsoft Graph.

## Workflow

### 1) Detect “this is a spend”
Trigger in the spend group when the message contains **buy** (case-insensitive).

### 2) Draft a row (best-effort extraction)
Extract:
- `ts_iso` (message timestamp)
- `chat_id`, `message_id`, `author_id`, `author_name`, `raw_text`
- `item`, `price`, `currency`, `category`, `project_code`
- optional: qty/vendor in `notes`

Use `scripts/parse_purchase_message.py` for a first draft, but sanity-check.

### 3) Clarify (single lightweight question)
If any required fields are missing/unclear, ask **one** follow-up that lists missing fields.

### 4) Idempotency (before writing)
Use `references/idempotency.md`:
- Prefer message-id dedupe key `telegram:<chat_id>:message:<message_id>`.
- If unsure, verify against Excel with `scripts/find_excel_rows.py`.

### 5) Append to Excel (Graph) — MUST HAPPEN BEFORE REPLY
Best practice: workbook has an Excel **Table** named `Ledger`.

- Runtime settings: `references/runtime-config.md`

Execution requirement:
- Call the Excel append via an `exec` tool call and **check it returned ok**.
- Only after Excel returns success, mark dedupe and reply.

Preferred append command (works even if system python is used; `graph_excel_append.py` can load `msal` from the repo `.venv`):

```bash
python skills/public/lab-spend-ledger/scripts/log_spend_to_excel.py ...
```

Hard rule:
- **Never send “Logged ✅” unless the Graph append returned success.**
- If append fails, reply with a short error and do not mark dedupe.

### 6) Confirm
Keep it minimal: “Logged ✅ …”

## Excel/Graph setup requirements (ask the owner if missing)

To fully automate, collect:
- **Workbook share URL** (provided)
- **Excel Table name** (create one in Excel Online via Insert → Table; e.g. name it `Ledger`)
- **Column order** used by the table (comma-separated)
- Azure app details:
  - `client_id` (provided)
  - tenant (`common` works for many cases; otherwise tenant id)
  - confirmation the app is a **public client** (device code flow) *or* provide confidential client secret/cert (not recommended to paste into chat)

## Bundled resources

### scripts/
- `parse_purchase_message.py` — heuristic parser; outputs a JSON draft.
- `graph_excel_append.py` — device-code auth + append row to Excel table via Microsoft Graph.

### references/
- `ledger-schema.md` — recommended columns and normalization.
- `parsing-guidelines.md` — extraction heuristics + clarification policy.
