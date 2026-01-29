# Sources & coverage

## Journals / publishers (preferred)

Primary targets (prefer RSS feeds; fall back to listing pages if RSS is blocked):

### Nature family

- Nature — https://www.nature.com/nature.rss
- Nature Energy — https://www.nature.com/nenergy.rss
- Nature Chemistry — https://www.nature.com/nchem.rss
- Nature Materials — https://www.nature.com/nmat.rss
- Nature Sustainability — https://www.nature.com/natsustain.rss
- Nature Chemical Engineering — https://www.nature.com/natchemeng.rss
- Nature Catalysis — https://www.nature.com/natcatal.rss
- Nature Communications — https://www.nature.com/ncomms.rss

(Other Nature titles often follow the pattern: `https://www.nature.com/<journal>.rss`.)

### AAAS

- Science (TOC) — https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science
- Science Advances (TOC) — https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv

### ACS

- ACS Energy Letters (TOC) — https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=aelccp
- ACS Catalysis (TOC) — https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=accacs

### Cell Press

- Joule (RSS) — https://www.cell.com/joule/rss
  - Note: currently returns a bot challenge (403) from this environment; fall back to Crossref/Semantic Scholar queries for Joule until RSS fetch is accessible.

### RSC

- Energy & Environmental Science — listing page: https://pubs.rsc.org/en/journals/journalissues/ee#!recentarticles
  - Note: could not resolve a stable RSS endpoint from this environment; treat as listing-page scrape for now.

### Other

- Advanced Materials — use listing pages / Crossref queries (RSS varies).

Notes:
- Many are partially paywalled; aim to collect at least: title, authors, date, journal, URL.
- Abstract availability depends on publisher; when unavailable, extract the publicly visible abstract snippet or skip the abstract and note "abstract not available".

## Research groups (people)

Track new papers/posts mentioning:
- Ted Sargent
- David Sinton
- Peter Strasser
- Tom Burdyny
- Brian Seger
- Haotian Wang
- Shannon Boettcher

Heuristics: search for (author:"<name>") via Crossref/Semantic Scholar/arXiv; also keyword search that includes the group name.

## Topics (keywords)

- CO2 electrolysis / CO2 reduction / CO2R
- AEM water electrolysis
- H2 separation / electrochemical compression
- carbon capture and conversion
- electrochemical pH swing
- renewable energy investments/funding

## News / social

Desired sources: news sites, LinkedIn, Bluesky.

Important limitations:
- LinkedIn content is often not accessible without login and cannot be reliably scraped.
- Bluesky has APIs but coverage depends on accounts/feeds and rate limits.

Fallback approach:
- Use web search (Brave) for "funding", "Series A", "seed", "grant", "DOE", "ARPA-E", "Breakthrough Energy", "electrolysis", etc.
- If specific Bluesky handles or RSS/newsletters are provided, include them.
