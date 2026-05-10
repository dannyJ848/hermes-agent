#!/usr/bin/env python3
"""
distillation_quality_gate.py — Quality gate for distillation pipeline.

Validates tips before they enter the training corpus:
- Operational check: tip must be actionable (contains verbs, conditions)
- Grounding check: tip must cite evidence or have 3+ successful applications
- Novelty check: tip must not duplicate existing tips (MD5 + semantic)
- Cross-domain check: tip must map to at least 2 domains

Tips failing any gate go to error_registry for revision.
Tips passing all gates get Elo 1200 and enter training corpus.

Usage:
    from distillation_quality_gate import DistillationQualityGate
    gate = DistillationQualityGate()
    result = gate.validate_tip(tip_text, evidence_sources=[])
    # result: {'passed': True, 'score': 0.85, 'elo': 1200}

Wiring:
    - Call from post_tool_call hook after tip extraction
    - Or batch validate from WARM tier before sending to COLD
"""

import re
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

HERMES_HOME = Path.home() / ".hermes"
QUALITY_DB = HERMES_HOME / "distillation_quality.db"
CEREBRUM_DB = HERMES_HOME / "cerebrum_memory.db"

class DistillationQualityGate:
    """Four-gate quality validation for distilled tips."""
    
    # Operational verbs that indicate actionable tips
    ACTION_VERBS = [
        'use', 'check', 'verify', 'run', 'try', 'ensure', 'avoid',
        'prefer', 'when', 'if', 'do', 'call', 'set', 'enable', 'disable',
        'install', 'configure', 'deploy', 'test', 'validate', 'monitor'
    ]
    
    # Condition markers
    CONDITION_MARKERS = ['when', 'if', 'before', 'after', 'during', 'unless']
    
    def __init__(self):
        self._ensure_db()
    
    def _ensure_db(self):
        QUALITY_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(QUALITY_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tip_text TEXT,
                    tip_hash TEXT UNIQUE,
                    operational_score REAL,
                    grounding_score REAL,
                    novelty_score REAL,
                    cross_domain_score REAL,
                    overall_score REAL,
                    passed BOOLEAN,
                    rejection_reason TEXT,
                    evidence_count INTEGER,
                    domain_count INTEGER,
                    created_at REAL
                )
            """)
    
    def _hash_tip(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def check_operational(self, tip_text: str) -> Tuple[float, str]:
        """
        Gate 1: Operational — tip must contain actionable guidance.
        Score: 0-1 based on presence of verbs, conditions, specificity.
        """
        text_lower = tip_text.lower()
        
        # Check for action verbs
        verb_count = sum(1 for v in self.ACTION_VERBS if v in text_lower)
        
        # Check for condition markers (WHEN/IF)
        has_condition = any(m in text_lower for m in self.CONDITION_MARKERS)
        
        # Check specificity (length + concrete details)
        word_count = len(tip_text.split())
        is_specific = word_count >= 10
        
        # Check for anti-patterns
        anti_patterns = [
            "always", "never", "must", "should"  # Too absolute without context
        ]
        has_anti_pattern = any(p in text_lower for p in anti_patterns)
        
        # Calculate score
        score = 0.0
        if verb_count >= 2:
            score += 0.3
        if has_condition:
            score += 0.3
        if is_specific:
            score += 0.2
        if word_count >= 15:
            score += 0.2
        if has_anti_pattern:
            score -= 0.2
        
        score = max(0.0, min(1.0, score))
        
        reason = ""
        if score < 0.5:
            missing = []
            if verb_count < 2:
                missing.append("action verbs")
            if not has_condition:
                missing.append("condition (WHEN/IF)")
            if not is_specific:
                missing.append("specificity")
            reason = f"Missing: {', '.join(missing)}"
        
        return score, reason
    
    def check_grounding(self, tip_text: str, evidence_sources: List[str] = None) -> Tuple[float, str]:
        """
        Gate 2: Grounding — tip must have evidence or 3+ successful applications.
        Score: 0-1 based on evidence quality.
        """
        evidence_count = len(evidence_sources or [])
        
        # Check for self-evidence in text (citations, references)
        has_citation = bool(re.search(r'\[.*?\]|\(.*?\d{4}.*?\)', tip_text))
        has_reference = any(w in tip_text.lower() for w in ['source', 'from', 'via', 'using'])
        
        # Score based on evidence
        score = 0.0
        if evidence_count >= 3:
            score += 0.5
        elif evidence_count >= 1:
            score += 0.3
        
        if has_citation:
            score += 0.2
        if has_reference:
            score += 0.1
        
        # Bonus for explicit success markers
        success_markers = ['worked', 'successful', 'fixed', 'resolved', 'verified']
        success_count = sum(1 for m in success_markers if m in tip_text.lower())
        score += min(0.2, success_count * 0.05)
        
        score = max(0.0, min(1.0, score))
        
        reason = ""
        if score < 0.5:
            reason = f"Insufficient evidence ({evidence_count} sources, need 3+ or citations)"
        
        return score, reason
    
    def check_novelty(self, tip_text: str) -> Tuple[float, str]:
        """
        Gate 3: Novelty — tip must not duplicate existing tips.
        Score: 0-1 based on uniqueness.
        """
        tip_hash = self._hash_tip(tip_text)
        
        # Check against quality DB
        with sqlite3.connect(str(QUALITY_DB)) as conn:
            existing = conn.execute(
                "SELECT COUNT(*) FROM quality_checks WHERE tip_hash = ?",
                (tip_hash,)
            ).fetchone()[0]
            
            if existing > 0:
                return 0.0, "Exact duplicate (MD5 match)"
            
            # Check semantic similarity (simple word overlap)
            words = set(tip_text.lower().split())
            if len(words) > 5:
                cur = conn.execute("SELECT tip_text FROM quality_checks WHERE overall_score >= 0.7")
                for row in cur.fetchall():
                    existing_words = set(row[0].lower().split())
                    if existing_words:
                        overlap = len(words & existing_words) / max(len(words), len(existing_words))
                        if overlap > 0.85:
                            return 0.1, f"Near-duplicate ({overlap:.0%} word overlap)"
        
        return 1.0, "Novel tip"
    
    def check_cross_domain(self, tip_text: str) -> Tuple[float, str]:
        """
        Gate 4: Cross-domain — tip must apply to at least 2 domains.
        Score: 0-1 based on domain breadth.
        """
        text_lower = tip_text.lower()
        
        # Domain indicators
        domains = {
            'code': ['python', 'javascript', 'typescript', 'rust', 'code', 'function', 'class'],
            'devops': ['docker', 'kubernetes', 'deploy', 'ci/cd', 'pipeline', 'server'],
            'ml': ['model', 'training', 'inference', 'dataset', 'gpu', 'tensor'],
            'data': ['sql', 'database', 'query', 'table', 'index', 'postgres'],
            'web': ['api', 'http', 'endpoint', 'request', 'response', 'json'],
            'security': ['auth', 'encrypt', 'token', 'secret', 'permission', 'audit'],
            'infra': ['ssh', 'server', 'cpu', 'memory', 'disk', 'network'],
        }
        
        matched_domains = []
        for domain, keywords in domains.items():
            if any(kw in text_lower for kw in keywords):
                matched_domains.append(domain)
        
        score = min(1.0, len(matched_domains) / 2.0)  # 2+ domains = full score
        
        reason = ""
        if len(matched_domains) < 2:
            reason = f"Only 1 domain matched ({', '.join(matched_domains)}), need 2+"
        
        return score, reason
    
    def validate_tip(self, tip_text: str, evidence_sources: List[str] = None,
                     session_id: str = "") -> Dict:
        """
        Run all four gates. Returns validation result.
        """
        tip_hash = self._hash_tip(tip_text)
        now = datetime.now().timestamp()
        
        # Run gates
        op_score, op_reason = self.check_operational(tip_text)
        gr_score, gr_reason = self.check_grounding(tip_text, evidence_sources)
        nv_score, nv_reason = self.check_novelty(tip_text)
        cd_score, cd_reason = self.check_cross_domain(tip_text)
        
        # Overall score (weighted)
        overall = (
            op_score * 0.35 +
            gr_score * 0.25 +
            nv_score * 0.25 +
            cd_score * 0.15
        )
        
        # Pass threshold: all gates >= 0.5, overall >= 0.7
        passed = (
            op_score >= 0.5 and
            gr_score >= 0.5 and
            nv_score >= 0.5 and
            cd_score >= 0.5 and
            overall >= 0.7
        )
        
        # Collect rejection reasons
        reasons = []
        if op_score < 0.5:
            reasons.append(f"Operational: {op_reason}")
        if gr_score < 0.5:
            reasons.append(f"Grounding: {gr_reason}")
        if nv_score < 0.5:
            reasons.append(f"Novelty: {nv_reason}")
        if cd_score < 0.5:
            reasons.append(f"Cross-domain: {cd_reason}")
        
        rejection_reason = "; ".join(reasons) if reasons else ""
        
        # Record
        with sqlite3.connect(str(QUALITY_DB)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO quality_checks
                (tip_text, tip_hash, operational_score, grounding_score, novelty_score,
                 cross_domain_score, overall_score, passed, rejection_reason,
                 evidence_count, domain_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tip_text[:1000], tip_hash, op_score, gr_score, nv_score, cd_score,
                overall, passed, rejection_reason,
                len(evidence_sources or []), len([r for r in reasons if r]), now
            ))
            conn.commit()
        
        return {
            "passed": passed,
            "overall_score": round(overall, 2),
            "operational": round(op_score, 2),
            "grounding": round(gr_score, 2),
            "novelty": round(nv_score, 2),
            "cross_domain": round(cd_score, 2),
            "elo": 1200 if passed else 800,
            "rejection_reason": rejection_reason,
            "tip_hash": tip_hash
        }
    
    def get_stats(self) -> Dict:
        with sqlite3.connect(str(QUALITY_DB)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM quality_checks").fetchone()[0]
            passed = conn.execute("SELECT COUNT(*) FROM quality_checks WHERE passed = 1").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM quality_checks WHERE passed = 0").fetchone()[0]
            avg_score = conn.execute("SELECT AVG(overall_score) FROM quality_checks").fetchone()[0] or 0
            
            return {
                "total_checked": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
                "avg_score": round(avg_score, 2),
                "db_path": str(QUALITY_DB)
            }


# Post-tool-call hook for tip validation
def post_tool_call_tip_validation(tool_name: str, result: str, **kwargs):
    """
    Hook to validate extracted tips after tool calls.
    Only runs when result contains potential tips.
    """
    # Check if result looks like a tip extraction
    if len(result) > 100 and any(w in result.lower() for w in ['when', 'if', 'use', 'check']):
        gate = DistillationQualityGate()
        validation = gate.validate_tip(
            tip_text=result[:500],
            evidence_sources=[tool_name]
        )
        
        if validation["passed"]:
            # Tip is good — could auto-store to WARM tier
            pass
        else:
            # Tip failed — log to error registry
            pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Distillation Quality Gate")
    parser.add_argument("--validate", type=str, help="Validate a tip text")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    gate = DistillationQualityGate()
    
    if args.validate:
        result = gate.validate_tip(args.validate)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(gate.get_stats(), indent=2))