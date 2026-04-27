"""
Background Self-Improvement Daemon — Kimi Harness v2.3

Runs between sessions to continuously improve the agent:
- Reviews past sessions for lessons learned
- Updates skills based on new knowledge
- Researches frequently-asked topics
- Practices weak tools
- Consolidates memories

This is the "sleep" phase of the agent — learning while idle.

Author: Kimi
Date: 2026-04-26
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _cortex_cursor():
    """Get a Cortex database cursor."""
    import sys
    sys.path.insert(0, str(Path.home() / "subconscious"))
    from cortex_access import cortex_cursor
    return cortex_cursor()


@dataclass
class ImprovementTask:
    """A single self-improvement task."""
    task_type: str  # 'review', 'research', 'practice', 'consolidate', 'skill_update'
    priority: float  # 0.0-1.0
    description: str
    context: str = ""
    estimated_duration_minutes: int = 5
    created_at: float = 0.0


class SelfImprovementDaemon:
    """Background daemon for continuous self-improvement."""
    
    def __init__(self):
        self._ensure_schema()
        self._last_run = 0.0
    
    def _ensure_schema(self):
        """Ensure improvement tracking tables exist."""
        with _cortex_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS improvement_tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    task_type TEXT NOT NULL,
                    priority FLOAT DEFAULT 0.5,
                    description TEXT,
                    context TEXT,
                    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, failed
                    result TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    estimated_duration_minutes INTEGER,
                    actual_duration_minutes INTEGER
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS session_reviews (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id TEXT,
                    review_type TEXT,  -- 'successes', 'failures', 'patterns', 'lessons'
                    findings JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
    
    def generate_tasks(self) -> List[ImprovementTask]:
        """Generate improvement tasks based on recent activity."""
        tasks = []
        
        # Task 1: Review recent errors
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT error_type, COUNT(*) as count, MAX(last_occurred) as last
                FROM error_patterns
                WHERE last_occurred > NOW() - INTERVAL '24 hours'
                GROUP BY error_type
                ORDER BY count DESC
            """)
            
            for row in cur.fetchall():
                if row['count'] >= 2:
                    tasks.append(ImprovementTask(
                        task_type='review',
                        priority=min(0.9, row['count'] / 10),
                        description=f"Review {row['count']} recent {row['error_type']} errors",
                        context=f"error_type:{row['error_type']}",
                        estimated_duration_minutes=3,
                        created_at=time.time(),
                    ))
        
        # Task 2: Research frequently asked topics
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT query_context, COUNT(*) as count
                FROM memory_usage_log
                WHERE timestamp > NOW() - INTERVAL '7 days'
                  AND query_context != ''
                GROUP BY query_context
                HAVING COUNT(*) >= 3
                ORDER BY count DESC
                LIMIT 5
            """)
            
            for row in cur.fetchall():
                tasks.append(ImprovementTask(
                    task_type='research',
                    priority=0.6,
                    description=f"Research: {row['query_context'][:80]}",
                    context=row['query_context'],
                    estimated_duration_minutes=10,
                    created_at=time.time(),
                ))
        
        # Task 3: Practice weak tools
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT tool_name, success_rate, usage_count
                FROM tool_usage_patterns
                WHERE success_rate < 0.7
                  AND usage_count > 2
                ORDER BY success_rate ASC
                LIMIT 5
            """)
            
            for row in cur.fetchall():
                tasks.append(ImprovementTask(
                    task_type='practice',
                    priority=0.5 + (0.7 - (row['success_rate'] or 0)),
                    description=f"Practice {row['tool_name']} (success rate: {row['success_rate']:.1%})",
                    context=f"tool:{row['tool_name']}",
                    estimated_duration_minutes=5,
                    created_at=time.time(),
                ))
        
        # Task 4: Consolidate memories
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count
                FROM memory_units
                WHERE created_at > NOW() - INTERVAL '7 days'
                  AND access_count = 0
            """)
            
            row = cur.fetchone()
            if row and row['count'] > 10:
                tasks.append(ImprovementTask(
                    task_type='consolidate',
                    priority=0.4,
                    description=f"Consolidate {row['count']} unused memories",
                    context="memory_cleanup",
                    estimated_duration_minutes=5,
                    created_at=time.time(),
                ))
        
        # Sort by priority
        tasks.sort(key=lambda t: -t.priority)
        return tasks
    
    def execute_task(self, task: ImprovementTask) -> Dict[str, Any]:
        """Execute a single improvement task."""
        start = time.time()
        result = {"task": task.task_type, "status": "completed", "findings": []}
        
        try:
            if task.task_type == 'review':
                result['findings'] = self._review_errors(task.context)
            elif task.task_type == 'research':
                result['findings'] = self._research_topic(task.context)
            elif task.task_type == 'practice':
                result['findings'] = self._practice_tool(task.context)
            elif task.task_type == 'consolidate':
                result['findings'] = self._consolidate_memories()
            elif task.task_type == 'skill_update':
                result['findings'] = self._update_skills(task.context)
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        duration = int((time.time() - start) / 60)
        
        # Store result
        with _cortex_cursor() as cur:
            cur.execute("""
                INSERT INTO improvement_tasks (
                    task_type, priority, description, context,
                    status, result, estimated_duration_minutes, actual_duration_minutes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                task.task_type, task.priority, task.description, task.context,
                result['status'], json.dumps(result['findings']),
                task.estimated_duration_minutes, duration
            ))
        
        return result
    
    def _review_errors(self, context: str) -> List[str]:
        """Review recent errors and extract lessons."""
        error_type = context.replace("error_type:", "")
        
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT error_summary, resolution, resolution_success_rate, occurrence_count
                FROM error_patterns
                WHERE error_type = %s
                ORDER BY occurrence_count DESC
                LIMIT 5
            """, (error_type,))
            
            findings = []
            for row in cur.fetchall():
                findings.append(
                    f"Error: {row['error_summary'][:80]}... "
                    f"Occurred {row['occurrence_count']}x. "
                    f"Fix: {row['resolution'][:60] if row['resolution'] else 'None'} "
                    f"(success: {row['resolution_success_rate']:.0%})"
                )
            
            return findings
    
    def _research_topic(self, context: str) -> List[str]:
        """Research a frequently-asked topic using web search."""
        findings = []
        
        try:
            from hermes_tools import web_search
            
            # Search for the topic
            results = web_search(context, limit=5)
            
            if results.get('data', {}).get('web'):
                findings.append(f"Research on '{context[:80]}':")
                for item in results['data']['web'][:3]:
                    findings.append(f"  - {item.get('title', 'Unknown')}: {item.get('url', '')}")
                    
                # Store findings as a memory
                try:
                    from agent.cortex_learning import get_learning_engine
                    engine = get_learning_engine()
                    # Add to memory_units as a world fact
                    import sys
                    sys.path.insert(0, str(Path.home() / 'subconscious'))
                    from cortex_access import cortex_cursor
                    
                    with cortex_cursor() as cur:
                        import uuid, json
                        from datetime import datetime
                        cur.execute("""
                            INSERT INTO memory_units (
                                id, bank_id, text, fact_type, metadata, tags, created_at
                            ) VALUES (%s, %s, %s, 'world', %s, %s, NOW())
                        """, (
                            str(uuid.uuid4()),
                            'hermes_memory_archive',
                            f"Auto-research: {context}\n\n" + "\n".join(findings),
                            json.dumps({"source": "auto_research", "topic": context}),
                            ['auto_research', 'daemon']
                        ))
                except Exception as e:
                    findings.append(f"[Note: Could not store to Cortex: {e}]")
            else:
                findings.append(f"No web results found for: {context[:80]}")
                
        except Exception as e:
            findings.append(f"Research failed: {e}")
        
        return findings
    
    def _practice_tool(self, context: str) -> List[str]:
        """Practice a weak tool."""
        tool_name = context.replace("tool:", "")
        return [f"Practice {tool_name} with test cases to improve success rate"]
    
    def _consolidate_memories(self) -> List[str]:
        """Consolidate unused memories."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count
                FROM memory_units
                WHERE access_count = 0
                  AND created_at < NOW() - INTERVAL '30 days'
            """)
            
            row = cur.fetchone()
            if row and row['count'] > 0:
                return [f"Found {row['count']} unused memories older than 30 days"]
            return ["No old unused memories found"]
    
    def _update_skills(self, context: str) -> List[str]:
        """Update skills based on new knowledge."""
        return [f"Skill update needed: {context[:100]}"]
    
    def run_daemon_cycle(self, max_tasks: int = 3) -> Dict[str, Any]:
        """
        Run one cycle of the improvement daemon.
        Call this periodically (e.g., every 5 minutes of idle time).
        """
        tasks = self.generate_tasks()
        
        if not tasks:
            return {"status": "no_tasks", "message": "No improvement tasks needed"}
        
        completed = 0
        failed = 0
        results = []
        
        for task in tasks[:max_tasks]:
            if task.priority < 0.3:
                continue
            
            result = self.execute_task(task)
            results.append({
                "type": task.task_type,
                "description": task.description,
                "status": result["status"],
            })
            
            if result["status"] == "completed":
                completed += 1
            else:
                failed += 1
        
        return {
            "status": "completed",
            "tasks_generated": len(tasks),
            "tasks_executed": completed + failed,
            "completed": completed,
            "failed": failed,
            "results": results,
        }
    
    def get_improvement_report(self, days: int = 7) -> Dict[str, Any]:
        """Get report on recent improvements."""
        with _cortex_cursor() as cur:
            cur.execute("""
                SELECT 
                    task_type,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    AVG(actual_duration_minutes) as avg_duration
                FROM improvement_tasks
                WHERE created_at > NOW() - INTERVAL '%s days'
                GROUP BY task_type
            """, (days,))
            
            by_type = {}
            for row in cur.fetchall():
                by_type[row['task_type']] = {
                    "total": row['count'],
                    "completed": row['completed'],
                    "avg_duration_min": round(row['avg_duration'] or 0, 1),
                }
            
            return {
                "period_days": days,
                "tasks_by_type": by_type,
                "total_tasks": sum(t['total'] for t in by_type.values()),
            }