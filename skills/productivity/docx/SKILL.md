---
name: docx
version: "1.0.0"
description: |
  Complete DOCX document creation, editing, and analysis. Supports creating new
  documents, modifying content, handling revisions, adding comments, and
  professional Word document generation across scenes: reports, resumes,
  contracts, academic papers, official docs, marketing copy, exams.
license: Proprietary (Z.AI document-skills)
compatibility: Python 3.10+ with python-docx, defusedxml; Node.js for docx-js route
metadata:
  author: Z.AI (ported to hermes)
  hermes:
    tags: [docx, word, documents, writing, reports, resumes, contracts]
    category: documents
    requires_tools: [terminal, execute_code]
    priority: high
---

# DOCX Creation, Editing, and Analysis

Full Word document capability ported from Z.AI document-skills. A .docx file
is a ZIP archive containing XML files. This skill provides tools for creating,
editing, reading, and reviewing Word documents.

## When to Use
- User wants a Word document created (report, resume, contract, paper)
- User needs to edit or modify an existing .docx
- User wants to analyze, review, or extract from a .docx
- User asks to write, draft, or generate a document

## Scenes (document types)
Each scene has a template in scenes/:
- report.md — business/technical reports
- resume.md — resumes and CVs
- contract.md — legal contracts
- academic.md — academic papers
- official-doc.md — official/formal documents
- copywriting.md — marketing copy
- exam.md — exams and assessments

## Workflow

### Creating a new document
1. Determine the scene (document type) and load scenes/SCENE.md
2. Load references/design-system.md for cover recipes, palettes, chart colors
3. Load references/common-rules.md for layout, font, and quality rules
4. Load references/docx-js-core.md for the document generation API
5. Generate the document via the docx-js or python-docx route
6. Run scripts/postcheck.py to validate the output

### Editing an existing document
1. Unzip the .docx to inspect its XML structure
2. Load references/ooxml.md for OOXML element references
3. Make targeted XML edits or use python-docx
4. Re-zip into the output .docx

### Analyzing a document
1. Extract text via python-docx
2. Extract comments via the comment XML parts
3. Check revisions via the revision XML parts

## Key References
- references/docx-js-core.md — core document generation API
- references/docx-js-advanced.md — advanced features (charts, math, fields)
- references/design-system.md — visual design (covers, palettes, typography)
- references/common-rules.md — layout, fonts, quality rules
- references/ooxml.md — raw OOXML element reference
- references/toc.md — table of contents generation
- references/chart-templates.md — chart insertion

## Qwopus-Specific Notes
- For simple docs, use python-docx directly via execute_code (faster, reliable)
- For complex layouts, use the docx-js route (needs Node.js)
- Build documents in stages: outline first, then fill sections
- Use working_memory to hold the document structure while writing
