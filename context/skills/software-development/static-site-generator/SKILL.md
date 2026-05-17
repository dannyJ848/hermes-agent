---
name: static-site-generator
title: Static Site Generation from Structured Data
description: |
  Generate production-ready static HTML sites from JSON/markdown data sources.
  Dark-themed, responsive, self-contained single-file output. Ideal for digests,
  reports, dashboards, and narrative analysis presentations.
triggers:
  - When generating a static site from JSON data
  - When building HTML reports from structured data
  - When creating dark-themed presentation sites
  - When the user says "generate site", "build HTML", "static site"
category: software-development
---

# Static Site Generation from Structured Data

## Overview

Generate self-contained static HTML sites from structured data (JSON, markdown, YAML).
Output is a single `index.html` with embedded CSS — no build step, no dependencies,
no external assets required.

## Architecture

```
Data Source (JSON) → Python Generator → index.html (single file)
```

### Input Format

```json
{
  "date": "2026-05-16",
  "title": "The Lens - Daily Digest",
  "stories": [
    {
      "headline": "Story Title",
      "topic": "politics",
      "core_claims": ["claim 1", "claim 2"],
      "framing_differences": [
        {"persona": "left_lens", "framing_style": "..."}
      ],
      "sample_tweets": [
        {"author": "user", "text": "...", "engagement": "10K"}
      ],
      "engagement_total": 100000
    }
  ],
  "narrative_analysis": {
    "total_sources_scanned": 4,
    "total_tweets_analyzed": 472,
    "cross_persona_stories": [],
    "sensational_language_frequency": {"breaking": 5}
  },
  "transparency_notes": ["note 1"],
  "methodology": {"personas_used": ["Left", "Right"]}
}
```

## Generator Pattern

### Template Structure

Use Python f-string templates with CSS-in-HTML:

```python
SITE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {
            --bg: #0a0a0f;
            --surface: #12121a;
            --text: #e0e0e0;
            --text-secondary: #888;
            --accent: #4a9eff;
            --accent-dim: #2a5a9e;
            --border: #222;
        }
        /* ... full CSS ... */
    </style>
</head>
<body>
    <div class="container">
        <header>...</header>
        <nav>...</nav>
        <main>{stories}</main>
        <section class="analysis">{analysis}</section>
        <footer>...</footer>
    </div>
</body>
</html>
"""
```

### Rendering Functions

```python
def render_story(story: dict, index: int) -> str:
    """Render a single story card."""
    claims_html = "".join(f"<li>{c}</li>" for c in story.get("core_claims", []))
    framing_html = render_framing(story.get("framing_differences", []))
    tweets_html = render_tweets(story.get("sample_tweets", [])[:3])
    
    return f"""
        <article class="story">
            <div class="story-header">
                <span class="story-number">{index}</span>
                <div class="story-meta">
                    <div class="topic">{story.get("topic", "").title()}</div>
                    <div class="engagement">{story.get("engagement_total", 0):,}</div>
                </div>
            </div>
            <h2>{story.get("headline", "Untitled")}</h2>
            <div class="core-claims"><ul>{claims_html}</ul></div>
            <div class="framing">{framing_html}</div>
            <div class="tweets">{tweets_html}</div>
        </article>
    """
```

### Methodology Handling

Methodology field may be dict or string — handle both:

```python
def render_methodology(methodology) -> str:
    if not methodology:
        return "<p>No methodology notes.</p>"
    
    if isinstance(methodology, dict):
        items = []
        for key, value in methodology.items():
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)
            items.append(f"<li><strong>{label}:</strong> {value_str}</li>")
        return f"<ul>{''.join(items)}</ul>"
    
    # String format
    paragraphs = methodology.split("\n\n")
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
```

**Pitfall:** Always check `isinstance(methodology, dict)` before calling `.split()` — JSON data often has structured methodology objects, not strings.

## CSS Design System

### Dark Theme Variables

```css
:root {
    --bg: #0a0a0f;           /* Deep black-blue */
    --surface: #12121a;       /* Card background */
    --surface-hover: #1a1a25; /* Hover state */
    --text: #e0e0e0;          /* Primary text */
    --text-secondary: #888;   /* Metadata, labels */
    --accent: #4a9eff;        /* Links, highlights */
    --accent-dim: #2a5a9e;    /* Badges, borders */
    --border: #222;           /* Dividers */
}
```

### Persona Badges

Color-code ideological lenses or categories:

```css
.persona-left { background: rgba(255, 107, 107, 0.15); color: #ff6b6b; }
.persona-center { background: rgba(255, 217, 61, 0.15); color: #ffd93d; }
.persona-right { background: rgba(107, 203, 119, 0.15); color: #6bcb77; }
.persona-personal { background: rgba(192, 132, 252, 0.15); color: #c084fc; }
```

### Responsive Breakpoints

```css
@media (max-width: 600px) {
    h1 { font-size: 1.75rem; }
    .story-header { flex-direction: column; gap: 0.75rem; }
    .meta { flex-direction: column; gap: 0.5rem; }
    .analysis-grid { grid-template-columns: 1fr; }
}
```

## Archive System

Generate dated copies for historical access:

