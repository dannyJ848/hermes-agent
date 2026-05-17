---
name: knowledge-synthesis
description: >
  Synthesize multiple research findings into actionable integration proposals.
  Connects dots across saved findings, maps them to project architecture,
  and generates concrete implementation recommendations. Use after accumulating
  3+ research findings in a domain.
version: 1.0.0
metadata:
  author: hermes
  hermes:
    tags: [research, synthesis, meta-agent, knowledge-management]
    category: meta
    requires_toolsets: [terminal]
---

## Overview

Knowledge Synthesis is the process of connecting dots between separate research
findings to produce insights that are greater than the sum of their parts. This
skill is used after accumulating research findings (via save_finding) to generate
actionable integration proposals.

## When to Use

- After accumulating 3+ saved findings in a related domain
- During "Knowledge Synthesis" time window (12:00-15:00 or after deep research)
- Before starting a new development sprint, to map research to implementation
- When reviewing monthly goals and identifying cross-domain patterns

## Process

### Step 1: Gather Findings

```
1. List all saved findings in ~/.hermes/knowledge/
2. Group by domain: medical-ai, 3d-rendering, agent-frameworks, nlp, data-formats
3. Identify clusters of 3+ related findings
```

### Step 2: Cross-Domain Pattern Detection

Look for these high-value connection types:

| Pattern Type | Example | Value |
|-------------|---------|-------|
| Enabling Tech | WebGPU shaders + anatomy datasets = real-time tissue rendering | High |
| Architecture Fit | FHIR resources + Bilingual terms = auto-translated patient records | High |
| Performance Trade-off | SAM segmentation quality vs. mobile frame budget | Medium |
| Knowledge Gap | Research says X but codebase does Y | Medium |
| Competitive Edge | SOMA can do X that competitors can't | High |

### Step 3: Generate Integration Proposals

For each pattern found, write a structured proposal:

```markdown
## Proposal: [Title]
**Source Findings:** finding-a.md, finding-b.md, finding-c.md
**Pattern Type:** Enabling Tech
**SOMA Impact:** [1-10]
**Implementation Complexity:** [Low/Medium/High]
**Dependencies:** [What must exist first]

### Current State
[What exists now in the codebase]

### Proposed Integration
[Concrete steps to connect the research]

### Expected Outcome
[What this enables when done]

### Risks
[What could go wrong]
```

### Step 4: Save and Prioritize

1. Save proposals as findings: `synthesis-[topic]-proposal.md`
2. Score each proposal using the Selection Algorithm axes
3. Feed top proposals into the next development sprint

## Synthesis Templates

### Medical AI + 3D Rendering
```
Given: [Medical AI model] + [3D rendering technique]
Question: How can [model] enhance [rendering] for [specific anatomy use case]?
Integration path: Model output → Data format → Renderer input → User interaction
```

### Agent Framework + SOMA Architecture
```
Given: [Agent technique] + [SOMA module]
Question: Can [technique] improve [module]'s [quality metric]?
Integration path: Technique adaptation → Code changes → Test → Measure
```

### Data Format + NLP + Bilingual
```
Given: [Data standard] + [NLP approach] + [ES/EN mapping]
Question: Can we auto-translate [standard] fields for Spanish-speaking patients?
Integration path: Standard parser → NLP pipeline → Bilingual mapper → UI display
```

### Step 5: Fill Integration Gaps with Targeted Research

After connecting findings, identify the "glue" between them — the missing technical details that make the connection work. Use targeted `web_research` + `web_extract` to fill these gaps:

```
Example: Found TotalSegmentator (segmentation) + FHIR ImagingStudy (data format)
  Gap: How does DICOM data flow from FHIR to the segmentation model?
  Research: "FHIR ImagingStudy DICOM WADO-RS segmentation pipeline"
  Result: OMI endpoints, DICOMweb bridge, 3D Slicer glTF export chain
```

This turns a synthesis from "these things could connect" into "here's exactly how they connect."

### Step 6: Visualize the Pipeline

Create ASCII architecture diagrams showing data flow between components. Structure as:

```
┌─────────────────────┐
│   LAYER NAME        │
│  component → output │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   NEXT LAYER        │
```

This makes the synthesis immediately actionable — a developer can see the full pipeline at a glance.

## Step 7: SSR Verification — Socratic Decomposition (from Shi et al., Salesforce AI 2025)

Before saving any synthesized finding, decompose key claims into **verifiable (sub-question, sub-answer) pairs** and check each independently against source material. This prevents cascading errors where one wrong claim corrupts the entire synthesis.

```
For each major claim in the synthesis:
1. Extract: "Claim: X because Y"
2. Decompose into sub-questions:
   - Q1: Does source A actually say X? → Verify in extracted text
   - Q2: Is Y the correct reason? → Cross-check with source B
   - Q3: Does the conclusion follow? → Logic check
3. Only keep claims where ALL sub-answers pass
4. Flag uncertain claims with [UNVERIFIED] prefix
```

This is especially critical when synthesizing from 3+ sources — the chance of misattribution grows with each additional source. A single wrong fact propagated to a finding can misdirect future development work.

## Pitfalls
- Don't synthesize too early — wait for 3+ findings in a cluster
- Don't produce proposals without checking if the codebase already handles it
- Always include complexity estimates — some integrations are months of work
- Keep proposals concrete — avoid "we should explore..." language
- Verify findings are still current (within 30 days) before synthesizing
- Don't skip the gap-fill research — without it, synthesis is just "X could connect to Y" rather than "here's how X connects to Y via Z"
- **Don't skip SSR verification** — without step-level claim checking, synthesized findings can contain misattributed facts that cascade into wrong architectural decisions
- Skip PDFs when extracting — use HTML/article pages instead; PDFs often fail to parse cleanly via web_extract
- Expect Medium and Substack paywalls — web_extract often returns only the preview teaser (1-2 paragraphs). Don't waste tokens retrying; move to the next source or search for the same topic on arXiv, the author's blog, or a mirror
- When delegating during research, avoid nemotron-free — it frequently 400s. Prefer glm-5.1 fallback or skip delegation entirely and use direct web_research + web_extract (faster, more reliable for simple extraction tasks)
- When researching consciousness/agent architecture papers, extract from multiple URLs in parallel (3+ web_extract calls at once) — the cross-referencing between sources IS the synthesis, not a separate step
