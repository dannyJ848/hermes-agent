#!/usr/bin/env python3
"""
R44 — Skill Internalizer — Skill0-inspired progressive skill weaning.
Key insight (arXiv 2604.02268): Skills at training, zero at inference.
Linear decay of skill budget across stages. Helpfulness-driven curriculum filters
skills by delta = acc_w/skill - acc_w/o/skill. Only keep skills where delta > 0.
"""
import threading, time
from typing import Dict, List, Optional, Tuple
_INSTANCES, _LOCK = {}, threading.Lock()

class SkillInternalizer:
    def __init__(self, session_id="default", max_stages=3):
        self.session_id = session_id
        self._skills: Dict[str, dict] = {}  # skill_name -> {helpful_count, total_count, delta}
        self._current_stage = 1
        self._max_stages = max_stages
        self._skill_budget = 10
        self._stage_transitions = 0
    
    def register_skill(self, name: str, category: str = "general") -> None:
        self._skills[name] = {"category": category, "delta": 0.0,
                              "uses_with": 0, "uses_without": 0,
                              "success_with": 0, "success_without": 0}
    
    def record_skill_use(self, skill_name: str, success: bool, was_provided: bool) -> None:
        if skill_name not in self._skills:
            self.register_skill(skill_name)
        s = self._skills[skill_name]
        if was_provided:
            s["uses_with"] += 1
            if success: s["success_with"] += 1
        else:
            s["uses_without"] += 1
            if success: s["success_without"] += 1
        # Compute delta
        acc_with = s["success_with"] / max(1, s["uses_with"])
        acc_without = s["success_without"] / max(1, s["uses_without"])
        s["delta"] = acc_with - acc_without
    
    def get_active_skills(self) -> List[str]:
        """Filter by delta > 0, rank by delta, return top budget."""
        helpful = [(name, s) for name, s in self._skills.items() if s["delta"] > 0]
        helpful.sort(key=lambda x: x[1]["delta"], reverse=True)
        budget = self._get_budget()
        return [name for name, _ in helpful[:budget]]
    
    def _get_budget(self) -> int:
        """Linear decay: M^(s) = ceil(N * (N_s - s) / (N_s - 1))"""
        n = len(self._skills)
        if self._max_stages <= 1:
            return n
        return max(0, int(n * (self._max_stages - self._current_stage) / (self._max_stages - 1)))
    
    def advance_stage(self) -> bool:
        if self._current_stage < self._max_stages:
            self._current_stage += 1
            self._stage_transitions += 1
            return True
        return False
    
    def should_advance(self, recent_success_rate: float) -> bool:
        """Advance when success rate is high enough with current skills."""
        return recent_success_rate >= 0.7 and self._current_stage < self._max_stages
    
    def get_stats(self):
        return {"total_skills": len(self._skills), "current_stage": self._current_stage,
                "budget": self._get_budget(), "active": len(self.get_active_skills()),
                "stage_transitions": self._stage_transitions}
    
    def build_injection(self, context="") -> Optional[str]:
        active = self.get_active_skills()
        if not active:
            return None
        return f"[SKILL-STAGE] Stage {self._current_stage}/{self._max_stages}. Active skills: {len(active)}. Budget: {self._get_budget()}"

def get_instance(session_id="default"):
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = SkillInternalizer(session_id)
        return _INSTANCES[session_id]

if __name__ == "__main__":
    si = SkillInternalizer("test", max_stages=3)
    si.register_skill("web_search"); si.register_skill("terminal_script")
    si.record_skill_use("web_search", True, True)
    si.record_skill_use("web_search", False, False)  # delta > 0
    print(f"Active: {si.get_active_skills()}, Budget: {si._get_budget()}")
    print(f"Injection: {si.build_injection()}")
    si.advance_stage()
    print(f"After advance: stage={si._current_stage}, budget={si._get_budget()}")
    print("✓ OK")
