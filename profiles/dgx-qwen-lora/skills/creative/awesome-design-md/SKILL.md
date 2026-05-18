---
name: awesome-design-md
description: Generate DESIGN.md files using patterns from 31+ real-world production websites. Drop into any project for instant design system.
version: 1.0.0
metadata:
  hermes:
    tags: [design, design-system, design-tokens, ui, components]
    related_skills: [top-design, web-typography, refactoring-ui]
---

# Awesome Design.md

Collection of DESIGN.md files capturing design systems from popular websites.
Drop one into your project and let coding agents build matching UI.

## When to Use

- User wants a DESIGN.md for their project
- User asks for a design system / design tokens
- User wants to standardize UI components
- Starting a new project and need visual specification

## Reference Library

Located at /tmp/awesome-design-md/

Contains design systems from real production sites including:
- Stripe, Vercel, Linear, Supabase (SaaS patterns)
- Tailwind, Radix, Shadcn (DevTool patterns)
- Shopify (E-commerce patterns)
- And more

## Usage

### 1. Browse available design references
```bash
ls /tmp/awesome-design-md/
```

### 2. Read a specific design file for inspiration
```bash
cat /tmp/awesome-design-md/<site-name>.md
```

### 3. Generate a DESIGN.md for current project

Load the most relevant 3-5 reference files, then synthesize a complete DESIGN.md covering:

1. Design Philosophy (3-5 principles)
2. Design Tokens (colors, typography, spacing, borders, motion)
3. Layout System (grid, breakpoints, templates)
4. Component Library (variants, states, accessibility)
5. Patterns & Interactions
6. Responsive Behavior
7. Accessibility (WCAG compliance)
8. Asset Guidelines

### 4. Tailor to tech stack

- Tailwind: Map to config format
- CSS Modules: Output custom properties
- styled-components: Output theme objects
- Shadcn/Radix: Reference their token system

## Output Rules

- Always use real hex/rgb/hsl values
- Always include light + dark mode
- Always include CSS custom properties
- Always include actual px/rem values
- Always show component state matrices as tables
