"""Autobrowse Synthesizer — Generate tips from waste patterns + maintain strategy.md.

After analysis, generates actionable "WHEN X, DO Y" tips and maintains
a running strategy.md scratchpad that compounds across sessions.
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

class AutobrowseSynthesizer:
    """Generates tips and maintains strategy scratchpad."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.generated_tips: List[Dict] = []
        self._lock = threading.Lock()
        self._cortex = None
        self.strategy_path = Path.home() / "subconscious" / "strategy.md"

    def _get_cortex(self):
        """Lazy-load CortexDB."""
        if self._cortex is None:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path.home() / "subconscious"))
                from cortex_access import CortexDB
                self._cortex = CortexDB()
            except Exception:
                self._cortex = None
        return self._cortex

    def generate_tips(self, patterns: List[Any]) -> List[Dict]:
        """Convert waste patterns into actionable tips."""
        tips = []

        for pattern in patterns:
            tip = self._pattern_to_tip(pattern)
            if tip:
                tips.append(tip)

        with self._lock:
            self.generated_tips.extend(tips)

        # Insert into CortexDB
        self._persist_tips(tips)

        return tips

    def _pattern_to_tip(self, pattern: Any) -> Optional[Dict]:
        """Convert single pattern to tip dict."""
        if pattern.confidence < 0.6:
            return None

        # Build WHEN/DO format
        condition = self._extract_condition(pattern)
        action = self._extract_action(pattern)
        rationale = f"Detected in {len(pattern.affected_traces)} trace(s): {pattern.description[:200]}"

        # Domain mapping
        domain_map = {
            "redundant_loop": "efficiency",
            "suboptimal_model": "cost_optimization",
            "token_waste": "cost_optimization",
            "failure_cluster": "reliability",
            "tool_mismatch": "efficiency",
        }
        domain = domain_map.get(pattern.pattern_type, "strategy")

        # Tool mapping
        tool_map = {
            "redundant_loop": "execute_code",
            "suboptimal_model": "delegate_with_model",
            "token_waste": "web_extract",
            "failure_cluster": "terminal",
            "tool_mismatch": "browser_navigate",
        }
        tool_name = tool_map.get(pattern.pattern_type, "")

        return {
            "tip_type": "strategy",
            "condition": condition,
            "recommendation": action,
            "rationale": rationale,
            "tool_name": tool_name,
            "domain": domain,
            "confidence": pattern.confidence,
            "source": "autobrowse_trace",
            "pattern_type": pattern.pattern_type,
            "severity": pattern.severity,
        }

    def _extract_condition(self, pattern: Any) -> str:
        """Extract WHEN condition from pattern."""
        if pattern.pattern_type == "redundant_loop":
            return f"WHEN about to call the same tool ({pattern.affected_traces[0].split('_')[0]}) with similar input again"
        elif pattern.pattern_type == "suboptimal_model":
            return "WHEN selecting a model for simple information retrieval"
        elif pattern.pattern_type == "token_waste":
            return "WHEN calling search or extract tools"
        elif pattern.pattern_type == "failure_cluster":
            return f"WHEN encountering {pattern.description.split()[0]} errors"
        else:
            return f"WHEN {pattern.pattern_type.replace('_', ' ')}"

    def _extract_action(self, pattern: Any) -> str:
        """Extract DO action from pattern."""
        return pattern.recommendation

    def _persist_tips(self, tips: List[Dict]):
        """Insert tips into CortexDB."""
        cortex = self._get_cortex()
        if cortex is None:
            return

        for tip in tips:
            try:
                text = f"{tip['condition']}, {tip['recommendation']} ({tip['rationale']})"
                cortex.insert_node(
                    text=text,
                    node_type="tip",
                    domain=tip["domain"],
                    confidence=tip["confidence"],
                    metadata={
                        "tip_type": tip["tip_type"],
                        "source": "autobrowse_trace",
                        "pattern_type": tip["pattern_type"],
                        "tool_name": tip["tool_name"],
                        "condition": tip["condition"],
                        "recommendation": tip["recommendation"],
                    }
                )
            except Exception:
                pass

    def update_strategy(self, patterns: List[Any], task_context: str = ""):
        """Update strategy.md with new observations."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        entry = f"\n## [{now}] Session: {self.session_id[:20]}\n\n"
        if task_context:
            entry += f"**Task**: {task_context[:200]}\n\n"

        entry += "### Observations\n\n"
        for p in patterns:
            entry += f"- **{p.pattern_type}** (severity={p.severity:.2f}): {p.description[:150]}\n"
            entry += f"  - *Fix*: {p.recommendation[:200]}\n\n"

        entry += "### What Worked\n\n"
        worked = [p for p in patterns if p.severity < 0.5]
        if worked:
            for p in worked:
                entry += f"- {p.description[:100]}\n"
        else:
            entry += "- No major issues detected in this batch\n"

        entry += "\n### What to Try Next\n\n"
        for p in patterns:
            if p.severity > 0.5:
                entry += f"- [ ] Address {p.pattern_type}: {p.recommendation[:150]}\n"

        # Append to strategy.md
        try:
            if self.strategy_path.exists():
                content = self.strategy_path.read_text()
            else:
                content = "# Autobrowse Strategy Scratchpad\n\n"
                content += "This document captures what the agent learns from its own execution traces.\n"
                content += "Read this before starting new tasks to compound improvements.\n"

            # Keep only last 50 entries to prevent bloat
            lines = content.splitlines()
            if len(lines) > 2000:
                # Find the 10th "## [" header and keep from there
                header_indices = [i for i, l in enumerate(lines) if l.startswith("## [")]
                if len(header_indices) > 10:
                    lines = lines[:100] + lines[header_indices[10]:]
                    content = "\n".join(lines)

            content += entry
            self.strategy_path.write_text(content)
        except Exception:
            pass

    def read_strategy(self) -> str:
        """Read current strategy.md content."""
        try:
            if self.strategy_path.exists():
                return self.strategy_path.read_text()[-5000:]  # Last 5000 chars
            return ""
        except Exception:
            return ""

    def build_injection(self, user_message: str = "") -> str:
        """Build injection from strategy.md learnings."""
        strategy = self.read_strategy()
        if not strategy:
            return ""

        # Extract recent "What to Try Next" items
        hints = []
        lines = strategy.splitlines()
        in_todo = False
        for line in reversed(lines):
            if line.startswith("### What to Try Next"):
                in_todo = True
                continue
            if in_todo:
                if line.startswith("- [ ]"):
                    hints.append(line.replace("- [ ]", "[AUTO-BROWSE STRATEGY]").strip())
                elif line.startswith("## ["):
                    break

        return " ".join(hints[:3]) if hints else ""


# Singleton registry
_INSTANCES: Dict[str, AutobrowseSynthesizer] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> AutobrowseSynthesizer:
    """Thread-safe singleton."""
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = AutobrowseSynthesizer(session_id)
        return _INSTANCES[session_id]


if __name__ == "__main__":
    print("=== AutobrowseSynthesizer Self-Test ===")

    # Mock pattern
    class MockPattern:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    patterns = [
        MockPattern(
            pattern_type="redundant_loop",
            severity=0.8,
            description="web_search called 3x with similar input",
            affected_traces=["t1", "t2", "t3"],
            recommendation="WHEN calling web_search repeatedly, DO cache results",
            confidence=0.85,
            domain="efficiency"
        ),
        MockPattern(
            pattern_type="suboptimal_model",
            severity=0.6,
            description="claude-opus used for web_search",
            affected_traces=["t1"],
            recommendation="WHEN using web_search, DO use glm-5.1",
            confidence=0.9,
            domain="cost_optimization"
        ),
    ]

    s = AutobrowseSynthesizer("test")
    tips = s.generate_tips(patterns)

    print(f"Tips generated: {len(tips)}")
    for t in tips:
        print(f"  - {t['condition'][:60]}...")
        print(f"    {t['recommendation'][:60]}...")

    s.update_strategy(patterns, "Testing autobrowse system")
    strategy = s.read_strategy()
    print(f"Strategy length: {len(strategy)} chars")

    injection = s.build_injection()
    print(f"Injection: {injection[:100]}...")
    print("=== PASS ===")
