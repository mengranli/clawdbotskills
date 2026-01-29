# Parsing guidelines (Telegram → ledger row)

## Group chat policy (spend-only)

For the spend-only Telegram group `chat_id=-1003711269809`:

- Trigger on messages containing **"buy"** (case-insensitive).
- If a message does **not** contain "buy", do **not** engage (stay silent), unless the user is clearly trying to log spend but forgot the keyword—then reply once with the required format.
- If someone asks unrelated questions, reply once:
  “Spend logging only. Please log purchases with **BUY** (e.g. `BUY: item; amount currency; project_code; category; vendor=...`).”
  then ignore further off-topic.

## What to extract

From an unstructured message about a purchase, extract:

- item (what was bought)
- total amount + currency (or unit price + qty)
- category (Lab consumables | Equipment | Chemicals & gases)
- project_code (DE, DE Est, KC8 CO2R, KC8 pH swing, ASG, DP, LP, Startup, Pursuit)
- optional: vendor, qty, notes

## Heuristics

- Amounts: detect patterns like `$123`, `123 aud`, `AUD 123.45`, `£12.30`, `12.30` (only treat bare numbers as money if “$” or currency token is present).
- Qty: `x2`, `2x`, `qty 2`, `2 units`, `2 bottles`.
- Category keywords:
  - **Lab consumables**: tips, tubes, gloves, filters, vials, pipette, falcon, kimwipes
  - **Equipment**: pump, balance, instrument, power supply, meter, glassware set
  - **Chemicals & gases**: NaOH, HCl, electrolyte, CO2, N2, Ar, solvent, salt
- Project codes: exact match OR near match (case-insensitive). If ambiguous, ask.

## Clarification policy

If any of these are missing or low-confidence, ask a single follow-up question that lists the missing fields:

- amount (and currency)
- category
- project_code
- item (if message is too vague)

Keep it lightweight (1 message). If they reply with partial info, update and ask again only if still required.

## Examples

- “Bunnings: nitrile gloves $28.50 DE” → item=nitrile gloves, total=28.50, category=Lab consumables, project=DE
- “Airgas CO2 bottle refill 95 AUD (KC8 CO2R)” → category=Chemicals & gases, project=KC8 CO2R
- “Bought electrodes $320” → ask for category + project code.
