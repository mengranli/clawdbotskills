# Author radar

This file defines the “who to watch” list for electrochem engineering research.

## Seed list (manual)

**Private:** Do not store personal/name watchlists in the public GitHub repo.

Keep the seed list in a local-only file (not committed), e.g.:
- `~/.clawdbot/electrochem-author-radar-private.txt`

The weekly author-radar updater should propose candidates; Aaron approves any additions.

## Auto-population (heuristic)

Goal: periodically suggest additions to the radar based on high publication activity.

Policy: **Do not auto-add names without Aaron’s approval.** Collect suggestions + counts, ask Aaron to confirm which to add, then update the seed list.

Suggested method (no paywalled scraping):

1) Use Crossref works API to count papers per author name over the last N years, filtered by journal container-title (best-effort).
2) Rank by counts, then keep top K and/or those above a threshold.
3) Maintain a denylist for common-name false positives.

Caveats:
- Author-name matching can be ambiguous (e.g. “Wang”). Prefer adding full names you recognize.
- Container-title strings vary; use multiple synonyms and treat results as approximate.

Implementation helper: `scripts/author_radar_crossref.py`.
