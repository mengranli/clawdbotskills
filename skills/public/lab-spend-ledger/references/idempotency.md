# Idempotency / "Already logged" behavior

In the spend-only group, users may repeat messages or send `@bot log`.

Rule:
- Never claim **Logged ✅** unless the Excel append succeeded.
- Use a local dedupe key so repeats don’t create duplicate ledger entries.

## Dedupe key

Use:
- `telegram:<chat_id>:message:<message_id>`

## Procedure

1) On a trigger message (contains "buy"):
- If `message_id` is available: run
  - `python scripts/ledger_dedupe.py check --key <key>`
  - If exit code is 10: reply **Already logged ✅** and do nothing.

2) Append to Excel:
- Run in venv:
  - `. .venv/bin/activate && python scripts/log_spend_to_excel.py ...`
- If it fails: reply with a short error and do **not** mark dedupe.

3) After append success:
- `python scripts/ledger_dedupe.py mark --key <key> --meta '{"item":"...","price":...}'`
- Reply **Logged ✅**.

## About `@bot log`

If someone replies `@bot log` to an earlier message, treat it as:
- “please log the referenced message (if not already logged)”.

(If you can’t access the referenced message text, ask them to re-send the BUY line.)
