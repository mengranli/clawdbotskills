#!/usr/bin/env python3
"""Log a spend record to the lab ledger (Excel Table) via Microsoft Graph.

This is a thin wrapper around graph_excel_append.py with Aaron's defaults.

Usage:
  python log_spend_to_excel.py --ts-iso 2026-01-30T06:59:00Z \
    --chat-id -1003711269809 --message-id 123 --author-id 999 --author-name "Haowei Zhang" \
    --item "Hydrogen peroxide solution" --price 22.11 --currency AUD \
    --category "Chemicals & gases" --project-code Pursuit \
    --notes "" --raw-text "Buy hydrogen peroxide solution 22.11AUD pursuit"

Note: This script expects the operator/agent to run it in the repo venv:
  . .venv/bin/activate

(We keep MSAL installed in that venv.)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

SHARE_URL = "https://1drv.ms/x/c/f41c1af2eee30a91/IQC57il2jfQ6Q5Idi604SQtNASxT0JypHcP9wVMRddS0PgA?e=n5BjtR"
CLIENT_ID = "b98aa7fe-f1b7-4780-9285-4acf1e25d0e8"
TENANT = "common"
TABLE = "Ledger"
COLUMNS = "ts_iso,chat_id,message_id,author_id,author_name,item,price,currency,category,project_code,notes,raw_text"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ts-iso", required=True)
    ap.add_argument("--chat-id", required=True)
    ap.add_argument("--message-id", required=True)
    ap.add_argument("--author-id", required=True)
    ap.add_argument("--author-name", required=True)
    ap.add_argument("--item", required=True)
    ap.add_argument("--price", required=True, type=float)
    ap.add_argument("--currency", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--project-code", required=True)
    ap.add_argument("--notes", default="")
    ap.add_argument("--raw-text", required=True)
    ap.add_argument(
        "--receipt",
        default="",
        help="Optional receipt id to embed in notes (recommended: telegram:<chat_id>:<message_id>)",
    )

    args = ap.parse_args()

    receipt = args.receipt or f"telegram:{args.chat_id}:{args.message_id}"

    notes = (args.notes or "").strip()
    receipt_tag = f"receipt={receipt}"
    if receipt_tag not in notes:
        notes = (notes + ("; " if notes else "") + receipt_tag).strip()

    values = {
        "ts_iso": args.ts_iso,
        "chat_id": args.chat_id,
        "message_id": args.message_id,
        "author_id": args.author_id,
        "author_name": args.author_name,
        "item": args.item,
        "price": args.price,
        "currency": args.currency,
        "category": args.category,
        "project_code": args.project_code,
        "notes": notes,
        "raw_text": args.raw_text,
    }

    cmd = [
        sys.executable,
        str((__file__).replace("log_spend_to_excel.py", "graph_excel_append.py")),
        "--client-id",
        CLIENT_ID,
        "--tenant",
        TENANT,
        "--share-url",
        SHARE_URL,
        "--table",
        TABLE,
        "--columns",
        COLUMNS,
        "--values-json",
        json.dumps(values, ensure_ascii=False),
    ]

    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr or p.stdout)
        return p.returncode

    # Normalize output for the agent: include receipt + excel row index when available.
    try:
        out = json.loads(p.stdout)
    except Exception:
        sys.stdout.write(p.stdout)
        return 0

    index = None
    try:
        # Graph rows/add response: result.index (usually)
        index = out.get("result", {}).get("index")
    except Exception:
        index = None

    sys.stdout.write(
        json.dumps(
            {
                "ok": True,
                "receipt": receipt,
                "mode": out.get("mode"),
                "excel_index": index,
                "drive_id": out.get("drive_id"),
                "item_id": out.get("item_id"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
