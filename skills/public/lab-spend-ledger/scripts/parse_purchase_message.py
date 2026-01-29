#!/usr/bin/env python3
"""Parse a short unstructured purchase message into a ledger row draft.

Usage:
  echo "Bunnings nitrile gloves $28.50 DE" | ./parse_purchase_message.py

Output: JSON on stdout.

This script is intentionally heuristic; the agent should still review/clarify.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

CATEGORIES = [
    "Lab consumables",
    "Equipment",
    "Chemicals & gases",
]

PROJECT_CODES = [
    "DE",
    "DE Est",
    "KC8 CO2R",
    "KC8 pH swing",
    "ASG",
    "DP",
    "LP",
    "Startup",
    "Pursuit",
]

CURRENCY_TOKENS = {
    "AUD": "AUD",
    "USD": "USD",
    "GBP": "GBP",
    "EUR": "EUR",
    "NZD": "NZD",
}

SYMBOL_TO_CCY = {"$": "AUD", "£": "GBP", "€": "EUR"}

CATEGORY_KEYWORDS = {
    "Lab consumables": [
        "gloves",
        "tips",
        "pipette",
        "tube",
        "tubes",
        "falcon",
        "filter",
        "filters",
        "vial",
        "vials",
        "kimwipe",
        "kimwipes",
    ],
    "Equipment": [
        "pump",
        "balance",
        "instrument",
        "power supply",
        "meter",
    ],
    "Chemicals & gases": [
        "co2",
        "n2",
        "argon",
        "ar",
        "hcl",
        "naoh",
        "electrolyte",
        "solvent",
        "salt",
        "gas",
        "cylinder",
        "refill",
    ],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_project(text: str) -> tuple[str | None, float]:
    t = text.lower()
    for p in sorted(PROJECT_CODES, key=len, reverse=True):
        if p.lower() in t:
            return p, 0.95
    return None, 0.0


def find_currency_and_amount(text: str) -> tuple[str | None, float | None, float]:
    # Prefer explicit currency tokens.
    m = re.search(r"\b(AUD|USD|GBP|EUR|NZD)\b\s*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
    if m:
        ccy = CURRENCY_TOKENS[m.group(1).upper()]
        amt = float(m.group(2))
        return ccy, amt, 0.9

    # Symbols like $12.34
    m = re.search(r"([\$£€])\s*([0-9]+(?:\.[0-9]{1,2})?)", text)
    if m:
        ccy = SYMBOL_TO_CCY.get(m.group(1))
        amt = float(m.group(2))
        return ccy, amt, 0.7

    # Bare amount with a currency suffix: 12.34 aud
    m = re.search(r"\b([0-9]+(?:\.[0-9]{1,2})?)\s*(aud|usd|gbp|eur|nzd)\b", text, re.IGNORECASE)
    if m:
        ccy = CURRENCY_TOKENS[m.group(2).upper()]
        amt = float(m.group(1))
        return ccy, amt, 0.85

    return None, None, 0.0


def find_category(text: str) -> tuple[str | None, float]:
    t = text.lower()
    best = (None, 0.0)
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return cat, 0.7
    return best


def guess_item(text: str) -> tuple[str | None, float]:
    # crude: remove project codes and amounts; keep remaining as item/notes
    cleaned = text
    for p in PROJECT_CODES:
        cleaned = re.sub(re.escape(p), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(AUD|USD|GBP|EUR|NZD)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"([\$£€])\s*[0-9]+(?:\.[0-9]{1,2})?", "", cleaned)
    cleaned = re.sub(r"\b[0-9]+(?:\.[0-9]{1,2})?\s*(aud|usd|gbp|eur|nzd)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -–—:\t")
    if not cleaned:
        return None, 0.0
    return cleaned, 0.4


def parse(text: str) -> dict:
    project, p_conf = find_project(text)
    ccy, amt, a_conf = find_currency_and_amount(text)
    category, c_conf = find_category(text)
    item, i_conf = guess_item(text)

    conf = max(p_conf, a_conf, c_conf, i_conf)

    missing = []
    if item is None:
        missing.append("item")
    if amt is None:
        missing.append("amount")
    if category is None:
        missing.append("category")
    if project is None:
        missing.append("project_code")

    return {
        "timestamp_utc": _now_iso(),
        "raw_text": text.strip(),
        "item": item,
        "total": amt,
        "currency": ccy,
        "category": category,
        "project_code": project,
        "confidence": round(conf, 2),
        "missing_fields": missing,
        "needs_clarification": len(missing) > 0,
    }


def main() -> int:
    text = sys.stdin.read()
    if not text.strip():
        print("{}")
        return 2
    print(json.dumps(parse(text), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
