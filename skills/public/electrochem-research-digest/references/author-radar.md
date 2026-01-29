# Author radar

This file defines the “who to watch” list for electrochem engineering research.

## Seed list (manual)

- Ted Sargent
- David Sinton
- Peter Strasser
- Tom Burdyny
- Brian Seger
- Haotian Wang
- Shannon Boettcher
- Curtis Berlinguette

## Auto-population (heuristic)

Goal: periodically expand the radar to include highly active authors/groups in the target journal set.

Suggested method (no paywalled scraping):

1) Use Crossref works API to count papers per author name over the last N years, filtered by journal container-title (best-effort).
2) Rank by counts, then keep top K and/or those above a threshold.
3) Maintain a denylist for common-name false positives.

Caveats:
- Author-name matching can be ambiguous (e.g. “Wang”). Prefer adding full names you recognize.
- Container-title strings vary; use multiple synonyms and treat results as approximate.

Implementation helper: `scripts/author_radar_crossref.py`.
