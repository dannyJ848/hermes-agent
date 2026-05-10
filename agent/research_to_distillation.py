"""Research-to-Distillation Bridge.

Converts wiki research findings into actionable distillation tips that get
injected into the agent's behavior via the bottom-up/top-down pipeline.

FLOW:
1. AGI cron does research → saves to wiki + knowledge library
2. This bridge scans new findings → extracts actionable implementation steps
3. Implementation steps become distilled_tips with high initial confidence
4. Tips flow through top-down injection → change actual agent behavior
5. Behavioral changes measured via tool success rates → feedback to tips

This closes the loop: Research → Knowledge → Capability → Measurement → Improvement
"""
import json
import os
import re
import sqlite3
import time
from pathlib import Path

WIKI_DIR = Path.home() / "wiki" / "concepts"
CEREBRUM_DB = Path.home() / ".hermes" / "cerebrum_memory.db"
KNOWLEDGE_DIR = Path.home() / ".hermes" / "knowledge"


def _extract_implementation_steps(content: str) -> list[dict]:
    """Extract 'Implementation for Evey' sections from wiki pages."""
    steps = []
    
    # Find the implementation section
    impl_match = re.search(
        r'## Implementation for Evey\s*\n(.*?)(?=\n## |\Z)',
        content, re.DOTALL
    )
    if not impl_match:
        return steps
    
    impl_text = impl_match.group(1)
    
    # Parse bullet points with **Action** or **Missing** markers
    for line in impl_text.split('\n'):
        line = line.strip()
        if not line.startswith('-'):
            continue
        
        # Extract the action/missing item
        line = line.lstrip('- ')
        
        # Determine type
        tip_type = "strategy"
        if '**Action**' in line:
            tip_type = "action"
            line = line.replace('**Action**:', '').replace('**Action**', '').strip()
        elif '**Missing**' in line:
            tip_type = "gap"
            line = line.replace('**Missing**:', '').replace('**Missing**', '').strip()
        elif '**Distillation**' in line:
            tip_type = "distillation"
            line = line.replace('**Distillation**:', '').replace('**Distillation**', '').strip()
        elif 'Implemented' in line:
            continue  # Skip already implemented items
        else:
            tip_type = "strategy"
        
        if len(line) > 20:  # Skip trivially short items
            steps.append({
                "recommendation": line[:200],
                "type": tip_type,
            })
    
    return steps


def _extract_concept_name(content: str, filename: str) -> str:
    """Get the concept name from the wiki page."""
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    return filename.replace('.md', '').replace('-', ' ').title()


def _extract_source(content: str) -> str:
    """Get the paper source from the wiki page."""
    source_match = re.search(r'\*\*Source:\*\* (.+)$', content, re.MULTILINE)
    if source_match:
        return source_match.group(1).strip()
    return "wiki-research"


def research_to_tips(force: bool = False) -> dict:
    """Scan wiki concepts and convert findings into distilled tips.
    
    Returns stats about what was converted.
    """
    # DISABLED: Research-to-distillation seeding produces speculative tips
    # ("From research: ...") that pollute the tips table with non-operational content.
    # Re-enable only if wiki content is refactored into actionable tool-specific rules.
    return {"error": "Research tip seeding disabled — tips must be operational", "tips_created": 0}
    
    if not WIKI_DIR.exists():
        return {"error": "Wiki directory not found", "tips_created": 0}
    
    stats = {
        "pages_scanned": 0,
        "tips_created": 0,
        "tips_skipped": 0,
        "tips_by_type": {},
    }
    
    db = sqlite3.connect(str(CEREBRUM_DB), timeout=5)
    
    try:
        # Get existing tips to avoid duplicates
        existing = set(
            row[0] for row in db.execute(
                "SELECT recommendation FROM distilled_tips"
            ).fetchall()
        )
        
        for md_file in sorted(WIKI_DIR.glob("*.md")):
            content = md_file.read_text()
            concept = _extract_concept_name(content, md_file.name)
            source = _extract_source(content)
            steps = _extract_implementation_steps(content)
            
            stats["pages_scanned"] += 1
            
            for step in steps:
                rec = step["recommendation"]
                tip_type = step["type"]
                
                # Skip if tip already exists (fuzzy match)
                if any(rec[:50] in existing_rec for existing_rec in existing):
                    stats["tips_skipped"] += 1
                    continue
                
                # Determine tool_name from the recommendation
                tool_name = _infer_tool(rec)
                
                # Insert as research-derived tip
                now = time.time()
                db.execute(
                    "INSERT INTO distilled_tips "
                    "(tip_type, condition, recommendation, rationale, tool_name, "
                    "domain, confidence, upvotes, downvotes, frequency, "
                    "source_ids, created_at, last_seen, last_used) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (tip_type, f"From research: {concept}", rec,
                     f"Research finding from {source}",
                     tool_name, "research",
                     0.7,  # High initial confidence for research-derived tips
                     3,    # Start with 3 upvotes (research-backed)
                     0, 1,
                     f"wiki:{md_file.name}",
                     now, now, now)
                )
                
                existing.add(rec)
                stats["tips_created"] += 1
                stats["tips_by_type"][tip_type] = stats["tips_by_type"].get(tip_type, 0) + 1
        
        db.commit()
    
    finally:
        db.close()
    
    return stats


def _infer_tool(recommendation: str) -> str:
    """Infer which tool a recommendation applies to."""
    rec_lower = recommendation.lower()
    
    tool_keywords = {
        "terminal": ["terminal", "shell", "bash", "command", "docker", "git "],
        "execute_code": ["execute_code", "python", "import from hermes"],
        "read_file": ["read_file", "offset", "limit", "pagination"],
        "write_file": ["write_file", "create file"],
        "patch": ["patch", "find-and-replace", "edit file"],
        "search_files": ["search_files", "grep", "rg", "find file"],
        "web_extract": ["web_extract", "extract url", "crawl"],
        "web_research": ["web_research", "web search", "search online"],
        "delegate": ["delegate", "subagent", "parallel"],
        "memory": ["memory", "cerebrum", "consolidation"],
        "skill_manage": ["skill", "skill_manage"],
        "mesh": ["mesh", "agent mesh", "multi-agent"],
        "distillation": ["distill", "tip", "bottom-up", "top-down"],
    }
    
    for tool, keywords in tool_keywords.items():
        if any(kw in rec_lower for kw in keywords):
            return tool
    
    return "general"


if __name__ == "__main__":
    result = research_to_tips()
    print(json.dumps(result, indent=2))
