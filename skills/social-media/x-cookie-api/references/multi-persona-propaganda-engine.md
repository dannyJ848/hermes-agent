# Multi-Persona Propaganda Demystification Engine — Reference

Complete implementation built 2026-05-15. Source: `~/propaganda-demystifier/`

## Project Structure

```
~/propaganda-demystifier/
├── config/personas.yaml          # Persona definitions
├── personas/                     # Cookie files per persona
│   ├── left_lens_cookies.json
│   ├── center_lens_cookies.json
│   └── right_lens_cookies.json
├── scanner.py                    # Multi-persona feed scanner
├── digest_generator.py           # Daily digest + bias decomposition
├── site_generator.py             # Static HTML site generator
├── run_pipeline.py               # Orchestrates scan → digest → site
├── site/index.html               # Generated output
└── README.md
```

## Core Components

### scanner.py

- Loads cookies per persona from `personas/{name}_cookies.json`
- Extracts fresh GraphQL hashes from X's JS bundle
- Scans followed accounts (UserTweets) and search queries (SearchTimeline POST)
- Deduplicates tweets across personas by `text[:80]`
- Identifies cross-persona stories and sensational language

Key functions:
- `load_persona_cookies(name)` → dict with auth_token, ct0, twid
- `create_session(cookies)` → authenticated requests.Session
- `get_gql_hashes(session)` → extracts current query hashes
- `scan_persona_feed(persona, hashes)` → returns tweets + metadata

### digest_generator.py

- Loads latest scan from `scans/scan_*.json`
- Filters by engagement threshold (default 50)
- Clusters by topic (politics, foreign_policy, economy, health, tech, culture)
- Analyzes framing per persona (loaded language, emotional appeal, omissions)
- Generates neutral summary with transparency notes

Output formats:
- JSON: `digests/digest_YYYY-MM-DD.json`
- Markdown: `digests/digest_YYYY-MM-DD.md`

### site_generator.py

- Dark-themed static HTML (no framework)
- Color-coded personas: red=left, yellow=center, green=right
- Mobile-responsive CSS
- Archive links for past digests
- Transparency section with methodology notes

## Persona YAML Schema

```yaml
personas:
  - name: "left_lens"              # internal key
    display_name: "Left Lens"      # human label
    bias_indicator: "left"         # for color coding
    follows:                       # accounts to scan
      - AOC
      - BernieSanders
    search_queries:                # search terms
      - "from:AOC OR from:BernieSanders"
    
verification_sources:            # for cross-reference
  domestic_wire:
    - https://apnews.com
  international:
    - https://bbc.com/news

narrative_keywords:              # loaded language to flag
  - "breaking"
  - "slammed"
  - "bombshell"

output:
  site_title: "The Lens"
  author_pseudonym: "The Curator"
  max_stories_per_digest: 10
  min_engagement_threshold: 50
  digest_time: "06:00"
```

## Running the Pipeline

```bash
cd ~/propaganda-demystifier
python3 run_pipeline.py
```

Steps:
1. Scan all personas → `scans/scan_*.json`
2. Generate digest → `digests/digest_*.json` + `*.md`
3. Build site → `site/index.html` + `site/YYYY-MM-DD.html`

## Cron Setup

```bash
0 6 * * * cd ~/propaganda-demystifier && python3 run_pipeline.py >> logs/cron.log 2>&1
```

## Cookie Extraction

For each persona account:
1. Open X in Chrome, log in
2. DevTools → Application → Cookies → x.com
3. Copy `auth_token`, `ct0`, `twid`
4. Save to `personas/{name}_cookies.json`:
```json
{
  "auth_token": "FULL_HEX_STRING_HERE",
  "ct0": "CSRF_TOKEN_HERE",
  "twid": "u%3DNUMERIC_USER_ID"
}
```

## Engagement Scoring

```python
engagement_score = likes + retweets * 3 + replies * 2
```

Retweets weighted higher (endorsement signal).

## Topic Clustering Keywords

| Topic | Keywords |
|-------|----------|
| politics | biden, trump, congress, senate, election, vote, campaign, gop, democrat, republican |
| foreign_policy | ukraine, russia, china, israel, gaza, iran, nato, war, diplomacy, sanctions |
| economy | inflation, jobs, unemployment, gdp, recession, fed, interest rates, stock market |
| health | covid, vaccine, healthcare, medicare, medicaid, fda, cdc, pandemic |
| tech | ai, artificial intelligence, google, meta, apple, microsoft, regulation, privacy |
| culture | lgbtq, trans, abortion, roe, supreme court, justice, rights, protest |

## Known Issues

- Scanner returns 401 with placeholder cookies (expected — need real auth)
- SearchTimeline requires POST (not GET)
- GraphQL hashes rotate — always extract fresh
- Rate limits: 2s between UserTweets, 3s between SearchTimeline
