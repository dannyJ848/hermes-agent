#!/usr/bin/env python3
"""
R52: Tip Evolution Engine — mutation, crossover, and selection for tips.

Inspired by OpenAI's evolutionary approach (EvoLLM): high-Elo tips breed,
low-Elo tips die, new variants emerge from crossover of proven strategies.
"""
import os, json, threading, time, re, hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

_INSTANCES: Dict[str, "TipEvolution"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "TipEvolution":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = TipEvolution(session_id)
        return _INSTANCES[session_id]

# Mutation operators
MUTATIONS = {
    "generalize": lambda t: re.sub(r'\bpython\b', 'code', t, flags=re.I),
    "specific": lambda t: t.replace("WHEN", "WHEN (e.g., in debugging)"),
    "compress": lambda t: t[:80] + "..." if len(t) > 120 else t,
    "add_context": lambda t: t.rstrip('.') + " (cortex-validated).",
}


class TipEvolution:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._generations = 0
        self._mutations_applied = 0
        self._crossovers = 0

    def crossover(self, tip_a: str, tip_b: str) -> str:
        """Create child tip from two parent tips."""
        self._crossovers += 1
        # Take condition from A, action from B
        ca = tip_a.split("DO")[0].replace("WHEN", "").strip() if "DO" in tip_a else tip_a[:60]
        ab = tip_b.split("DO")[1].strip() if "DO" in tip_b else tip_b[:60]
        return f"WHEN {ca}, DO {ab}"

    def mutate(self, tip: str, operation: str = "generalize") -> str:
        """Apply a mutation operator to a tip."""
        if operation in MUTATIONS:
            self._mutations_applied += 1
            return MUTATIONS[operation](tip)
        return tip

    def evolve_cycle(self, tips_with_elo: List[Tuple[str, float]]) -> List[str]:
        """One evolution cycle: select top, crossover, mutate."""
        self._generations += 1
        if len(tips_with_elo) < 2:
            return []

        # Sort by elo, take top 5
        sorted_tips = sorted(tips_with_elo, key=lambda x: x[1], reverse=True)
        top = sorted_tips[:5]

        offspring = []
        for i in range(len(top) - 1):
            child = self.crossover(top[i][0], top[i+1][0])
            child = self.mutate(child, "compress")
            offspring.append(child)

        return offspring

    def get_status(self) -> Dict:
        return {
            "session": self.session_id,
            "generations": self._generations,
            "mutations": self._mutations_applied,
            "crossovers": self._crossovers,
        }


if __name__ == "__main__":
    te = TipEvolution("test")
    print("Tip Evolution Engine")
    print("=" * 40)

    tips = [
        ("WHEN debugging code, DO use print statements", 1400),
        ("WHEN writing python, DO add type hints", 1350),
        ("WHEN testing, DO write unit tests first", 1300),
    ]

    offspring = te.evolve_cycle(tips)
    for child in offspring:
        print(f"  Offspring: {child[:80]}")

    print(f"\nStatus: {json.dumps(te.get_status())}")
    print("OK")
