---
name: pdf
version: "1.0.0"
description: |
  Professional PDF toolkit: text/table/image extraction, page operations
  (merge/split/rotate/crop), form filling, office→PDF conversion, HTML→PDF,
  LaTeX→PDF, report/poster/resume generation, and metadata management.
  Use when the user needs to read, create, edit, convert, or analyze PDFs.
license: Proprietary (Z.AI document-skills)
compatibility: Python 3.10+ with pikepdf, pdfplumber, reportlab; Chromium for HTML route
metadata:
  author: Z.AI (ported to hermes)
  hermes:
    tags: [pdf, extraction, documents, reports, forms, conversion, latex]
    category: documents
    requires_tools: [terminal, execute_code]
    priority: high
---

# PDF - Document Production & Processing Workbench

Full PDF capability suite ported from Z.AI document-skills. Runs locally
on the DGX via the hermes venv (/data/SpecForge/venv).

## Setup

Dependencies are already installed in the hermes venv:
- pikepdf 10.9.1 (page ops, metadata, forms)
- pdfplumber 0.11.10 (text/table extraction)
- reportlab (PDF generation)
- LibreOffice (office document conversion)
- Chromium (HTML→PDF rendering)

## Commands (via scripts/pdf.py)

Run with: /data/SpecForge/venv/bin/python /home/djg6228/.hermes-glm/skills/pdf/scripts/pdf.py <command>

### Extraction (PRIORITY — read existing PDFs)
-  — Extract text from PDF
-  — Extract tables from PDF
-  — Extract images from PDF

### Page Operations
-  — Merge multiple PDFs
-  — Split PDF into pages
-  — Rotate pages
-  — Crop pages
-  — Remove blank pages

### Metadata
-  — Get PDF metadata
-  — Set metadata
-  — Brand multiple PDFs

### Forms
-  — Get form field info
-  — Fill PDF form
-  — Export form details

### Conversion
-  — Office doc → PDF (via LibreOffice)
-  — HTML → PDF (via Chromium)
-  — LaTeX → PDF (needs tectonic)
-  — Convert LLM response to PDF

### Generation (reports, posters, resumes)
- Load briefs/report.md, briefs/poster.md, briefs/resume.md for templates
- Use design_engine.py for palette + typography generation
- Use configs/fonts.md and configs/components.md for design system

## Extraction Workflow (most common use)

1. User provides a PDF path
2. Run:  for text
3. Run:  for tables (if structured data)
4. Run:  for figures
5. Synthesize the extracted content for the user

## Generation Workflow

1. Determine document type (report, poster, resume, academic)
2. Load the matching brief from briefs/
3. Load design system from configs/ and typesetting/
4. Generate HTML or LaTeX source
5. Convert to PDF via convert.html or convert.latex

## Notes for Qwopus (local model adaptation)

- Extraction commands are fast and reliable — use freely
- Generation requires multi-step work; break into stages
- For large PDFs, use -p flag to extract specific pages
- Table extraction works best on structured PDFs (financial, scientific)
- For scanned PDFs, use vision_analyze tool on extracted images
