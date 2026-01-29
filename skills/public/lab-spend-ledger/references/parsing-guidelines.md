# Parsing guidelines (Telegram → ledger row)

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
