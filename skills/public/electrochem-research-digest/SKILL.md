---
name: electrochem-research-digest
description: "Monitor recent research progress and news in electrochemical engineering (CO2 electrolysis/CO2R, AEM water electrolysis, H2 separation/compression, carbon capture & conversion, electrochemical pH swing) and deliver a daily highlights digest with source links. Use when you need to gather new journal articles (title, lead author, abstract excerpt) and relevant funding/investment news (news sites; limited support for LinkedIn/Bluesky) and send a concise summary message daily."
---

# Electrochem Research Digest

Produce a daily digest for Aaron with highlights + links across electrochemical engineering research and related funding/investment news.

## Output format (Telegram-friendly)

- Target: **6 papers + 4 news** (vary as needed, but keep **< 15 items total**).
- For **journal articles** include:
  - Title
  - Lead author
  - Abstract excerpt (1–3 sentences) or “abstract not available”
  - Link
- For **news/funding** include:
  - Headline + 1–2 sentence summary
  - Link

## Workflow

1) Gather candidate items (past 24h or since last run)
- Prefer RSS feeds and publisher listing pages where possible.
- Use web search for news/funding.
- LinkedIn / Bluesky: **best-effort via web search** (no login scraping). If a specific public URL/RSS/feed is provided later, prefer that.

2) De-duplicate
- Same URL/title → keep best source.

3) Classify
- `journal` vs `news/social`

4) Extract fields
- journal: title, lead author, abstract excerpt, link
- news/social: headline, short summary, link

5) Send digest
- One message per day to Aaron.

## Sources

See `references/sources.md` for the target journals, topics, and key groups, plus limitations.

## Scripts

- `scripts/build_digest.py` formats a list of items into a digest message.
