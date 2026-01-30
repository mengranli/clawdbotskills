#!/usr/bin/env python3
"""Find potential duplicate rows in the Ledger Excel table.

This is used to avoid false "Already logged" claims.

Search strategy:
- Fetch the last N rows from the Excel table.
- Look for rows where (item contains query) OR (raw_text contains query) OR (price == query_price).
- Return matching rows (index + key fields).

Requires running inside the repo venv (msal installed).
"""

from __future__ import annotations

import argparse
import json

import msal  # type: ignore
import os
import base64
from pathlib import Path

import requests

GRAPH = "https://graph.microsoft.com/v1.0"
DEFAULT_SCOPES = ["Files.ReadWrite.All"]


def share_id(url: str) -> str:
    b = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    return "u!" + b


def token_cache_path() -> Path:
    p = Path(os.path.expanduser("~/.clawdbot/msal_token_cache_lab_spend_ledger.json"))
    return p


def get_token(client_id: str, tenant: str = "common") -> str:
    cache = msal.SerializableTokenCache()
    p = token_cache_path()
    if p.exists():
        cache.deserialize(p.read_text())
    app = msal.PublicClientApplication(client_id=client_id, authority=f"https://login.microsoftonline.com/{tenant}", token_cache=cache)
    accts = app.get_accounts()
    res = app.acquire_token_silent(DEFAULT_SCOPES, account=accts[0]) if accts else None
    if not res or "access_token" not in res:
        raise SystemExit("No token available; run device login again")
    if cache.has_state_changed:
        p.write_text(cache.serialize())
    return res["access_token"]


def graph(method: str, url: str, token: str):
    r = requests.request(method, url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
    return r.json()


def resolve_item(token: str, share_url: str):
    sid = share_id(share_url)
    di = graph("GET", f"{GRAPH}/shares/{sid}/driveItem", token)
    drive_id = di["parentReference"]["driveId"]
    item_id = di["id"]
    return drive_id, item_id


def list_rows(token: str, drive_id: str, item_id: str, table: str, top: int = 50):
    return graph("GET", f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook/tables/{table}/rows?$top={top}", token)["value"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--tenant", default="common")
    ap.add_argument("--share-url", required=True)
    ap.add_argument("--table", required=True)
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--q", default="", help="free-text query (matched against item/raw_text)")
    ap.add_argument("--price", type=float, default=None)

    args = ap.parse_args()

    token = get_token(args.client_id, args.tenant)
    drive_id, item_id = resolve_item(token, args.share_url)
    rows = list_rows(token, drive_id, item_id, args.table, top=args.top)

    q = (args.q or "").strip().lower()

    matches = []
    for r in rows:
        idx = r.get("index")
        vals = (r.get("values") or [[]])[0]
        # expected columns: ts_iso,chat_id,message_id,author_id,author_name,item,price,currency,category,project_code,notes,raw_text
        item = str(vals[5]) if len(vals) > 5 else ""
        price = vals[6] if len(vals) > 6 else None
        proj = str(vals[9]) if len(vals) > 9 else ""
        raw = str(vals[11]) if len(vals) > 11 else ""

        ok = False
        if q and (q in item.lower() or q in raw.lower()):
            ok = True
        if args.price is not None:
            try:
                if float(price) == float(args.price):
                    ok = True
            except Exception:
                pass

        if ok:
            matches.append({"index": idx, "item": item, "price": price, "project": proj, "raw_text": raw})

    print(json.dumps({"ok": True, "matches": matches}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
