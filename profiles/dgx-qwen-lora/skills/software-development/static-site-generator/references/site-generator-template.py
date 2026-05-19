#!/usr/bin/env python3
"""
Static site generator template — dark-themed, responsive, single-file output.
Copy and modify for your data source.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
SITE_DIR = PROJECT_ROOT / "site"
SITE_DIR.mkdir(exist_ok=True)

# ── CSS Variables ─────────────────────────────────────────────────────────
CSS_VARS = """
:root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface-hover: #1a1a25;
    --text: #e0e0e0;
    --text-secondary: #888;
    --accent: #4a9eff;
    --accent-dim: #2a5a9e;
    --border: #222;
    --left: #ff6b6b;
    --center: #ffd93d;
    --right: #6bcb77;
}
"""

# ── HTML Template ─────────────────────────────────────────────────────────
SITE_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        {CSS_VARS}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        
        header {{
            text-align: center;
            padding: 3rem 0 2rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }}
        
        h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }}
        .subtitle {{ color: var(--text-secondary); font-size: 1.1rem; }}
        
        .meta {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
            flex-wrap: wrap;
        }}
        
        .story {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .story:hover {{ border-color: var(--accent-dim); }}
        
        .story-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 1rem;
        }}
        
        .story-number {{
            background: var(--accent-dim);
            color: var(--accent);
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
        }}
        
        .story-meta {{ text-align: right; font-size: 0.85rem; color: var(--text-secondary); }}
        .story-meta .topic {{ font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }}
        
        h2 {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 0.75rem; }}
        
        .badge {{
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        
        .badge-left {{ background: rgba(255, 107, 107, 0.15); color: var(--left); }}
        .badge-center {{ background: rgba(255, 217, 61, 0.15); color: var(--center); }}
        .badge-right {{ background: rgba(107, 203, 119, 0.15); color: var(--right); }}
        
        footer {{
            text-align: center;
            padding: 3rem 0;
            margin-top: 3rem;
            border-top: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        
        @media (max-width: 600px) {{
            h1 {{ font-size: 1.75rem; }}
            .story-header {{ flex-direction: column; gap: 0.75rem; }}
            .story-meta {{ text-align: left; }}
            .meta {{ flex-direction: column; gap: 0.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{title}}</h1>
            <p class="subtitle">{{subtitle}}</p>
            <div class="meta">
                <span>📅 {{date}}</span>
                <span>📊 {{count}} items</span>
            </div>
        </header>
        
        <main>
            {{content}}
        </main>
        
        <footer>
            <p>Generated {{generated_at}}</p>
        </footer>
    </div>
</body>
</html>
"""

# ── Render Functions ──────────────────────────────────────────────────────

def render_item(item: dict, index: int) -> str:
    """Render a single item card. Modify for your data structure."""
    return f"""
        <article class="story">
            <div class="story-header">
                <span class="story-number">{index}</span>
                <div class="story-meta">
                    <div class="topic">{item.get("category", "general").title()}</div>
                </div>
            </div>
            <h2>{item.get("title", "Untitled")}</h2>
            <p>{item.get("description", "")}</p>
        </article>
    """


def render_methodology(methodology) -> str:
    """Handle both dict and string methodology fields."""
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
    
    paragraphs = methodology.split("\n\n")
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())


# ── Main Generator ────────────────────────────────────────────────────────

def generate_site():
    """Generate site from latest data file."""
    data_files = sorted(DATA_DIR.glob("*.json"), reverse=True)
    if not data_files:
        print("ERROR: No data files found")
        return
    
    latest = data_files[0]
    with open(latest) as f:
        data = json.load(f)
    
    # Render content
    content_html = ""
    for i, item in enumerate(data.get("items", []), 1):
        content_html += render_item(item, i)
    
    if not content_html:
        content_html = "<p>No items to display.</p>"
    
    # Build final HTML
    html = SITE_TEMPLATE.format(
        title=data.get("title", "Daily Digest"),
        subtitle=data.get("subtitle", ""),
        date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
        count=len(data.get("items", [])),
        content=content_html,
        generated_at=datetime.now().isoformat(),
    )
    
    # Write files
    index_path = SITE_DIR / "index.html"
    with open(index_path, "w") as f:
        f.write(html)
    
    # Archive copy
    dated_path = SITE_DIR / f"{data.get('date', 'archive')}.html"
    shutil.copy(index_path, dated_path)
    
    print(f"Site generated: {index_path}")
    print(f"Archive: {dated_path}")


if __name__ == "__main__":
    generate_site()
