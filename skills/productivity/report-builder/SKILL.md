---
name: report-builder
version: "1.0.0"
description: |
  End-to-end report generation that orchestrates the document suite. Takes a
  topic, runs deep research, synthesizes findings, writes a formatted document
  (DOCX or PDF), and optionally generates slides. This is the "Kimi Works"
  equivalent: one request produces a complete, cited, professional report.
license: MIT
compatibility: Requires deep-research, docx, pdf, and optionally slides skills
metadata:
  author: hermeshub
  hermes:
    tags: [report, document-suite, orchestration, research, writing]
    category: documents
    requires_tools: [web_search, web_extract, terminal, execute_code]
    priority: high
    related_skills: [deep-research, docx, pdf, slides, spreadsheet]
---

# Report Builder (Document Suite Orchestrator)

The capstone skill: turns a request into a complete professional document.
Orchestrates deep-research, docx/pdf, and optionally slides into one workflow.

## When to Use
- User asks for a report, whitepaper, or briefing on a topic
- User wants a research document created end-to-end
- User says "write me a report on X" or "create a document about Y"
- User wants research output delivered as a formatted file

## The Workflow (6 stages)

### Stage 1: SCOPE
Clarify with the user:
- Topic and specific angle
- Output format: DOCX, PDF, or both
- Length: brief (2-3 pages), standard (5-8), comprehensive (10+)
- Audience: executive, technical, academic, general
- Include slides? Include data/charts?

### Stage 2: RESEARCH
Invoke the deep-research skill:
- Plan sub-questions (3-7 facets)
- Search and extract per facet
- Collect findings with citations
- Store in working_memory between stages

### Stage 3: OUTLINE
Build the document structure from research findings:
1. Title page (title, date, author)
2. Executive summary (1 paragraph)
3. Introduction (context, scope)
4. Main body (one section per research facet)
5. Data/findings (tables, charts if applicable)
6. Conclusions
7. Sources (numbered citations)
8. Appendix (if comprehensive)

### Stage 4: DRAFT
Write each section. Use this approach for Qwopus:
- Write ONE section at a time (do not attempt the whole doc in one pass)
- Use working_memory to hold completed sections
- Keep paragraphs focused (3-5 sentences each)
- Cite sources inline as you write
- After each section, stash it and move to the next

### Stage 5: FORMAT
Convert the draft to the output format:
- For DOCX: use the docx skill (python-docx or docx-js)
  - Apply scene template (report.md) for layout
  - Add title page, headers, page numbers
  - Insert charts as images
- For PDF: generate DOCX first, then convert via pdf skill
  - convert.office /tmp/report.docx -o /tmp/report.pdf
  - Or generate HTML and use convert.html

### Stage 6: DELIVER
- Save the file to the user's requested location
- If slides requested, invoke the slides skill to create a deck from the report
- Provide a brief summary of what was produced

## Output Formats

### DOCX Report
Use the docx skill scenes/report.md template:
- Professional cover page
- Table of contents
- Section headers with consistent styling
- Inline citations [1], [2]
- Sources page at end

### PDF Report
Generate via DOCX then convert, or use pdf skill directly:
- For designed reports: use pdf briefs/report.md
- For simple reports: DOCX then convert.office

### With Slides
After the report, create a deck:
- Title slide from report title
- One slide per main section
- Key data as chart slides
- Sources on final slide

## Quality Checklist
Before delivering:
- All claims have citations
- No placeholder text remains
- Document opens correctly (test by reading it back)
- Page numbers and TOC are present
- Sources list is complete and formatted

## Qwopus-Specific Notes
- This is a LONG workflow. Use context_stash between stages.
- The model's job is orchestration + writing. The skills handle formatting.
- If context fills during drafting, stash completed sections and continue.
- Prefer DOCX output (more reliable than direct PDF generation on local).
- For the final PDF, convert from the completed DOCX.
