#!/usr/bin/env python3
"""
Bulk cleanup script for removing ~/subconscious/ references from all .hermes config.

Usage: python3 bulk-config-cleanup.py

Scans ~/.hermes/ for all JSON/YAML/Markdown files (excluding historical logs),
replaces path and import references, and reports what was fixed.
"""

import os
from pathlib import Path

REPLACEMENTS = [
    ("/Users/dannygomez/subconscious", "/Users/dannygomez/hermes-agent"),
    ("$HOME/subconscious", "$HOME/hermes-agent"),
    ("~/subconscious", "~/hermes-agent"),
    ("from cortex_access import", "from agent.cortex_access import"),
    ("from llm_judge import", "from agent.llm_judge import"),
    ("from cortex_flywheel import", "from agent.cortex_flywheel import"),
    ("from tip_normalizer import", "from agent.tip_system.normalizer import"),
    ("from autobrowse_tracer import", "from tools.autobrowse.tracer import"),
    ("from autobrowse_analyzer import", "from tools.autobrowse.analyzer import"),
    ("from autobrowse_synthesizer import", "from tools.autobrowse.synthesizer import"),
    ("from autobrowse_graduator import", "from tools.autobrowse.graduator import"),
]

SKIP_PATTERNS = ["session", "output", "checkpoint", "state-snapshots", "claude-bridge"]

def should_skip(path: Path) -> bool:
    s = str(path)
    return any(p in s for p in SKIP_PATTERNS)

def main():
    hermes_data = Path.home() / ".hermes"
    fixed = []
    
    for ext in ("*.json", "*.yaml", "*.yml", "*.md"):
        for f in hermes_data.rglob(ext):
            if should_skip(f):
                continue
            try:
                content = f.read_text()
                if "subconscious" not in content.lower():
                    continue
                for old, new in REPLACEMENTS:
                    content = content.replace(old, new)
                f.write_text(content)
                fixed.append(str(f.relative_to(hermes_data)))
            except Exception as e:
                print(f"ERROR: {f}: {e}")
    
    print(f"Fixed {len(fixed)} files:")
    for p in fixed:
        print(f"  {p}")

if __name__ == "__main__":
    main()
