---
name: deep-research
version: "1.0.0"
description: |
  Multi-step deep research orchestration for local models. Decomposes complex
  questions into sub-questions, searches multiple sources (web + PDF), extracts
  key findings, and synthesizes a cited report. Designed for Qwopus 27B:
  plays to local-model strengths (focused subtasks) rather than requiring
  frontier-model single-shot synthesis.
license: MIT
compatibility: Hermes Agent with web_search, web_extract, pdf skill, execute_code
metadata:
  author: hermeshub
  hermes:
    tags: [research, deep-research, synthesis, citations, multi-step]
    category: research
    requires_tools: [web_search, web_extract, terminal, execute_code]
    priority: high
    related_skills: [pdf, data-analyst]
---

# Deep Research (Local-Model Optimized)

Structured research pipeline that turns a complex question into a cited,
multi-source report. Built for Qwopus: each step is a small, reliable unit
the model handles well.

## When to Use
- User asks for research, analysis, or a literature review
- User wants a report on a topic with sources
- User needs to compare options with evidence
- User says research, investigate, analyze, find out about

## The Pipeline (5 stages)

### Stage 1: PLAN
Decompose the question into 3-7 sub-questions (facets):
- Definition: what is it?
- Current state: where does it stand in 2026?
- Key players: who matters?
- Evidence: what data/studies exist?
- Counterarguments: what are the limitations?

For deep research, add historical context and future implications.
For quick research, use only the first 3 facets.

Run the planner:
    /data/SpecForge/venv/bin/python /home/djg6228/.hermes-glm/skills/deep-research/scripts/research_skill.py plan "YOUR QUESTION" --depth standard

### Stage 2: SEARCH
For EACH sub-question:
1. Call web_search with a focused query
2. Collect 3-5 relevant URLs from results
3. For each URL, call web_extract to get the content
4. For PDF URLs, use the pdf skill: pdf.py extract.text then the URL

### Stage 3: EXTRACT
From each source, pull 2-4 key findings:
- Specific facts with numbers and dates
- Direct quotes (keep short, attribute)
- Data points (save for tables and charts)
Discard: marketing fluff, speculation without evidence

### Stage 4: SYNTHESIZE
Combine findings across sources into a structured answer:
- One paragraph per facet (sub-question)
- Lead with the strongest evidence
- Note where sources agree vs disagree
- Flag uncertainty explicitly

### Stage 5: CITE
- Number each source
- Attach citations inline
- Include a sources list at the end with URLs
- Note confidence: high when multiple sources agree, medium for single source,
  low when inferred or gap exists

## Output Format

Structure the final report as:
1. Executive summary (2-3 sentences)
2. Main findings (one section per facet)
3. Data tables (if applicable)
4. Sources (numbered, with URLs)
5. Confidence assessment and gaps

## Qwopus-Specific Notes

- Do ONE sub-question at a time. Do not batch since context fills fast.
- Use working_memory tool to store findings between steps
- If a source is dense, extract just the relevant section, not the whole page
- Prefer PDF extraction for academic and technical sources (more reliable than HTML)
- When context gets large (over 50 percent), use context_stash to offload completed facets
- The model writes the final report. The pipeline just structures the work.
