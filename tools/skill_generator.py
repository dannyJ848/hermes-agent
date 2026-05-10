#!/usr/bin/env python3
"""
hermes_skill_generator.py — Auto-generate skills from completed sessions.

Analyzes session history, extracts workflows, generates SKILL.md drafts.
Integrates with manual triggers for on-demand skill creation.

Usage:
  from hermes_skill_generator import generate_skill_from_session, generate_skill_from_topic
  
  # From recent session:
  skill = generate_skill_from_session(hours_back=24)
  
  # From topic:
  skill = generate_skill_from_topic("cron elimination", 
                                    source_files=["hermes_unified_daemon.py"])
"""

import sqlite3
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional

# Import tool logger if available
try:
    from hermes_tool_logger import log_tool_call
    TOOL_LOGGER = True
except ImportError:
    TOOL_LOGGER = False

SKILLS_DIR = Path.home() / ".hermes" / "skills"
CEREBRUM_DB = Path.home() / ".hermes" / "cerebrum_memory.db"

def _sanitize_name(name: str) -> str:
    """Convert to valid skill name."""
    return re.sub(r'[^a-z0-9-]', '-', name.lower())[:64]

def _extract_workflow_from_learnings(learnings: List[Dict]) -> List[Dict]:
    """Extract workflow steps from rapid learnings."""
    steps = []
    
    for learning in learnings:
        lesson = learning.get('lesson', '')
        category = learning.get('category', 'general')
        
        # Extract actionable steps
        # Pattern: "When X, do Y" or "Use Z for W"
        if 'use ' in lesson.lower() or 'when ' in lesson.lower():
            steps.append({
                'trigger': lesson.split('.')[0] if '.' in lesson else lesson[:100],
                'action': lesson,
                'category': category,
                'confidence': learning.get('confidence', 0.5),
            })
    
    # Sort by confidence
    steps.sort(key=lambda x: x['confidence'], reverse=True)
    return steps[:10]  # Top 10 steps

def _extract_pitfalls_from_errors(errors: List[Dict]) -> List[str]:
    """Extract pitfalls from error patterns."""
    pitfalls = []
    
    for error in errors:
        pattern = error.get('pattern_name', '')
        count = error.get('occurrence_count', 0)
        
        if count > 2:  # Recurring error
            pitfalls.append(f"{pattern} (occurred {count} times)")
    
    return pitfalls[:5]

def _generate_skill_md(name: str, description: str, triggers: List[str],
                       steps: List[Dict], pitfalls: List[str],
                       source_files: List[str] = None) -> str:
    """Generate SKILL.md content."""
    
    lines = [
        "---",
        f"name: {name}",
        f"version: 1.0.0",
        f"created: {time.strftime('%Y-%m-%d')}",
        f"auto_generated: true",
        "---",
        "",
        f"# {name.replace('-', ' ').title()}",
        "",
        f"{description}",
        "",
        "## Trigger Conditions",
        "",
    ]
    
    for trigger in triggers:
        lines.append(f"- {trigger}")
    
    lines.extend([
        "",
        "## Steps",
        "",
    ])
    
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. **{step['trigger']}**")
        lines.append(f"   - {step['action']}")
        lines.append(f"   - Category: {step['category']}, Confidence: {step['confidence']:.2f}")
        lines.append("")
    
    if pitfalls:
        lines.extend([
            "## Pitfalls",
            "",
        ])
        for pitfall in pitfalls:
            lines.append(f"- {pitfall}")
        lines.append("")
    
    if source_files:
        lines.extend([
            "## Source Files",
            "",
        ])
        for f in source_files:
            lines.append(f"- `{f}`")
        lines.append("")
    
    lines.extend([
        "## Verification",
        "",
        "- [ ] Test steps in isolation",
        "- [ ] Confirm trigger conditions match real usage",
        "- [ ] Review and refine if needed",
        "",
    ])
    
    return "\n".join(lines)

