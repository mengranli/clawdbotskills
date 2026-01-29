#!/usr/bin/env python3
"""Append a row to an Excel Table in a OneDrive/Share link workbook using Microsoft Graph.

Designed to be called by the agent after it has extracted/confirmed fields.

Auth: device-code flow (public client) via MSAL.

Examples:
  ./graph_excel_append.py \
    --client-id b98aa7fe-f1b7-4780-9285-4acf1e25d0e8 \
    --tenant common \
    --share-url "https://onedrive.live.com/..." \
    --table "Ledger" \
    --values-json '{"timestamp_utc":"2026-01-29T12:43:01Z","item":"nitrile gloves","total":28.5,"currency":"AUD","category":"Lab consumables","project_code":"DE"}'

Notes:
- Requires: pip install msal requests
- Best practice: ensure the workbook contains an Excel *Table* named e.g. "Ledger".
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests

try:
    import msal  # type: ignore
except ImportError:
    msal = None


GRAPH = "https://graph.microsoft.com/v1.0"

DEFAULT_SCOPES = [
    # For Excel workbook access through the file
    "Files.ReadWrite.All",
]


def _share_id(share_url: str) -> str:
    b = base64.urlsafe_b64encode(share_url.encode("utf-8")).decode("utf-8")
    b = b.rstrip("=")
    return "u!" + b


def _token_cache_path() -> Path:
    """Return a stable MSAL token cache path.

    Default is outside the repo so it persists across skill repackaging and
    does not get committed.

    Override with env: CLAWD_LEDGER_TOKEN_CACHE
    """
    p = os.environ.get("CLAWD_LEDGER_TOKEN_CACHE")
    if p:
        return Path(p).expanduser()

    state_dir = Path(os.path.expanduser("~/.clawdbot"))
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "msal_token_cache_lab_spend_ledger.json"


def _load_cache() -> "msal.SerializableTokenCache":
    cache = msal.SerializableTokenCache()
    p = _token_cache_path()
    if p.exists():
        cache.deserialize(p.read_text())
    return cache


def _save_cache(cache: "msal.SerializableTokenCache") -> None:
    if not cache.has_state_changed:
        return
    p = _token_cache_path()
    p.write_text(cache.serialize())


def get_access_token(client_id: str, tenant: str, scopes: list[str]) -> str:
    if msal is None:
        raise RuntimeError("Missing dependency: msal. Install with: pip install msal")

    authority = f"https://login.microsoftonline.com/{tenant}"
    cache = _load_cache()
    app = msal.PublicClientApplication(client_id=client_id, authority=authority, token_cache=cache)

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            raise RuntimeError(f"Failed to create device flow: {flow}")
        print(flow["message"], file=sys.stderr)
        result = app.acquire_token_by_device_flow(flow)

    _save_cache(cache)

    if "access_token" not in result:
        raise RuntimeError(f"Auth failed: {result}")
    return result["access_token"]


def graph_json(method: str, url: str, token: str, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Accept"] = "application/json"
    if "json" in kwargs:
        headers["Content-Type"] = "application/json"
    r = requests.request(method, url, headers=headers, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"Graph error {r.status_code} for {url}: {r.text}")
    if r.text:
        return r.json()
    return None


def resolve_drive_item(token: str, share_url: str) -> tuple[str, str]:
    sid = _share_id(share_url)
    data = graph_json("GET", f"{GRAPH}/shares/{sid}/driveItem", token)
    parent_ref = data.get("parentReference", {})
    drive_id = parent_ref.get("driveId")
    item_id = data.get("id")
    if not drive_id or not item_id:
        raise RuntimeError(f"Could not resolve driveId/itemId from share link: {data}")
    return drive_id, item_id


def list_tables(token: str, drive_id: str, item_id: str):
    return graph_json(
        "GET",
        f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook/tables",
        token,
    )


def add_row(token: str, drive_id: str, item_id: str, table: str, values: list):
    # values must be a 2D array: [[...rowValues...]]
    body = {"values": [values]}
    return graph_json(
        "POST",
        f"{GRAPH}/drives/{drive_id}/items/{item_id}/workbook/tables/{table}/rows/add",
        token,
        json=body,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--tenant", default="common")
    ap.add_argument("--share-url", required=True)
    ap.add_argument("--table", required=True, help="Excel Table name or id (recommended: name, e.g. Ledger)")
    ap.add_argument("--columns", help="Comma-separated column order to write")
    ap.add_argument("--values-json", help="JSON object with fields; will be mapped into --columns order")
    ap.add_argument("--list-tables", action="store_true", help="List workbook tables and exit")

    args = ap.parse_args()

    scopes = DEFAULT_SCOPES

    token = get_access_token(args.client_id, args.tenant, scopes)
    drive_id, item_id = resolve_drive_item(token, args.share_url)

    if args.list_tables:
        tables = list_tables(token, drive_id, item_id)
        print(json.dumps({"ok": True, "drive_id": drive_id, "item_id": item_id, "tables": tables}, ensure_ascii=False))
        return 0

    if not args.columns or not args.values_json:
        raise SystemExit("--columns and --values-json are required unless --list-tables is used")

    data = json.loads(args.values_json)
    cols = [c.strip() for c in args.columns.split(",") if c.strip()]

    row = [data.get(c, "") for c in cols]

    res = add_row(token, drive_id, item_id, args.table, row)
    print(json.dumps({"ok": True, "drive_id": drive_id, "item_id": item_id, "result": res}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
