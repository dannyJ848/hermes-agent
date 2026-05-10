#!/usr/bin/env python3
"""
cognitive_infrastructure_v2.py — 5 Novel Cognitive Systems for Hermes Agent

1. InjectionGovernorV2    — Log drops + feedback loop for tip prioritization
2. CreditAssigner          — Correlates injected tips to tool outcomes
3. SessionEndExtractor     — Auto-extract lessons when session closes
4. ToolIntelligenceRouter  — Query success rates before tool selection
5. AutoSkillCron           — Monthly autonomous skill generation

All systems integrate with existing cerebrum_memory.db tables.
"""

import sqlite3
import os
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. INJECTION GOVERNOR V2 — Drop logging + feedback loop
# ═══════════════════════════════════════════════════════════════════════════════

class InjectionGovernorV2:
    """Wraps tip injection with comprehensive drop tracking.
    
    Every tip that reaches the governor gets logged:
    - injected=1: made it into the context
    - injected=0, drop_reason='budget': exceeded char/line limit
    - injected=0, drop_reason='priority': lower priority than others
    - injected=0, drop_reason='duplicate': same as last injection
    
    Feedback loop: tips with high drop rates get confidence penalty.
    tips with high injection+success rates get confidence boost.
    """
    
    def __init__(self, max_chars: int = 2500, max_lines: int = 12, max_tips: int = 8):
        self.max_chars = max_chars
        self.max_lines = max_lines
        self.max_tips = max_tips
        self.session_id = os.environ.get("HERMES_SESSION_ID", "default")
        self.turn_number = 0
        
    def log_attempt(self, tip_id: int, condition: str, priority: int, 
                    injected: bool, drop_reason: str, chars_used: int, lines_used: int):
        """Log a single tip's injection attempt."""
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO tip_injection_attempts 
            (session_id, turn_number, tip_id, tip_condition, priority, 
             injected, drop_reason, chars_used, lines_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.session_id, self.turn_number, tip_id, condition[:200], 
              priority, 1 if injected else 0, drop_reason, chars_used, lines_used))
        conn.commit()
        conn.close()
    
    def apply_feedback(self):
        """Run feedback loop: penalize frequently-dropped tips, boost frequently-injected+successful tips."""
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        # Find tips with >50% drop rate over last 100 attempts
        c.execute("""
            SELECT tip_id, 
                   SUM(CASE WHEN injected=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as inject_rate,
                   COUNT(*) as total
            FROM tip_injection_attempts
            WHERE created_at > strftime('%s', 'now') - 86400 * 7
            GROUP BY tip_id
            HAVING total >= 20 AND inject_rate < 0.5
        """)
        weak_tips = c.fetchall()
        
        for tip_id, rate, total in weak_tips:
            c.execute("UPDATE distilled_tips SET confidence = MAX(0.1, confidence * 0.95) WHERE id=?", (tip_id,))
            print(f"[GOVERNOR] Penalized tip {tip_id}: inject rate {rate*100:.0f}% over {total} attempts")
        
        # Find tips with >80% inject rate AND high success in skill_rewards
        c.execute("""
            SELECT i.tip_id, COUNT(*) as inject_count
            FROM tip_injection_attempts i
            JOIN skill_rewards s ON i.tip_id = s.tip_id
            WHERE i.injected=1 AND s.outcome='success'
            AND i.created_at > strftime('%s', 'now') - 86400 * 7
            GROUP BY i.tip_id
            HAVING inject_count >= 10
        """)
        strong_tips = c.fetchall()
        
        for tip_id, count in strong_tips:
            c.execute("UPDATE distilled_tips SET confidence = MIN(1.0, confidence * 1.05) WHERE id=?", (tip_id,))
            print(f"[GOVERNOR] Boosted tip {tip_id}: {count} successful injections")
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Return injection statistics for dashboard."""
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM tip_injection_attempts WHERE injected=1")
        injected = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tip_injection_attempts WHERE injected=0")
        dropped = c.fetchone()[0]
        c.execute("SELECT drop_reason, COUNT(*) FROM tip_injection_attempts WHERE injected=0 GROUP BY drop_reason")
        drop_reasons = dict(c.fetchall())
        
        conn.close()
        total = injected + dropped
        return {
            "total_attempts": total,
            "injected": injected,
            "dropped": dropped,
            "inject_rate": injected / total if total > 0 else 0,
            "drop_reasons": drop_reasons
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CREDIT ASSIGNER — Tip-to-outcome correlation
# ═══════════════════════════════════════════════════════════════════════════════

class CreditAssigner:
    """Tracks which tips were injected before each tool call, then correlates with outcomes.
    
    Replaces the in-memory `_injected_tips_this_turn` dict with durable storage.
    Enables long-term analysis: which tips actually improve tool success rates?
    """
    
    def __init__(self):
        self.session_id = os.environ.get("HERMES_SESSION_ID", "default")
        self.pending_tips: Dict[str, List[int]] = {}  # tool_name -> [tip_ids]
    
    def record_injection(self, tool_name: str, tip_id: int):
        """Called during pre_llm_call: record which tips are in context for upcoming tool."""
        if tool_name not in self.pending_tips:
            self.pending_tips[tool_name] = []
        self.pending_tips[tool_name].append(tip_id)
    
    def record_outcome(self, tool_name: str, success: bool, error: str = ""):
        """Called during post_tool_call: credit/blame the injected tips."""
        tip_ids = self.pending_tips.get(tool_name, [])
        if not tip_ids:
            return
        
        outcome = "success" if success else f"failure:{error[:50]}"
        reward = 1.0 if success else -0.5
        
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        for tip_id in tip_ids:
            c.execute("""
                INSERT INTO skill_rewards (tip_id, tool_name, outcome, reward, session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (tip_id, tool_name, outcome, reward, self.session_id))
        
        conn.commit()
        conn.close()
        
        # Clear pending for this tool
        self.pending_tips[tool_name] = []
    
    def get_tip_effectiveness(self, tip_id: int) -> Dict:
        """Get success rate for a specific tip."""
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        c.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as successes,
                AVG(reward) as avg_reward
            FROM skill_rewards
            WHERE tip_id=?
        """, (tip_id,))
        total, successes, avg_reward = c.fetchone()
        conn.close()
        
        return {
            "total_applications": total or 0,
            "successes": successes or 0,
            "success_rate": (successes / total * 100) if total else 0,
            "avg_reward": avg_reward or 0
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SESSION-END RAPID EXTRACTOR — Auto-extract lessons on session close
# ═══════════════════════════════════════════════════════════════════════════════

class SessionEndExtractor:
    """When a session ends, automatically extract lessons from the session history.
    
    Uses heuristics (no LLM call — fast):
    - Count tool calls by tool, identify failures
    - Check for repeated error patterns
    - Identify novel tool combinations that worked
    - Flag tools with 0% success in session
    """
    
    def __init__(self):
        self.session_id = os.environ.get("HERMES_SESSION_ID", "default")
    
    def extract(self, tool_calls: List[Dict]) -> List[Dict]:
        """Extract lessons from a session's tool call history.
        
        tool_calls: list of {tool_name, success, error, duration_ms}
        """
        lessons = []
        
        # 1. Tool failure patterns
        tool_stats = {}
        for call in tool_calls:
            tn = call["tool_name"]
            if tn not in tool_stats:
                tool_stats[tn] = {"total": 0, "success": 0, "errors": []}
            tool_stats[tn]["total"] += 1
            if call["success"]:
                tool_stats[tn]["success"] += 1
            else:
                tool_stats[tn]["errors"].append(call.get("error", "")[:50])
        
        for tool, stats in tool_stats.items():
            rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            if stats["total"] >= 3 and rate < 0.5:
                lessons.append({
                    "lesson": f"Tool {tool} had {rate*100:.0f}% success ({stats['success']}/{stats['total']}) this session. Consider alternatives.",
                    "category": "tool_failure",
                    "source": "session_end_extractor"
                })
        
        # 2. Repeated errors
        from collections import Counter
        all_errors = []
        for stats in tool_stats.values():
            all_errors.extend(stats["errors"])
        error_counts = Counter(all_errors)
        for error, count in error_counts.most_common(3):
            if count >= 2 and error:
                lessons.append({
                    "lesson": f"Repeated error '{error}' occurred {count} times. Add to error_patterns_predictive.",
                    "category": "repeated_error",
                    "source": "session_end_extractor"
                })
        
        # 3. Novel successful combos
        # (Would need full call sequence — simplified here)
        
        return lessons
    
    def save_lessons(self, lessons: List[Dict]):
        """Save extracted lessons to rapid_learnings and session_rapid_extractions."""
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        for lesson in lessons:
            # Save to session_rapid_extractions
            c.execute("""
                INSERT INTO session_rapid_extractions (session_id, lesson, category, source)
                VALUES (?, ?, ?, ?)
            """, (self.session_id, lesson["lesson"], lesson["category"], lesson["source"]))
            
            # Also save to rapid_learnings (if not duplicate)
            c.execute("""
                INSERT OR IGNORE INTO rapid_learnings (lesson, category, source, created_at)
                VALUES (?, ?, ?, strftime('%s', 'now'))
            """, (lesson["lesson"], lesson["category"], lesson["source"]))
        
        conn.commit()
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TOOL INTELLIGENCE ROUTER — Query success rates before selection
# ═══════════════════════════════════════════════════════════════════════════════

class ToolIntelligenceRouter:
    """Before executing a tool, check its historical performance and route accordingly.
    
    Integrates with tool_intelligence.db to provide real-time routing decisions.
    Logs all decisions to tool_routing_decisions for later analysis.
    """
    
    def __init__(self):
        self.tool_db = os.path.expanduser("~/.hermes/tool_intelligence.db")
        self.session_id = os.environ.get("HERMES_SESSION_ID", "default")
    
    def get_tool_rate(self, tool_name: str) -> float:
        """Get historical success rate for a tool."""
        conn = sqlite3.connect(self.tool_db)
        c = conn.cursor()
        c.execute("""
            SELECT success_rate FROM tool_performance_summary WHERE tool_name=?
        """, (tool_name,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0.5
    
    def recommend(self, tool_name: str, context: str = "") -> Dict:
        """Get routing recommendation for a tool call.
        
        Returns: {
            "proceed": bool,
            "confidence": float,
            "alternatives": [str],
            "warning": str
        }
        """
        rate = self.get_tool_rate(tool_name)
        
        recommendation = {
            "proceed": True,
            "confidence": rate,
            "alternatives": [],
            "warning": ""
        }
        
        if rate < 0.3:
            recommendation["proceed"] = False
            recommendation["warning"] = f"{tool_name} has {rate*100:.0f}% historical success. Strongly consider alternatives."
            # Suggest alternatives with higher rates
            conn = sqlite3.connect(self.tool_db)
            c = conn.cursor()
            c.execute("""
                SELECT tool_name, success_rate FROM tool_performance_summary
                WHERE success_rate > 0.8 ORDER BY success_rate DESC LIMIT 3
            """)
            alts = c.fetchall()
            conn.close()
            recommendation["alternatives"] = [a[0] for a in alts]
        elif rate < 0.6:
            recommendation["warning"] = f"{tool_name} has {rate*100:.0f}% success. Use with caution."
        
        return recommendation
    
    def log_decision(self, tool_name: str, decision: str, actual_outcome: str):
        """Log the routing decision and actual outcome for analysis."""
        rate = self.get_tool_rate(tool_name)
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO tool_routing_decisions (tool_name, historical_rate, decision, actual_outcome, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (tool_name, rate, decision, actual_outcome, self.session_id))
        conn.commit()
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. AUTO-SKILL CRON — Monthly autonomous skill generation
# ═══════════════════════════════════════════════════════════════════════════════

class AutoSkillCron:
    """Monthly scan of knowledge docs, auto-generate SKILL.md for top candidates.
    
    Scoring criteria:
    - Size: >5000 chars (substantial content)
    - Completeness: has sections, code examples, tables
    - Recency: <90 days old
    - Uniqueness: not already a skill
    """
    
    def __init__(self):
        self.knowledge_dir = Path.home() / ".hermes" / "knowledge"
        self.skills_dir = Path.home() / ".hermes" / "skills"
    
    def score_doc(self, doc_path: Path) -> float:
        """Score a knowledge doc for skill-worthiness."""
        if not doc_path.exists():
            return 0.0
        
        content = doc_path.read_text()
        score = 0.0
        
        # Size score (0-0.3)
        size = len(content)
        score += min(0.3, size / 20000)
        
        # Structure score (0-0.3)
        has_headers = content.count("##") + content.count("###")
        has_code = content.count("```")
        has_tables = content.count("|")
        score += min(0.3, (has_headers * 0.05 + has_code * 0.05 + has_tables * 0.02))
        
        # Recency score (0-0.2)
        mtime = doc_path.stat().st_mtime
        days_old = (time.time() - mtime) / 86400
        score += max(0, 0.2 - days_old / 450)
        
        # Uniqueness score (0-0.2)
        skill_name = doc_path.stem.replace("-", "_").lower()
        existing = list(self.skills_dir.rglob(f"*/{skill_name}*"))
        score += 0.2 if not existing else 0.0
        
        return score
    
    def find_candidates(self, limit: int = 5) -> List[Tuple[Path, float]]:
        """Find top skill candidates from knowledge docs."""
        candidates = []
        for doc in self.knowledge_dir.glob("*.md"):
            score = self.score_doc(doc)
            if score > 0.5:
                candidates.append((doc, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]
    
    def generate_skill(self, doc_path: Path, score: float) -> Optional[Path]:
        """Generate a SKILL.md from a knowledge doc.
        
        Returns path to generated skill, or None if generation fails.
        """
        content = doc_path.read_text()
        skill_name = doc_path.stem.replace("-", "_").lower()[:64]
        
        # Extract title from first line
        title = content.split("\n")[0].replace("#", "").strip() or skill_name
        
        # Build skill directory
        skill_dir = self.skills_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        
        # Generate skill content
        skill_content = f"""---
