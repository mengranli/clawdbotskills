#!/usr/bin/env python3
"""Update an author "radar" based on recent RSS items.

Workflow (intended):
- Read RSS URLs from references/sources.md (best-effort extraction)
- Fetch feeds
- For each item, extract dc:creator list; count lead author appearances
- Persist rolling counts to a state file (default in ~/.clawdbot)
- Output suggestions: most frequent authors not already in the seed radar

This avoids paywalled scraping and does not require any API keys.

Usage:
  python update_author_radar.py --days 30 --top 25

Outputs JSON on stdout.

Dependencies: requests (stdlib xml.etree)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from xml.etree import ElementTree as ET

DC = "{http://purl.org/dc/elements/1.1/}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _default_state_path() -> Path:
    p = Path(os.path.expanduser("~/.clawdbot"))
    p.mkdir(parents=True, exist_ok=True)
    return p / "electrochem_author_radar_counts.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_urls_from_sources_md(text: str) -> list[str]:
    # Pull http(s) links; keep RSS-ish ones.
    urls = re.findall(r"https?://[^\s)]+", text)
    # strip trailing punctuation
    cleaned = [u.rstrip(".,;") for u in urls]

    def is_rss(u: str) -> bool:
        if u.endswith(".rss"):
            return True
        if "showFeed" in u and "feed=rss" in u:
            return True
        if u.endswith("/rss"):
            return True
        return False

    return sorted({u for u in cleaned if is_rss(u)})


def normalize_name(name: str) -> str:
    # Collapse whitespace; keep capitalization as-is but strip.
    n = re.sub(r"\s+", " ", name).strip()
    # Remove dangling punctuation
    return n.strip(" ,;\t\n\r")


def lead_author_from_creators(creators: list[str]) -> str | None:
    if not creators:
        return None
    # Cross-publisher variance; creators can include "A; B; C" or "A, B".
    first = creators[0]
    first = re.split(r"\s*(?:;|,| and )\s*", first)[0]
    return normalize_name(first)


def parse_rss(xml_text: str) -> list[dict]:
    # Parse RSS 1.0 (rdf) or RSS 2.0
    root = ET.fromstring(xml_text)
    items = []

    # Nature/AAAS/ACS are RDF-ish with <item>
    for it in root.findall(".//item"):
        creators = [c.text for c in it.findall(f"{DC}creator") if c.text]
        date_el = it.find(f"{DC}date")
        date = date_el.text.strip() if (date_el is not None and date_el.text) else None
        link_el = it.find("link")
        link = link_el.text.strip() if (link_el is not None and link_el.text) else None
        title_el = it.find(f"{DC}title") or it.find("title")
        title = title_el.text.strip() if (title_el is not None and title_el.text) else None
        items.append({"title": title, "link": link, "date": date, "creators": creators})

    return items


def parse_date(s: str) -> datetime | None:
    # Nature feeds use YYYY-MM-DD
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"updated_at": None, "counts": {}}  # name -> count
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources-md", default=str(Path(__file__).resolve().parents[1] / "references" / "sources.md"))
    ap.add_argument("--state", default="")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--sleep", type=float, default=0.2)
    ap.add_argument("--seed", default="", help="Optional path to author-radar.md to exclude existing names")
    ap.add_argument("--apply", action="store_true", help="Append suggested names into author-radar.md under an auto-added section (requires Aaron approval before running in production)")
    ap.add_argument("--min-count", type=int, default=3, help="Minimum count (in rolling state) to auto-add when --apply is set")
    ap.add_argument("--deny", default="", help="Comma-separated denylist of names to never auto-add")

    args = ap.parse_args()

    sources_text = _read_text(Path(args.sources_md))
    urls = extract_urls_from_sources_md(sources_text)

    cutoff = _now() - timedelta(days=args.days)

    state_path = Path(args.state) if args.state else _default_state_path()
    state = load_state(state_path)
    counts = Counter({k: int(v) for k, v in state.get("counts", {}).items()})

    # Load seed names to exclude from suggestions
    seed_names: set[str] = set()
    seed_path = Path(args.seed) if args.seed else (Path(__file__).resolve().parents[1] / "references" / "author-radar.md")
    if seed_path.exists():
        txt = seed_path.read_text(encoding="utf-8")
        for line in txt.splitlines():
            m = re.match(r"^-\s+(.+)$", line.strip())
            if m:
                seed_names.add(normalize_name(m.group(1)))

    fetched = []
    new_counts = Counter()

    for u in urls:
        try:
            r = requests.get(u, timeout=30)
            r.raise_for_status()
            items = parse_rss(r.text)
            for it in items:
                dt = parse_date(it.get("date") or "")
                if dt and dt < cutoff:
                    continue
                lead = lead_author_from_creators(it.get("creators") or [])
                if lead:
                    new_counts[lead] += 1
            fetched.append({"url": u, "ok": True})
        except Exception as e:
            fetched.append({"url": u, "ok": False, "error": str(e)})
        time.sleep(args.sleep)

    counts.update(new_counts)

    deny = {normalize_name(x) for x in args.deny.split(",") if x.strip()}

    suggestions = [
        (name, c)
        for name, c in counts.most_common(args.top * 3)
        if name not in seed_names and name not in deny
    ][: args.top]

    # Optionally append to author-radar.md
    applied = []
    if args.apply and suggestions:
        add_names = [name for name, c in suggestions if c >= args.min_count]
        add_names = [n for n in add_names if n not in seed_names and n not in deny]
        if add_names:
            ar_path = seed_path
            txt = ar_path.read_text(encoding="utf-8") if ar_path.exists() else "# Author radar\n"
            if "## Auto-added (pending review)" not in txt:
                txt = txt.rstrip() + "\n\n## Auto-added (pending review)\n\n"
            # Append only missing names
            for n in add_names:
                if re.search(rf"^\s*-\s+{re.escape(n)}\s*$", txt, flags=re.MULTILINE):
                    continue
                txt += f"- {n}\n"
                applied.append(n)
            ar_path.write_text(txt, encoding="utf-8")

    out = {
        "ok": True,
        "updated_at": _now().replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "cutoff": cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "feeds": fetched,
        "new_counts_window": dict(new_counts),
        "suggestions": suggestions,
        "applied": applied,
        "state_path": str(state_path),
    }

    # Persist
    state["updated_at"] = out["updated_at"]
    state["counts"] = dict(counts)
    save_state(state_path, state)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
