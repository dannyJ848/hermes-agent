#!/usr/bin/env python3
"""
Deep Research orchestration engine for local models.

Local models (Qwopus 27B) can't do frontier-grade single-shot research, but
they CAN do excellent focused subtasks. This engine breaks deep research into
a pipeline of small, reliable steps that compound into a strong result.

Pipeline:
  1. PLAN    — decompose the question into sub-questions
  2. SEARCH  — web search + PDF extraction per sub-question
  3. EXTRACT — pull key facts/quotes from each source
  4. SYNTH   — combine extracted facts into a structured answer
  5. CITE    — attach sources, flag confidence, note gaps

Each step is a discrete, verifiable unit the model can do well.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERMES_PYTHON = "/data/SpecForge/venv/bin/python"
PDF_SCRIPT = "/home/djg6228/.hermes-glm/skills/pdf/scripts/pdf.py"


@dataclass
class ResearchSubQuestion:
    question: str
    search_queries: list = field(default_factory=list)
    sources: list = field(default_factory=list)  # {url, title, snippet, extracted}
    findings: list = field(default_factory=list)  # key facts extracted
    status: str = "pending"  # pending | searching | extracted | done | failed


@dataclass
class ResearchPlan:
    main_question: str
    sub_questions: list = field(default_factory=list)  # ResearchSubQuestion
    scope: str = "general"  # general | academic | technical | market
    depth: str = "standard"  # quick | standard | deep


def plan_research(question: str, depth: str = "standard") -> ResearchPlan:
    """Decompose a research question into sub-questions.

    The model calls this to structure the work. Returns a plan the model
    then executes step-by-step via search_extract.
    """
    plan = ResearchPlan(main_question=question, depth=depth)

    # Heuristic decomposition: break into facets the model should investigate.
    # The model can override/refine this, but this gives a starting structure.
    facets = [
        ("definition", f"What is {question}? Core definition and scope."),
        ("current_state", f"What is the current state of {question} as of 2026?"),
        ("key_players", f"Who are the key organizations/people in {question}?"),
        ("evidence", f"What evidence, data, or studies exist about {question}?"),
        ("counterarguments", f"What are the criticisms or limitations of {question}?"),
    ]
    if depth == "deep":
        facets.extend([
            ("history", f"What is the historical context and trajectory of {question}?"),
            ("implications", f"What are the future implications of {question}?"),
        ])
    elif depth == "quick":
        facets = facets[:3]

    for facet_id, q in facets:
        plan.sub_questions.append(ResearchSubQuestion(question=q))

    return plan


def search_and_extract(
    query: str,
    max_sources: int = 5,
    extract_pdf: bool = True,
) -> list:
    """Search the web and extract content from top results.

    Uses kimi-webbridge/firecrawl for search, pdf.py for PDF extraction.
    Returns a list of source dicts with extracted content.
    """
    sources = []
    # The actual search happens via the web_search tool in the harness.
    # This function is called BY the model after it runs web_search and
    # collects URLs — it handles the extraction phase.
    #
    # In practice the model will:
    #   1. Call web_search(query) -> get URLs
    #   2. For each URL, call web_extract(url) -> get content
    #   3. For PDF URLs, call this helper to run pdf.py extract.text
    #
    # This helper handles the PDF extraction part (the part that needs
    # the local pdf.py script).
    if extract_pdf and query.endswith(".pdf"):
        try:
            result = subprocess.run(
                [HERMES_PYTHON, PDF_SCRIPT, "extract.text", query],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                sources.append({
                    "url": query,
                    "type": "pdf",
                    "extracted": data.get("data", {}).get("pages", []),
                    "chars": data.get("data", {}).get("total_chars", 0),
                })
        except Exception as e:
            sources.append({"url": query, "type": "pdf", "error": str(e)})
    return sources


def synthesize_findings(plan: ResearchPlan) -> dict:
    """Structure the research output for the model to write up.

    Returns a structured summary the model turns into prose. This is the
    scaffold — the model does the actual writing (its strength).
    """
    sections = []
    for sq in plan.sub_questions:
        if sq.findings:
            sections.append({
                "facet": sq.question,
                "findings": sq.findings,
                "source_count": len(sq.sources),
                "status": sq.status,
            })
    return {
        "main_question": plan.main_question,
        "depth": plan.depth,
        "sections": sections,
        "total_sources": sum(len(s.sources) for s in plan.sub_questions),
        "total_findings": sum(len(s.findings) for s in plan.sub_questions),
        "gaps": [s.question for s in plan.sub_questions if s.status != "done"],
    }


if __name__ == "__main__":
    # CLI: python research_skill.py plan "question" [--depth standard|deep|quick]
    if len(sys.argv) < 3:
        print("Usage: research_skill.py plan|extract|synth <args>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "plan":
        question = sys.argv[2]
        depth = "standard"
        if "--depth" in sys.argv:
            depth = sys.argv[sys.argv.index("--depth") + 1]
        plan = plan_research(question, depth)
        print(json.dumps({
            "main_question": plan.main_question,
            "depth": plan.depth,
            "sub_questions": [sq.question for sq in plan.sub_questions],
        }, indent=2))