```python
def generate_site():
    # Find latest digest
    digest_files = sorted(DIGESTS_DIR.glob("digest_*.json"), reverse=True)
    latest = digest_files[0]
    
    with open(latest) as f:
        digest = json.load(f)
    
    # Generate archive links (last 7 days)
    archive_links = ""
    for df in digest_files[:7]:
        date_str = df.stem.replace("digest_", "")
        if date_str != digest["date"]:
            archive_links += f'<a href="{date_str}.html">{date_str}</a>'
    
    # Build HTML
    html = SITE_TEMPLATE.format(
        title=digest["title"],
        date=digest["date"],
        archive_links=archive_links,
        stories=render_stories(digest.get("stories", [])),
        analysis=render_analysis(digest.get("narrative_analysis", {})),
        # ... other sections
    )
    
    # Write files
    index_path = SITE_DIR / "index.html"
    with open(index_path, "w") as f:
        f.write(html)
    
    # Archive copy
    dated_path = SITE_DIR / f"{digest['date']}.html"
    shutil.copy(index_path, dated_path)
```

## Deployment Options

| Option | Command | Best For |
|--------|---------|----------|
| GitHub Pages | `git push` | Free, versioned, custom domain |
| Netlify | Drag & drop or CLI | Instant, branch previews |
| Cloudflare Pages | `wrangler deploy` | Global CDN, edge caching |
| Self-hosted | `rsync` to VPS | Full control, existing infra |
| DGX | `rsync` to `/var/www/` | Internal dashboards |

### Deploy Script Template

```bash
#!/bin/bash
SITE_DIR="$(dirname "$0")/site"

echo "Choose deployment option:"
echo "1) GitHub Pages"
echo "2) Netlify"
echo "3) DGX/VPS"
echo "4) Local preview"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        cd "$SITE_DIR"
        git init && git add . && git commit -m "Initial"
        git remote add origin https://github.com/USER/REPO.git
        git push -u origin main
        ;;
    2)
        npx netlify-cli deploy --prod --dir="$SITE_DIR"
        ;;
    3)
        read -p "Host: " host
        read -p "Path: " path
        rsync -avz --delete "$SITE_DIR/" "$host:$path/"
        ;;
    4)
        open "$SITE_DIR/index.html"
        ;;
esac
```

## Pipeline Integration

Static site generation works best as the **third stage** of a modular pipeline:

```
scanner.py → digest_generator.py → site_generator.py → bot/run_bots.py
```

### Why this order matters

1. **Scanner** collects raw data (tweets, articles, metrics)
2. **Digest generator** analyzes, deduplicates, and structures findings into JSON
3. **Site generator** renders the JSON into HTML — pure presentation, no business logic
4. **Bot distributor** posts links to the generated site

### JSON as the contract

The digest JSON is the stable interface between stages. Each stage reads the previous stage's output and writes its own:

```python
# digest_generator.py output
{
  "date": "2026-05-16",
  "title": "Daily Digest",
  "stories": [...],
  "narrative_analysis": {
    "total_sources_scanned": 4,
    "total_tweets_analyzed": 472,
    "cross_persona_stories": [],
    "sensational_language_frequency": {...}
  },
  "methodology": {"personas_used": [...], "engagement_threshold": 50},
  "transparency_notes": [...]
}
```

The site generator reads this JSON and knows exactly what fields to expect. If the digest format changes, only the site generator needs updating — not the scanner or digest generator.

### Type safety for digest fields

**Pitfall (May 16, 2026):** The `methodology` field may be either a `dict` or a `string` depending on the digest generator version. Always type-check before rendering:

```python
def render_methodology(methodology) -> str:
    if not methodology:
        return "<p>No methodology notes.</p>"
    
    if isinstance(methodology, dict):
        items = []
        for key, value in methodology.items():
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)
            items.append(f"<li><strong>{label}:</strong> {value_str}</li>")
        return f"<ul>{''.join(items)}</ul>"
    
    # String format (legacy or alternative generator)
    paragraphs = methodology.split("\n\n")
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
```

**Other fields with type variability:**
- `engagement_total` vs `total_engagement` — different generators use different keys. Check both.
- `sample_tweets` may be nested under stories or at top level — verify structure before iterating.
## Pitfalls

1. **Methodology type mismatch**: JSON data may have dict methodology — always `isinstance` check before string operations
2. **Archive link drift**: Use `df.stem.replace("digest_", "")` not hardcoded dates
3. **CSS specificity wars**: Use CSS variables and BEM-like naming to avoid conflicts
4. **Mobile viewport**: Always test at 375px width (iPhone SE) — flex columns break differently than grid
5. **Emoji in titles**: Some terminals strip emoji from file paths — use text-only in `<title>`
6. **rsync --delete danger**: Verify destination path matches exactly before using `--delete`
7. **Terminal heredocs with `&`**: When writing deploy scripts with shell heredocs, the `&` character triggers backgrounding detection. Use `write_file` instead of terminal heredocs for scripts containing ampersands.

## References

| `references/dark-theme-css.md` — Complete dark theme CSS variable system
| `references/site-generator-template.py` — Full working generator template
| `references/deploy-script.sh` — Multi-option deployment script
