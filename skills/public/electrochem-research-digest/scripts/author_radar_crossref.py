#!/usr/bin/env python3
"""Build/update an author "radar" list using Crossref counts.

Purpose
- Identify high-activity authors for the electrochem digest by counting papers in
  selected journals over recent years.

This is best-effort: Crossref metadata is imperfect and author-name ambiguity is real.
Use the output as suggestions for Aaron to confirm.

Usage
  python author_radar_crossref.py --years 2 --top 30

Dependencies: requests
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import time
from typing import Iterable

import requests

CROSSREF = "https://api.crossref.org/works"

DEFAULT_JOURNALS = [
    "Nature Energy",
    "Nature Chemical Engineering",
    "Nature Catalysis",
    "Nature Communications",
    "Nature",
    "Nature Chemistry",
    "Nature Materials",
    "Nature Sustainability",
    "Science",
    "Science Advances",
    "ACS Energy Letters",
    "ACS Catalysis",
    "Energy & Environmental Science",
    "Joule",
    "Advanced Materials",
]


def year_range(years: int) -> tuple[int, int]:
    now = dt.datetime.now(dt.timezone.utc)
    end = now.year
    start = end - max(1, years) + 1
    return start, end


def crossref_count(author: str, journal: str, start_year: int, end_year: int) -> int:
    # We use rows=0 and ask Crossref for total-results. Filter by from-pub-date.
    params = {
        "rows": 0,
        "query.author": author,
        "filter": f"from-pub-date:{start_year}-01-01,until-pub-date:{end_year}-12-31",
        # container-title is not always reliable; use it as a query term.
        "query.container-title": journal,
    }
    r = requests.get(CROSSREF, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return int(data.get("message", {}).get("total-results", 0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--journals", help="JSON array of journal names (overrides default)")
    ap.add_argument("--sleep", type=float, default=0.2, help="polite delay between calls")

    args = ap.parse_args()

    journals = DEFAULT_JOURNALS
    if args.journals:
        journals = json.loads(args.journals)

    start_y, end_y = year_range(args.years)

    # Seed authors we care about; output is for suggesting additional names.
    # In practice, you would expand this by harvesting authors from RSS hits.
    seed_authors: list[str] = []

    # If no seed authors are provided, this script does nothing useful; keep it
    # as a helper that can be extended.
    if not seed_authors:
        print(
            json.dumps(
                {
                    "ok": True,
                    "note": "No seed authors provided; extend script to harvest author candidates from RSS/Crossref results.",
                    "years": args.years,
                    "start_year": start_y,
                    "end_year": end_y,
                    "journals": journals,
                },
                indent=2,
            )
        )
        return 0

    scores = collections.Counter()
    for author in seed_authors:
        for j in journals:
            try:
                c = crossref_count(author, j, start_y, end_y)
            except Exception as e:
                c = 0
            scores[(author, j)] = c
            time.sleep(args.sleep)

    # Aggregate across journals
    agg = collections.Counter()
    for (author, _j), c in scores.items():
        agg[author] += c

    top = agg.most_common(args.top)
    print(json.dumps({"ok": True, "years": args.years, "start_year": start_y, "end_year": end_y, "top_authors": top}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
