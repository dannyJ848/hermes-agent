---
name: mobile-css-responsiveness-audit
version: 1.0.0
description: Systematic audit of React/TypeScript + CSS projects for mobile viewport issues (320px-375px iPhone SE support)
tags: [css, mobile, responsive, audit, react]
---

# Mobile CSS Responsiveness Audit

Systematic approach for auditing React/TypeScript + CSS projects for mobile viewport issues (320px-375px iPhone SE support).

## Trigger
- User asks to "audit mobile responsiveness", "check 375px breakpoint", "fix iPhone SE layout", or similar
- Working on a web app that needs mobile support

## Methodology

### 1. Map the project
```bash
find src -name "*.css" -o -name "*.tsx" | head -50
```

### 2. Scan for hardcoded widths that break on small screens
```bash
grep -n 'width:.*[0-9]\+px' styles.css | grep -v 'max-width\|100%'
grep -n 'min-width:.*[3-9][0-9][0-9]px' styles.css
```

Key thresholds:
- **> 375px fixed width**: Breaks on iPhone SE -- MUST fix
- **> 320px min-width**: Risky for smallest devices
- **Any width > 480px without mobile override**: Needs @media query

### 3. Check for existing mobile overrides BEFORE adding new ones
```bash
grep -n '@media.*max-width.*768\|@media.*max-width.*480\|@media.*max-width.*375' styles.css
```

Many components already have @media (max-width: 768px) overrides. Only add fixes for gaps.

### 4. Common fixes by pattern

#### Fixed-width panels
```css
.some-panel { width: 380px; max-width: 90vw; }
```

#### nowrap text hints (common overflow source)
```css
.hint { white-space: nowrap; max-width: calc(100vw - 40px); overflow: hidden; text-overflow: ellipsis; }
```

#### Container height for mobile browsers
```css
.view { height: 100vh; height: 100dvh; padding-bottom: env(safe-area-inset-bottom, 0px); }
```

#### min-width panels that can't fit
```css
.panel { min-width: 280px; max-width: min(480px, calc(100vw - 32px)); }
```

#### JS-side viewport awareness (radial menus, positioned elements)
```tsx
const radius = typeof window !== 'undefined' && window.innerWidth < 420 ? 80 : 110;
```

### 5. Verify brace balance after CSS edits
```bash
OPEN=$(grep -c '{' file.css); CLOSE=$(grep -c '}' file.css)
```

### 6. Always verify existing iOS fixes are present
- font-size: 16px on all inputs/textareas (prevents iOS auto-zoom)
- env(safe-area-inset-*) for notch/home indicator
- -webkit-overflow-scrolling: touch for scrollable containers
- overscroll-behavior: contain for chat/message lists

## Pitfalls
- **Don't double-add @media blocks**: Check existing overrides first
- **Don't replace working max-width: 90vw**: Already viewport-relative is fine
- **Long translated strings**: Spanish/French text is ~20-30% longer -- test nowrap elements
- **JS hardcoded pixel distances**: Radial/spread menus need viewport-aware fallbacks
- **100vh vs 100dvh**: Mobile browsers have dynamic toolbars, always provide 100dvh
- **Brace mismatches**: When patching @media blocks, verify closing } isn't duplicated