name: {skill_name}
description: {title}
version: 1.0.0
metadata:
  hermes:
    tags: [auto-generated, knowledge-derived]
    related_skills: []
---

# {title}

Auto-generated skill from knowledge doc: {doc_path.name}
Quality score: {score:.3f}

## Source Content

{content[:8000]}

{"... (truncated)" if len(content) > 8000 else ""}
"""
        
        skill_path.write_text(skill_content)
        return skill_path
    
    def run_monthly(self):
        """Run the monthly skill generation cycle."""
        candidates = self.find_candidates(limit=3)
        generated = []
        
        for doc, score in candidates:
            skill_path = self.generate_skill(doc, score)
            if skill_path:
                generated.append((skill_path, score))
                print(f"[AUTO-SKILL] Generated: {skill_path} (score: {score:.3f})")
        
        return generated


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION — Hook wiring helpers
# ═══════════════════════════════════════════════════════════════════════════════

# Singleton instances
_governor_v2: Optional[InjectionGovernorV2] = None
_credit_assigner: Optional[CreditAssigner] = None
_session_extractor: Optional[SessionEndExtractor] = None
_tool_router: Optional[ToolIntelligenceRouter] = None
_auto_skill: Optional[AutoSkillCron] = None

def get_governor_v2() -> InjectionGovernorV2:
    global _governor_v2
    if _governor_v2 is None:
        _governor_v2 = InjectionGovernorV2()
    return _governor_v2

def get_credit_assigner() -> CreditAssigner:
    global _credit_assigner
    if _credit_assigner is None:
        _credit_assigner = CreditAssigner()
    return _credit_assigner

def get_session_extractor() -> SessionEndExtractor:
    global _session_extractor
    if _session_extractor is None:
        _session_extractor = SessionEndExtractor()
    return _session_extractor

def get_tool_router() -> ToolIntelligenceRouter:
    global _tool_router
    if _tool_router is None:
        _tool_router = ToolIntelligenceRouter()
    return _tool_router

def get_auto_skill() -> AutoSkillCron:
    global _auto_skill
    if _auto_skill is None:
        _auto_skill = AutoSkillCron()
    return _auto_skill


if __name__ == "__main__":
    # Test all 5 systems
    print("=== Cognitive Infrastructure V2 Test ===\n")
    
    # 1. Governor stats
    gov = get_governor_v2()
    stats = gov.get_stats()
    print(f"1. InjectionGovernorV2: {stats}")
    
    # 2. Credit assigner
    ca = get_credit_assigner()
    print(f"2. CreditAssigner: ready (pending_tips: {len(ca.pending_tips)})")
    
    # 3. Session extractor
    se = get_session_extractor()
    test_calls = [
        {"tool_name": "cronjob", "success": False, "error": "id confusion", "duration_ms": 100},
        {"tool_name": "cronjob", "success": False, "error": "id confusion", "duration_ms": 100},
        {"tool_name": "execute_code", "success": True, "error": "", "duration_ms": 200},
    ]
    lessons = se.extract(test_calls)
    print(f"3. SessionEndExtractor: {len(lessons)} lessons from test data")
    for l in lessons:
        print(f"   - {l['lesson'][:60]}...")
    
    # 4. Tool router
    tr = get_tool_router()
    rec = tr.recommend("cronjob")
    print(f"4. ToolIntelligenceRouter: cronjob recommendation: {rec}")
    
    # 5. Auto skill
    asc = get_auto_skill()
    candidates = asc.find_candidates(limit=3)
    print(f"5. AutoSkillCron: {len(candidates)} candidates found")
    for doc, score in candidates:
        print(f"   - {doc.name}: {score:.3f}")
    
    print("\n=== All systems operational ===")
