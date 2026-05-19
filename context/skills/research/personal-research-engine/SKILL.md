---
title: Personal Research Engine with Hermes
name: personal-research-engine
version: 1.0.0
author: Ian Lapham / Hermes adaptation
description: Set up a continuous research system that ingests, organizes, retrieves, and connects knowledge through recurring workflows. High-ROI agent setup.
trigger: When the user wants to set up automated research, knowledge management, recurring information gathering, or says "research engine", "personal wiki", "knowledge base", or "continuous learning".
---

# Personal Research Engine with Hermes

## Overview

After 2 months of everyday use, a personal research engine is one of the highest-ROI things you can do if you like learning. — Ian Lapham

A personal research engine continuously:
1. **Ingests** — RSS feeds, APIs, newsletters, papers, web content
2. **Organizes** — structures and classifies information
3. **Retrieves** — semantic search over accumulated knowledge
4. **Connects** — links disparate pieces into coherent understanding

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Ingestion  │───▶│ Organization│───▶│  Retrieval  │◀───│   Query     │
│             │    │             │    │             │    │             │
│ • RSS feeds │    │ • save_finding│   │ • knowledge_│    │ • User asks │
│ • news_scan │    │ • LLM Wiki  │    │   search    │    │ • Cron job  │
│ • web_extract│   │ • Interlink │    │ • Qdrant DB │    │ • Subagent  │
│ • APIs      │    │ • Tagging   │    │ • Semantic  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                                                    │
       └────────────────────────────────────────────────────┘
                          Connection Layer
```

## Setup

### 1. Ingestion Sources

Configure cron jobs for recurring data intake:

```bash
# Daily news scan
hermes cron create --name daily-news \
  --schedule "0 9 * * *" \
  --prompt "Scan AI news for interesting developments. Save 3 most relevant findings to knowledge base."

# Weekly paper digest
hermes cron create --name weekly-papers \
  --schedule "0 10 * * 1" \
  --prompt "Search arXiv for papers on [your topics]. Extract key insights, save to knowledge base."

# RSS feed monitoring (if RSS skill available)
hermes cron create --name rss-monitor \
  --schedule "0 */6 * * *" \
  --prompt "Check RSS feeds for new posts. Summarize and save relevant ones."
```

### 2. Organization System

Use the LLM Wiki pattern (see skill: llm-wiki):

```
~/.hermes/knowledge/research/
├── topics/           # Thematic pages
├── entities/         # People, orgs, projects
├── sources/          # Individual papers/articles
├── raw/              # Unprocessed findings
└── index.md          # Master index
```

### 3. Retrieval Setup

Already built into Hermes:
- `knowledge_search` — semantic search over all indexed docs
- `session_search` — recall past conversations
- `web_research` — real-time web search for gaps

### 4. Connection Layer

The key differentiator: not just storing, but **connecting**:

```python
# When saving a finding, auto-link to related topics
from hermes_tools import knowledge_search

# Find related existing knowledge
related = knowledge_search("similar: " + finding_title, limit=5)

# Update wiki pages with cross-references
# Flag contradictions
# Suggest new connections
```

## Daily Workflow

### Morning (automated)
1. Cron runs news scan → findings saved
2. Cron runs RSS check → new posts summarized
3. Knowledge base updated with overnight content

### On Demand
```bash
# Quick knowledge query
hermes knowledge_search "latest on sparse autoencoders"

# Deep research
hermes "Research [topic]. Read 5 sources, synthesize, save to wiki."

# Connection discovery
hermes "What connects [topic A] and [topic B] in my knowledge base?"
```

## Example: Setting Up for a New Topic

```bash
# 1. Create topic page
hermes "Create wiki page for 'mechanistic interpretability' with key concepts, researchers, and papers."

# 2. Set up monitoring
hermes cron create --name mi-news \
  --schedule "0 9 * * *" \
  --prompt "Search for news on mechanistic interpretability, sparse autoencoders, and feature visualization. Save top 3 findings."

# 3. Initial deep dive
hermes "Deep research on mechanistic interpretability. Read Anthropic's recent work, distill key insights, connect to existing ML knowledge."

# 4. Weekly synthesis
hermes cron create --name mi-weekly \
  --schedule "0 18 * * 5" \
  --prompt "Review all mechanistic interpretability findings from this week. Synthesize into weekly summary, update main topic page, flag contradictions."
```

## Tools Used

| Tool | Purpose |
|------|---------|
| `news_scan` | Daily AI news monitoring |
| `web_research` | Targeted web search |
| `web_extract` | Full article extraction |
| `save_finding` | Save to knowledge base |
| `knowledge_search` | Semantic retrieval |
| `cronjob` | Recurring workflows |
| `llm-wiki` skill | Interlinked organization |

## ROI Factors

- **Time saved** — no more re-researching topics you've already explored
- **Connection discovery** — LLM finds links you'd miss
- **Contradiction detection** — flags when sources disagree
- **Compounding** — each finding makes the next one more valuable
- **Availability** — knowledge accessible 24/7 via natural language queries

## References
- Original tweet: https://x.com/ianlapham/status/2052567929049272571
- LLM Wiki skill: see llm-wiki
- Hermes knowledge system: ~/.hermes/knowledge/
