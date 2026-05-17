# Static Site Generator from Structured Data

**Pattern:** Generate dark-themed, mobile-responsive static HTML sites from JSON/YAML data sources. No framework needed — pure HTML/CSS with embedded styles.

## When to Use

- Daily/weekly digest sites (newsletters, reports, dashboards)
- Documentation sites generated from structured data
- Portfolio sites from JSON resume data
- Any recurring content that needs a static web presence

## Architecture

```
Data Source (JSON/YAML) → Python Generator → Static HTML → Browser/GitHub Pages
```

## Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        :root {
            --bg: #0a0a0f;
            --surface: #12121a;
            --text: #e0e0e0;
            --text-secondary: #888;
            --accent: #4a9eff;
            --border: #222;
        }
        /* ... full CSS ... */
    </style>
</head>
<body>
    <div class="container">
        <header>...</header>
        <nav class="nav">{{archive_links}}</nav>
        <main>{{content}}</main>
        <footer>...</footer>
    </div>
</body>
</html>
```

## Python Generator Pattern

```python
from pathlib import Path
import json

SITE_TEMPLATE = """..."""  # HTML template with {placeholders}

def render_story(story: dict, index: int) -> str:
    """Render one content item as HTML."""
    return f"""
        <article class="story">
            <div class="story-header">
                <span class="story-number">{index}</span>
                <div class="story-meta">
                    <div>{story['topic']}</div>
                    <div>{story['engagement']:,} engagement</div>
                </div>
            </div>
            <h2>{story['headline']}</h2>
            ...
        </article>
    """

def generate_site():
    # Load data
    with open('data.json') as f:
        data = json.load(f)
    
    # Render content
    stories_html = ""
    for i, story in enumerate(data['stories'], 1):
        stories_html += render_story(story, i)
    
    # Build final HTML
    html = SITE_TEMPLATE.format(
        title=data['title'],
        content=stories_html,
        ...
    )
    
    # Write output
    Path('site/index.html').write_text(html)
```

## Design System (Dark Theme Default)

```css
:root {
    --bg: #0a0a0f;           /* Deep background */
    --surface: #12121a;      /* Card background */
    --surface-hover: #1a1a25; /* Hover state */
    --text: #e0e0e0;         /* Primary text */
    --text-secondary: #888;  /* Muted text */
    --accent: #4a9eff;       /* Links, highlights */
    --accent-dim: #2a5a9e;   /* Subtle accents */
    --border: #222;          /* Borders, dividers */
}
```

## Key CSS Patterns

**Container:**
```css
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
}
```

**Cards:**
```css
.story {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: border-color 0.2s;
}
.story:hover {
    border-color: var(--accent-dim);
}
```

**Badges (for labels/tags):**
```css
.badge {
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}
.badge-left { background: rgba(255, 107, 107, 0.15); color: #ff6b6b; }
.badge-center { background: rgba(255, 217, 61, 0.15); color: #ffd93d; }
.badge-right { background: rgba(107, 203, 119, 0.15); color: #6bcb77; }
```

**Responsive:**
```css
@media (max-width: 600px) {
    h1 { font-size: 1.75rem; }
    .story-header { flex-direction: column; gap: 0.75rem; }
}
```

## Automation

**Cron for daily generation:**
```bash
0 6 * * * cd ~/project && python3 generate_site.py
```

**Serve locally:**
```bash
python3 -m http.server 8765 --directory site/
```

**Deploy to GitHub Pages:**
```bash
# Push site/ directory to gh-pages branch
git subtree push --prefix site origin gh-pages
```

## Real-World Example: Propaganda Demystifier

Source: `~/propaganda-demystifier/site_generator.py`

Features:
- 3-color persona coding (red/yellow/green)
- Archive navigation
- Engagement metrics
- Framing analysis display
- Transparency section
- Mobile-responsive

Generated output: `site/index.html` (13KB, zero dependencies)

## Pitfalls

- **No JS framework needed** — pure HTML/CSS is faster, more portable, and easier to host
- **Escape HTML in user content** — always sanitize text before embedding
- **Test on mobile** — use browser devtools device emulation
- **Archive pages** — generate dated copies for historical access
- **CSS variables** — use them for theming without JS
