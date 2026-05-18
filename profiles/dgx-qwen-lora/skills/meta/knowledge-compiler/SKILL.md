---
name: knowledge-compiler
description: >
  Compile raw research into structured, cross-linked knowledge bases that grow
  with use. Based on Karpathy's LLM Knowledge Base pattern (Apr 2026): raw/
  directory → LLM compiles wiki → Q&A against wiki → outputs filed back →
  perpetual enrichment. This is how I build lasting understanding, not just
  collect facts.
triggers:
  - "when I encounter a rich research topic worth deep understanding"
  - "when I have multiple related findings that should be connected"
  - "when Danny shares articles/repos/tweets for deep analysis"
  - "after completing a major research session"
---

# Knowledge Compiler

## Core Philosophy

Most research is consumption — read, summarize, forget. This skill turns research
into compounding knowledge. Every session builds on every previous session. The
knowledge base gets richer with use, not just bigger.

The key insight from Karpathy: at ~100 articles / 400K words, you can do complex
Q&A WITHOUT fancy RAG. The LLM auto-maintains index files and summaries. The
backlink structure enables intelligent traversal. The outputs get filed back in.

## Architecture

```
~/.hermes/knowledge/
├── raw/                    # Source documents (unread)
│   ├── articles/
│   ├── papers/
│   ├── repos/
│   ├── tweets/
│   └── conversations/
├── wiki/                   # Compiled knowledge (auto-maintained)
│   ├── index.md            # Master index with stats
│   ├── concepts/           # Individual concept articles
│   ├── topics/             # Multi-concept topic pages
│   ├── meta/               # Linting reports, health checks
│   └── mocs/               # Maps of Content (topic overviews)
├── output/                 # Generated outputs
│   ├── qa-log/             # Q&A session results
│   ├── summaries/          # Research summaries
│   └── insights/           # Cross-topic insights
└── tools/                  # Custom scripts
    ├── compile.py          # raw/ → wiki/ pipeline
    ├── lint.py             # Health check runner
    └── search.py           # CLI search engine
```

## Pipeline

### Phase 1: Ingest → raw/

When I encounter valuable information:
1. Save source to `raw/` with descriptive filename
2. Extract key content via web_extract or browser
3. Store in Honcho with topic tags for semantic recall

### Phase 2: Compile → wiki/

For each raw source:
1. Extract key concepts and entities
2. Create/update concept articles with `[[backlinks]]`
3. Cross-link to existing wiki articles
4. Add YAML frontmatter (source, date, tags, related concepts, confidence)
5. Update index files (master index + topic MOCs)

### Phase 3: Q&A Against Wiki

When I need to reason:
1. Load relevant wiki sections via index lookup
2. Traverse backlinks for related context
3. Answer grounded in compiled knowledge, cite [[wiki links]]
4. NEVER fabricate — if not in wiki, say so

### Phase 4: File Back → Perpetual Enrichment

After answering or researching:
1. New insights get filed into wiki/
2. Q&A outputs go to output/qa-log/
3. Cross-topic patterns → output/insights/
4. Re-run lint to verify integrity after mutations

### Phase 5: Linting (Health Checks)

Periodic integrity scans:
- Orphan detection: pages with zero backlinks
- Broken links: [[links]] pointing to non-existent pages
- Staleness: pages not reviewed in 30+ days
- Contradictions: pages with conflicting facts
- Coverage gaps: concepts referenced but never given own page
- Duplicate detection: near-identical articles

## Key Principles

1. **I rarely write wiki content directly.** The compilation pipeline writes it.
   I design the structure, the pipeline fills it.

2. **Backlinks are the data structure.** `[[double bracket]]` links create the
   knowledge graph. Every concept links to every related concept.

3. **Outputs feed back in.** Every Q&A session, every research output, every
   insight gets filed back. This is the compounding mechanism.

4. **No fancy RAG needed at scale.** Auto-maintained index files + backlink
   traversal + long context models = sufficient retrieval.

5. **Linting is not optional.** Knowledge rots. Health checks catch decay.

## Duplicate Detection & Cleanup (Hard-Won Lesson, Apr 2026)

**Problem:** When autonomous cron cycles research the same domain repeatedly (because domain_certainty keeps selecting it), the wiki accumulates hundreds of near-identical files. Discovered 221 reasoning-related files out of 720 total (31% duplication).

**Dedup Procedure:**
```python
import os

wiki_dir = os.path.expanduser("~/wiki/concepts")
# 1. Identify topic clusters by keyword
files = [f for f in os.listdir(wiki_dir) if 'reason' in f.lower()]

# 2. Sort by file size (proxy for comprehensiveness — bigger = more detail)
files_with_size = [(f, os.path.getsize(os.path.join(wiki_dir, f))) for f in files]
files_with_size.sort(key=lambda x: -x[1])

# 3. Keep top N most comprehensive, delete the rest
keep = [f for f, _ in files_with_size[:5]]
for f, _ in files_with_size[5:]:
    os.remove(os.path.join(wiki_dir, f))
```

**Prevention Rules:**
1. Before saving a wiki page, ALWAYS check: `ls ~/wiki/concepts/ | grep -i <topic>`
2. If 3+ files already exist on the same topic, SKIP — the domain is well-covered
3. domain_certainty should use wiki file counts as an input signal to avoid re-selecting saturated domains
4. Run dedup lint weekly: group files by first 2 words of filename, flag clusters > 5

## Difference from Cerebrum

Cerebrum is my *working memory* — fast, automatic, biological. The knowledge
compiler is my *research archive* — slow, deliberate, curated. Cerebrum handles
turns and sessions. The knowledge compiler handles weeks and months.

Both feed each other:
- Cerebrum recall surfaces relevant wiki articles during reasoning
- Wiki compilation stores facts that cerebrum can later retrieve
- Cerebrum's consolidation pipeline mirrors the wiki's compilation pipeline
