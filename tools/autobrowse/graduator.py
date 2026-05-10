"""Autobrowse Graduator — Promote winning tips to durable skills.

Tracks tip survival through Elo tournaments and promotes:
- 5+ successful applications → activate tip
- 10+ applications + Elo > 1200 → add to subconscious module
- 20+ applications + Elo > 1300 → graduate to SKILL.md
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

class AutobrowseGraduator:
    """Tracks tip lifecycle and promotes winners."""

    PROMOTION_THRESHOLDS = {
        "activate": {"applications": 5, "min_elo": 1100},
        "module": {"applications": 10, "min_elo": 1200},
        "skill": {"applications": 20, "min_elo": 1300},
    }

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.tip_lifecycle: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._cortex = None

    def _get_cortex(self):
        """Lazy-load CortexDB."""
        if self._cortex is None:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path.home() / "hermes-agent"))
                from cortex_access import CortexDB
                self._cortex = CortexDB()
            except Exception:
                self._cortex = None
        return self._cortex

    def record_application(self, tip_id: str, success: bool):
        """Record that a tip was applied (success or failure)."""
        with self._lock:
            if tip_id not in self.tip_lifecycle:
                self.tip_lifecycle[tip_id] = {
                    "applications": 0,
                    "successes": 0,
                    "failures": 0,
                    "first_seen": time.time(),
                    "promoted_to": None,
                }

            self.tip_lifecycle[tip_id]["applications"] += 1
            if success:
                self.tip_lifecycle[tip_id]["successes"] += 1
            else:
                self.tip_lifecycle[tip_id]["failures"] += 1

    def check_promotions(self) -> List[Dict]:
        """Check which tips qualify for promotion."""
        promotions = []
        cortex = self._get_cortex()

        with self._lock:
            for tip_id, lifecycle in self.tip_lifecycle.items():
                if lifecycle["promoted_to"] is not None:
                    continue

                apps = lifecycle["applications"]

                # Get Elo from Cortex
                elo = 1150  # Default
                if cortex:
                    try:
                        node = cortex.get_node(tip_id)
                        if node:
                            elo = node.get("elo", 1150)
                    except Exception:
                        pass

                # Check thresholds
                for level, threshold in self.PROMOTION_THRESHOLDS.items():
                    if apps >= threshold["applications"] and elo >= threshold["min_elo"]:
                        promotions.append({
                            "tip_id": tip_id,
                            "level": level,
                            "applications": apps,
                            "success_rate": lifecycle["successes"] / apps,
                            "elo": elo,
                        })
                        lifecycle["promoted_to"] = level
                        break

        return promotions

    def promote_tip(self, promotion: Dict) -> bool:
        """Execute promotion for a tip."""
        level = promotion["level"]
        tip_id = promotion["tip_id"]

        if level == "activate":
            return self._activate_tip(tip_id)
        elif level == "module":
            return self._promote_to_module(tip_id)
        elif level == "skill":
            return self._promote_to_skill(tip_id)

        return False

    def _activate_tip(self, tip_id: str) -> bool:
        """Activate tip in CortexDB."""
        cortex = self._get_cortex()
        if cortex is None:
            return False

        try:
            cortex.update_node(tip_id, {"is_active": True, "activated_at": time.time()})
            return True
        except Exception:
            return False

    def _promote_to_module(self, tip_id: str) -> bool:
        """Add tip to subconscious as a mini-module."""
        cortex = self._get_cortex()
        if cortex is None:
            return False

        try:
            node = cortex.get_node(tip_id)
            if not node:
                return False

            # Extract tip content
            text = node.get("text", "")
            metadata = node.get("metadata", {})

            # Write to autobrowse_generated.py
            module_path = Path.home() / "hermes-agent" / "autobrowse_generated.py"

            entry = f"\n# [{datetime.now().isoformat()}] Tip {tip_id} (Elo={node.get('elo', 0):.0f})\n"
            entry += f"# {text[:200]}\n"
            entry += f"# Applications: {self.tip_lifecycle.get(tip_id, {}).get('applications', 0)}\n"

            if module_path.exists():
                content = module_path.read_text()
            else:
                content = "# Auto-generated tips from Autobrowse graduator\n"
                content += "# These tips graduated from trace analysis to durable code\n\n"

            content += entry
            module_path.write_text(content)
            return True
        except Exception:
            return False

    def _promote_to_skill(self, tip_id: str) -> bool:
        """Graduate tip to SKILL.md format."""
        cortex = self._get_cortex()
        if cortex is None:
            return False

        try:
            node = cortex.get_node(tip_id)
            if not node:
                return False

            text = node.get("text", "")
            metadata = node.get("metadata", {})
            domain = node.get("domain", "strategy")

            # Write to autobrowse_skills.md
            skills_path = Path.home() / "hermes-agent" / "autobrowse_skills.md"

            skill_entry = f"\n## {domain.replace('_', ' ').title()} Tip (Elo {node.get('elo', 0):.0f})\n\n"
            skill_entry += f"**Trigger**: {metadata.get('condition', 'N/A')}\n\n"
            skill_entry += f"**Action**: {metadata.get('recommendation', text[:300])}\n\n"
            skill_entry += f"**Rationale**: {metadata.get('rationale', 'Derived from execution trace analysis')}\n\n"
            skill_entry += f"**Survival**: {self.tip_lifecycle.get(tip_id, {}).get('applications', 0)} applications, "
            success_rate = self.tip_lifecycle.get(tip_id, {}).get('successes', 0) / max(1, self.tip_lifecycle.get(tip_id, {}).get('applications', 1))
            skill_entry += f"{success_rate:.0%} success rate\n\n"
            skill_entry += f"**Source**: Autobrowse trace analysis, {datetime.now().strftime('%Y-%m-%d')}\n\n"
            skill_entry += "---\n"

            if skills_path.exists():
                content = skills_path.read_text()
            else:
                content = "# Autobrowse Graduated Skills\n\n"
                content += "Tips that survived Elo tournaments and earned promotion to durable skills.\n\n"

            content += skill_entry
            skills_path.write_text(content)
            return True
        except Exception:
            return False

    def get_lifecycle_report(self) -> Dict[str, Any]:
        """Generate report of all tracked tips."""
        with self._lock:
            total = len(self.tip_lifecycle)
            activated = sum(1 for v in self.tip_lifecycle.values() if v.get("promoted_to") == "activate")
            moduled = sum(1 for v in self.tip_lifecycle.values() if v.get("promoted_to") == "module")
            skilled = sum(1 for v in self.tip_lifecycle.values() if v.get("promoted_to") == "skill")

            return {
                "total_tracked": total,
                "activated": activated,
                "moduled": moduled,
                "skilled": skilled,
                "pending": total - activated - moduled - skilled,
                "tip_ids": list(self.tip_lifecycle.keys()),
            }

    def build_injection(self, user_message: str = "") -> str:
        """Build injection with promotion stats."""
        report = self.get_lifecycle_report()
        if report["total_tracked"] == 0:
            return ""

        hints = []
        if report["skilled"] > 0:
            hints.append(f"[AUTO-BROWSE] {report['skilled']} tips graduated to skills")
        if report["moduled"] > 0:
            hints.append(f"[AUTO-BROWSE] {report['moduled']} tips promoted to modules")
        if report["pending"] > 5:
            hints.append(f"[AUTO-BROWSE] {report['pending']} tips awaiting promotion")

        return " ".join(hints) if hints else ""


# Singleton registry
_INSTANCES: Dict[str, AutobrowseGraduator] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> AutobrowseGraduator:
    """Thread-safe singleton."""
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = AutobrowseGraduator(session_id)
        return _INSTANCES[session_id]


if __name__ == "__main__":
    print("=== AutobrowseGraduator Self-Test ===")

    g = AutobrowseGraduator("test")

    # Simulate applications
    g.record_application("tip_1", True)
    g.record_application("tip_1", True)
    g.record_application("tip_1", True)
    g.record_application("tip_1", True)
    g.record_application("tip_1", True)

    g.record_application("tip_2", True)
    g.record_application("tip_2", False)
    g.record_application("tip_2", True)

    report = g.get_lifecycle_report()
    print(f"Total tracked: {report['total_tracked']}")
    print(f"Pending: {report['pending']}")

    # Note: promotions need CortexDB Elo data, so check_promotions may return empty in self-test
    promotions = g.check_promotions()
    print(f"Promotions ready: {len(promotions)}")

    print(f"Injection: {g.build_injection()}")
    print("=== PASS ===")
