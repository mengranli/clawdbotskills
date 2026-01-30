#!/usr/bin/env python3
"""Simple local idempotency helper for spend logging.

Goal: prevent double-logging the same Telegram message.

Key idea: compute a stable key like: "telegram:-1003711269809:message:12345"

Workflow:
- BEFORE appending: run `check`.
  - exit 0 => not seen
  - exit 10 => already seen
- AFTER a successful Excel append: run `mark`.

State is stored in a JSON file (default: ~/.clawdbot/lab_spend_ledger_dedupe.json).

This script is intentionally simple and local to the bot host.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


EXIT_ALREADY_SEEN = 10


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_path(p: str | None) -> Path:
    if p:
        return Path(p).expanduser()
    d = Path(os.path.expanduser("~/.clawdbot"))
    d.mkdir(parents=True, exist_ok=True)
    return d / "lab_spend_ledger_dedupe.json"


def load(p: Path) -> dict:
    if not p.exists():
        return {"version": 1, "seen": {}}  # key -> metadata
    return json.loads(p.read_text(encoding="utf-8"))


def save(p: Path, data: dict) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check", "mark"])
    ap.add_argument("--key", required=True)
    ap.add_argument("--state", default="")
    ap.add_argument("--meta", default="", help="Optional JSON metadata to store on mark")

    args = ap.parse_args()
    sp = state_path(args.state or None)
    data = load(sp)
    seen = data.setdefault("seen", {})

    if args.mode == "check":
        if args.key in seen:
            return EXIT_ALREADY_SEEN
        return 0

    # mark
    meta = {}
    if args.meta:
        meta = json.loads(args.meta)
    meta.setdefault("marked_at", now_iso())
    seen[args.key] = meta
    save(sp, data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