def generate_skill_from_session(hours_back: int = 24, 
                                 min_confidence: float = 0.7) -> Optional[Dict]:
    """Generate a skill from recent session learnings."""
    
    try:
        conn = sqlite3.connect(str(CEREBRUM_DB))
        c = conn.cursor()
        
        # Get recent learnings
        since = time.time() - (hours_back * 3600)
        c.execute("""
            SELECT lesson, category, confidence, source
            FROM rapid_learnings
            WHERE created_at > ? AND confidence >= ?
            ORDER BY confidence DESC
            LIMIT 20
        """, (since, min_confidence))
        
        learnings = [
            {'lesson': r[0], 'category': r[1], 'confidence': r[2], 'source': r[3]}
            for r in c.fetchall()
        ]
        
        if not learnings:
            return None
        
        # Get error patterns
        c.execute("""
            SELECT pattern_name, occurrence_count
            FROM error_patterns_predictive
            WHERE occurrence_count > 1
            ORDER BY occurrence_count DESC
        """)
        errors = [
            {'pattern_name': r[0], 'occurrence_count': r[1]}
            for r in c.fetchall()
        ]
        
        conn.close()
        
        # Extract workflow
        steps = _extract_workflow_from_learnings(learnings)
        pitfalls = _extract_pitfalls_from_errors(errors)
        
        # Determine skill name from top category
        categories = {}
        for l in learnings:
            cat = l['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        top_category = max(categories, key=categories.get) if categories else "general"
        skill_name = _sanitize_name(f"auto-{top_category}-workflow")
        
        # Generate description
        description = f"Auto-generated skill from {len(learnings)} learnings in the last {hours_back} hours. "
        description += f"Primary domain: {top_category}. "
        if pitfalls:
            description += f"Includes {len(pitfalls)} known pitfalls."
        
        # Generate triggers
        triggers = [f"Working with {top_category}", f"Need to {steps[0]['trigger']}" if steps else "General task"]
        
        # Generate SKILL.md
        skill_md = _generate_skill_md(
            name=skill_name,
            description=description,
            triggers=triggers,
            steps=steps,
            pitfalls=pitfalls,
        )
        
        # Save draft
        skill_dir = SKILLS_DIR / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_md)
        
        result = {
            'name': skill_name,
            'path': str(skill_file),
            'learnings_used': len(learnings),
            'steps_generated': len(steps),
            'pitfalls_found': len(pitfalls),
            'draft': True,
        }
        
        if TOOL_LOGGER:
            log_tool_call("skill_generator", {
                'hours_back': hours_back,
                'skill_name': skill_name,
            }, result, success=True, context="auto_skill")
        
        return result
        
    except Exception as e:
        if TOOL_LOGGER:
            log_tool_call("skill_generator", {
                'hours_back': hours_back,
            }, None, success=False, error=str(e), context="auto_skill")
        return {'error': str(e)}

def generate_skill_from_topic(topic: str, source_files: List[str] = None,
                              description: str = None) -> Dict:
    """Generate a skill from a specific topic and source files."""
    
    skill_name = _sanitize_name(topic)
    
    # Default description
    if not description:
        description = f"Skill for {topic.replace('-', ' ')}. "
        if source_files:
            description += f"Based on {len(source_files)} source files."
    
    # Generate placeholder steps from file analysis
    steps = []
    if source_files:
        for f in source_files:
            file_path = Path(f).expanduser()
            if file_path.exists():
                # Extract first function/class as example step
                content = file_path.read_text()[:1000]
                # Simple heuristic: look for def lines
                defs = re.findall(r'def\s+(\w+)', content)
                if defs:
                    steps.append({
                        'trigger': f"Need to use {defs[0]}",
                        'action': f"Call {defs[0]} from {f}",
                        'category': topic,
                        'confidence': 0.8,
                    })
    
    if not steps:
        steps = [{
            'trigger': f"Working with {topic}",
            'action': f"Refer to {topic} documentation",
            'category': topic,
            'confidence': 0.5,
        }]
    
    # Generate triggers
    triggers = [
        f"Task involves {topic}",
        f"Need {topic.replace('-', ' ')} functionality",
    ]
    
    # Generate SKILL.md
    skill_md = _generate_skill_md(
        name=skill_name,
        description=description,
        triggers=triggers,
        steps=steps,
        pitfalls=[],
        source_files=source_files,
    )
    
    # Save
    skill_dir = SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(skill_md)
    
    return {
        'name': skill_name,
        'path': str(skill_file),
        'steps_generated': len(steps),
        'draft': True,
    }

def list_auto_skills() -> List[Dict]:
    """List all auto-generated skills."""
    auto_skills = []
    
    if not SKILLS_DIR.exists():
        return auto_skills
    
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir() and skill_dir.name.startswith("auto-"):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text()
                # Extract version line
                version = "1.0.0"
                if "version:" in content:
                    version = content.split("version:")[1].split("\n")[0].strip()
                
                auto_skills.append({
                    'name': skill_dir.name,
                    'path': str(skill_file),
                    'version': version,
                    'size': skill_file.stat().st_size,
                })
    
    return auto_skills

if __name__ == "__main__":
    print("=== Skill Generator Test ===")
    
    # Test from session
    print("\nGenerating from session (last 24h):")
    result = generate_skill_from_session(hours_back=24, min_confidence=0.8)
    if result:
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Generated: {result['name']}")
            print(f"Path: {result['path']}")
            print(f"Learnings: {result['learnings_used']}, Steps: {result['steps_generated']}")
    else:
        print("No learnings found with sufficient confidence")
    
    # Test from topic
    print("\nGenerating from topic:")
    topic_result = generate_skill_from_topic(
        "cron-elimination",
        source_files=["~/hermes-agent/agent/hermes_unified_daemon.py"],
        description="Systemic shift from cron to persistent daemons"
    )
    print(f"Generated: {topic_result['name']}")
    print(f"Path: {topic_result['path']}")
    
    # List auto skills
    print("\nAuto-generated skills:")
    skills = list_auto_skills()
    for s in skills:
        print(f"  {s['name']} (v{s['version']}, {s['size']} bytes)")
    
    print("\n=== Skill Generator Ready ===")
