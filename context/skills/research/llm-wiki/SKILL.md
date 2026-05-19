---
title: Karpathy's LLM Wiki Pattern
name: llm-wiki
version: 1.0.0
author: Andrej Karpathy (adapted for Hermes)
description: Build and maintain a persistent, compounding knowledge base as interlinked markdown files. Compilation over retrieval.
trigger: When saving research findings, building a knowledge base, or when the user says "wiki", "knowledge base", "interlinked notes", or "compounding knowledge".
---

# Karpathy's LLM Wiki Pattern

## Core Philosophy

Most RAG systems rediscover knowledge from scratch on every query. The LLM Wiki pattern instead **compiles knowledge once, keeps it current**.

> "The knowledge is compiled once and then kept current, not re-derived on every query."
> — Andrej Karpathy

## How It Works

### 1. Ingest Source
When you add a new document/paper/article:
- LLM reads it fully
- Extracts key information
- Identifies entities, claims, and relationships

### 2. Integrate into Wiki
The LLM updates the existing wiki:
- **New entity** → create page
- **Existing entity** → update page, add new info
- **Contradiction** → flag it, note both claims
- **Connection** → add cross-links between pages

### 3. Maintain Over Time
- Revisit pages when new sources arrive
- Strengthen or challenge evolving synthesis
- Keep cross-references current

## Wiki Structure

```
~/hermes/knowledge/wiki/
├── index.md              # Master index / table of contents
├── topics/
│   ├── agent-architecture.md
│   ├── prompting-patterns.md
│   └── production-systems.md
├── entities/
│   ├── karpathy-andrej.md
│   ├── anthropic.md
│   └── hermes-agent.md
├── sources/
│   ├── 2026-05-paper-name.md
│   └── 2026-04-article-name.md
└── contradictions.md     # Log of conflicting claims
```

## Page Template

```markdown
# [Entity/Topic Name]

## Summary
One-paragraph synthesis of what this is.

## Key Claims
- Claim 1 ([source](#source-1))
- Claim 2 ([source](#source-2))

## Related
- [[Related Topic A]]
- [[Related Entity B]]
- [[Contradiction: Some Other Claim]]

## Sources
1. [Source Name](url) — date, key insight
2. [Source Name](url) — date, key insight

## Last Updated
YYYY-MM-DD
```

## Integration with Hermes

### save_finding upgrade
Instead of standalone files, save_finding should:
1. Check if related wiki pages exist
2. Update or create entity pages
3. Add cross-references
4. Log contradictions if found

### Using with Obsidian
- Set `~/hermes/knowledge/wiki/` as Obsidian vault
- Use graph view to see connections
- Browse interlinked knowledge in real-time

### Automation
```bash
# Cron job: weekly wiki maintenance
hermes cron create --name wiki-maintenance --schedule "0 9 * * 1" \
  --prompt "Review all new findings from the past week. Update wiki pages, add cross-references, flag contradictions."
```

## Workflow Example

**User:** "I just read a paper on sparse autoencoders"

**Hermes:**
1. Reads paper via web_extract
2. Creates/updates `topics/sparse-autoencoders.md`
3. Updates `entities/anthropic.md` (if Anthropic paper)
4. Links to `topics/mechanistic-interpretability.md`
5. Checks for contradictions with existing SAE claims
6. Updates `index.md` with new entry

## Benefits Over RAG

| RAG | LLM Wiki |
|-----|----------|
| Retrieve chunks per query | Compile once, keep current |
| No accumulation | Compounding knowledge |
| Rediscover every time | Synthesis already done |
| Flat document store | Interlinked graph |
| No contradiction handling | Explicit contradiction logging |

## References
- Original gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Hermes knowledge dir: ~/.hermes/knowledge/
