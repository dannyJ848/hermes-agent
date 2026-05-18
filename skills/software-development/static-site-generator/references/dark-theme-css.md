# Dark Theme CSS Design System

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#0a0a0f` | Page background |
| `--surface` | `#12121a` | Card backgrounds |
| `--surface-hover` | `#1a1a25` | Hover states |
| `--text` | `#e0e0e0` | Primary text |
| `--text-secondary` | `#888` | Labels, metadata |
| `--accent` | `#4a9eff` | Links, highlights |
| `--accent-dim` | `#2a5a9e` | Borders, badges |
| `--border` | `#222` | Dividers |

## Persona Badge Colors

| Lens | Background | Text |
|------|-----------|------|
| Left | `rgba(255, 107, 107, 0.15)` | `#ff6b6b` |
| Center | `rgba(255, 217, 61, 0.15)` | `#ffd93d` |
| Right | `rgba(107, 203, 119, 0.15)` | `#6bcb77` |
| Personal | `rgba(192, 132, 252, 0.15)` | `#c084fc` |

## Typography Scale

| Element | Size | Weight |
|---------|------|--------|
| H1 | 2.5rem | 700 |
| H2 | 1.5rem | 600 |
| H3 | 1.2rem | 600 |
| Body | 1rem | 400 |
| Small | 0.85rem | 400 |
| Badge | 0.7rem | 700 |

## Spacing Scale

| Token | Value |
|-------|-------|
| `--space-xs` | 0.25rem |
| `--space-sm` | 0.5rem |
| `--space-md` | 1rem |
| `--space-lg` | 1.5rem |
| `--space-xl` | 2rem |
| `--space-2xl` | 3rem |

## Responsive Breakpoints

| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | < 600px | Stack columns, reduce font sizes |
| Tablet | 600-900px | 2-column grids |
| Desktop | > 900px | Full layout, max-width container |

## CSS Snippets

### Container
```css
.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
}
```

### Card
```css
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--accent-dim); }
```

### Badge
```css
.badge {
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
```

### Stats Grid
```css
.analysis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}
```
