---
name: architecture-diagram
description: Generate professional dark-themed architecture diagrams as standalone HTML/SVG files. Adapts the Cocoon AI diagram generator (github.com/Cocoon-AI/architecture-diagram-generator) for Hermes Agent use. Use when visualizing system architecture, infrastructure, data flow, or any multi-component system.
version: "1.0"
source: https://github.com/Cocoon-AI/architecture-diagram-generator
---

# Architecture Diagram Generator

Generate professional, dark-themed architecture diagrams as standalone HTML files with inline SVG graphics and CSS styling. No dependencies — opens in any browser.

## Design System

### Color Palette (semantic component types)

| Component Type | Fill (rgba) | Stroke | Use For |
|---------------|-------------|--------|---------|
| Frontend/Input | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) | Client apps, UI, input layer |
| Backend/Cognitive | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) | Services, modules, processing |
| Database | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) | Databases, storage, knowledge |
| Cloud/Infrastructure | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) | Cloud services, infra |
| Security/Eval | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) | Auth, evaluation, security |
| Message Bus | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) | Pipelines, buses, queues |
| External/Generic | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) | External systems, infra |

### Typography
- Font: JetBrains Mono (monospace, technical aesthetic)
- Sizes: 12px component names, 9px sublabels, 8px annotations, 7px tiny
- Load via: `<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet">`

### Key SVG Patterns

**Background:** `#020617` with grid pattern:
```svg
<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(30,41,59,0.3)" stroke-width="0.5"/>
</pattern>
```

**Arrow marker:**
```svg
<marker id="arrow" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
  <polygon points="0 0, 10 3.5, 0 7" fill="#475569"/>
</marker>
```

**Component box with opaque background (masks arrows behind it):**
```svg
<rect x="80" y="40" width="160" height="32" rx="6" fill="rgba(8, 51, 68, 0.4)" stroke="#22d3ee" stroke-width="1.5"/>
<rect x="80" y="40" width="160" height="32" rx="6" fill="#0f172a" opacity="0.6"/>
```
Draw the styled rect first, then an opaque rect on top to mask arrows.

**Region/group boundary:** Dashed stroke `stroke-dasharray="4,4"` with transparent fill.
**Security/eval groups:** Rose dashed `stroke-dasharray="4,4"`.
**Cloud regions:** Amber dashed `stroke-dasharray="8,4"`, `rx="12"`.

### Spacing Rules
- Standard component height: 60px (services), 80-120px (larger)
- Minimum vertical gap between components: 40px
- Place connectors/buses IN the gap between components, not overlapping
- Legend OUTSIDE all boundary boxes, at least 20px below lowest boundary

### Critical SVG Rendering Order
1. Background + grid
2. **Connection arrows** (drawn first → render behind everything)
3. Region/group boundaries
4. Component boxes (render on top, masking arrows)
5. Text labels
6. Legend

## Workflow

1. **Gather data** — query DB schemas, file lists, config, module rosters
2. **Identify components** — group by function (input, processing, storage, evaluation, infra)
3. **Map data flows** — which components connect and what data passes between them
4. **Layout** — left-to-right data flow (input → processing → storage → output)
5. **Write HTML** — use write_file to create the standalone .html file
6. **Save to Desktop** — `cp /tmp/diagram.html ~/Desktop/diagram.html` for user access
7. **Cannot preview** — browser_navigate blocks file:// URLs, so user must open manually

## Output Structure

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>[System] Architecture Diagram</title>
  <link href="fonts..." rel="stylesheet">
  <style> /* dark theme, card grid, header */ </style>
</head>
<body>
  <div class="header"> Title + subtitle stats </div>
  <div class="diagram-card">
    <svg viewBox="0 0 W H">
      <!-- grid, arrows, components, legend -->
    </svg>
  </div>
  <div class="cards"> Summary cards grid </div>
  <div class="footer"> Metadata </div>
</body>
</html>
```

## Pitfalls
- browser_navigate CANNOT open file:// URLs — save to Desktop and tell user to open manually
- Semi-transparent fills don't fully mask arrows — add opaque rect underneath
- SVG elements paint in document order — arrows MUST be drawn before component boxes
- Multi-line Python for DB queries must go to temp file, not inline in terminal command (shell quoting)
- For Cortex DB queries: `psycopg2.connect("postgresql://hindsight:hindsight@localhost:5432/cortex")`
