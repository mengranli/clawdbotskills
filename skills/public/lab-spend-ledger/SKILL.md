---
name: lab-spend-ledger
description: "Parse unstructured chat messages about lab purchases/spend into a structured spend ledger (item, amount, category, project code, timestamp, sender) and append rows into a shared Excel workbook (OneDrive) via Microsoft Graph. Use when operating in Telegram DMs or group chats where members report purchases in short messages and you must (1) extract fields, (2) ask minimal clarification questions when needed, and (3) record each expense into the lab’s Excel ledger."
---

# Lab Spend Ledger

Maintain a shared spend ledger from unstructured chat messages (Telegram now; extendable to other channels). Extract details, ask for clarification when necessary, then append a row to an Excel *Table* in a OneDrive workbook using Microsoft Graph.

## Workflow

### 1) Detect “this is a spend”
Treat a message as a spend record if it includes *any* of:
- money amount + currency/symbol
- purchase verbs: bought/ordered/paid/spent
- vendor/store names + an item

If it’s ambiguous, ask: “Is this a purchase to log?”

### 2) Draft a row (best-effort extraction)
Extract these fields:
- `timestamp_utc` (use message time)
- `submitted_by`, `submitted_by_id`, `chat`, `message_id`, `raw_text`
- `item`
- `total` and `currency` (or unit_price + qty)
- `category` (Lab consumables | Equipment | Chemicals & gases)
- `project_code` (DE | DE Est | KC8 CO2R | KC8 pH swing | ASG | DP | LP | Startup | Pursuit)
- optional: vendor, qty, notes

Use `scripts/parse_purchase_message.py` to get a first draft, but always sanity-check.

### 3) Clarify (single lightweight question)
If any required fields are missing or low-confidence, ask **one** follow-up message listing the missing fields, e.g.:

> I can log this—what’s the **project code** and **category** (consumables/equipment/chemicals & gases)?

If multiple items are in one message, prefer: “Is this 1 line item or multiple? If multiple, list them like: item — amount — project.”

### 4) Append to Excel (Graph)
Best practice: the workbook has an Excel **Table** (Insert → Table) named e.g. `Ledger` with stable columns.

- Column guidance: see `references/ledger-schema.md`.
- Parsing heuristics: see `references/parsing-guidelines.md`.

Use `scripts/graph_excel_append.py` to write into the Excel table via a OneDrive share link.

Important: Excel’s `rows/add` always appends to the bottom of the table. If the table contains blank rows (e.g. row 2 empty), call the script with `--fill-first-empty` to fill the first completely empty row inside the table.

### 5) Confirm (optional)
In busy group chats, keep confirmation minimal:
- If confidence is high: “Logged: <item>, <amount> <ccy>, <project>.”
- If you had to guess: “Logged (please confirm): …”

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
