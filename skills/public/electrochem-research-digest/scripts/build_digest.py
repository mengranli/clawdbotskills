#!/usr/bin/env python3
"""Build a daily electrochem research digest.

MVP implementation:
- Use Brave Search (via Clawdbot web_search tool) in-agent OR run this script with
  pre-fetched JSON.

This script is a placeholder for deterministic formatting.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    # Read a list of items from stdin and format markdown.
    # Item schema (recommended): {type, title, url, source, date, lead_author, abstract}
    raw = sys.stdin.read().strip()
    items = json.loads(raw) if raw else []

    lines = [f"Electrochem digest ({now_iso()})", ""]
    for it in items:
        title = it.get("title", "(no title)")
        url = it.get("url", "")
        source = it.get("source", "")
        lead = it.get("lead_author")
        abstract = it.get("abstract")

        head = f"- {title}"
        if source:
            head += f" — {source}"
        if url:
            head += f"\n  {url}"
        if lead:
            head += f"\n  Lead author: {lead}"
        if abstract:
            head += f"\n  Abstract: {abstract.strip()}"
        lines.append(head)
        lines.append("")

    sys.stdout.write("\n".join(lines).strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
