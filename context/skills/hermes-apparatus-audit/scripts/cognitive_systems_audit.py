#!/usr/bin/env python3
"""
Cognitive Systems Audit — checks which modules are wired vs orphaned.

Usage:
    python3 cognitive_systems_audit.py

Output:
    WIRED (N):      modules that are imported AND called in run_agent.py
    IMPORT_ONLY (N): modules that are imported but never called
    ORPHANED (N):   modules that are neither imported nor called
"""

import ast
import os
from pathlib import Path

HERMES_ROOT = Path.home() / "hermes-agent"
AGENT_DIR = HERMES_ROOT / "agent"
RUN_AGENT = HERMES_ROOT / "run_agent.py"


def get_agent_modules():
    """Find all Python modules in agent/ directory."""
    modules = {}
    for f in AGENT_DIR.glob("*.py"):
        if f.name.startswith("_"):
            continue
        module_name = f.stem
        try:
            tree = ast.parse(f.read_text())
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            modules[module_name] = {"file": f, "classes": classes, "functions": functions}
        except SyntaxError:
            modules[module_name] = {"file": f, "classes": [], "functions": []}
    return modules


def check_wiring_status():
    """Check which modules are imported/called in run_agent.py."""
    run_agent_text = RUN_AGENT.read_text()
    modules = get_agent_modules()

    for name, info in modules.items():
        import_patterns = [
            f"from agent.{name} import",
            f"import agent.{name}",
            f"from .{name} import",
        ]
        is_imported = any(p in run_agent_text for p in import_patterns)

        is_called = False
        for cls in info["classes"]:
            if f"{cls}(" in run_agent_text or f"{cls}." in run_agent_text:
                is_called = True
                break
        for func in info["functions"]:
            if f"{func}(" in run_agent_text:
                is_called = True
                break

        info["imported"] = is_imported
        info["called"] = is_called
        info["wired"] = is_imported and is_called

    return modules


def print_report(modules):
    """Print audit report."""
    wired = []
    import_only = []
    orphaned = []

    for name, info in sorted(modules.items()):
        if info["wired"]:
            wired.append(name)
        elif info["imported"]:
            import_only.append(name)
        else:
            orphaned.append(name)

    total_size = sum(info["file"].stat().st_size for info in modules.values())
    orphaned_size = sum(modules[name]["file"].stat().st_size for name in orphaned)

    print("=" * 60)
    print("COGNITIVE SYSTEMS AUDIT REPORT")
    print("=" * 60)
    print(f"\nWIRED ({len(wired)}):")
    for name in wired:
        print(f"  ✓ {name}")

    if import_only:
        print(f"\nIMPORT_ONLY ({len(import_only)}):")
        for name in import_only:
            print(f"  ⚠️  {name} (imported but never called)")

    if orphaned:
        print(f"\nORPHANED ({len(orphaned)}):")
        for name in orphaned:
            size = modules[name]["file"].stat().st_size
            print(f"  ✗ {name} ({size:,} bytes)")

    print(f"\n{'=' * 60}")
    print(f"Total modules: {len(modules)}")
    print(f"Wired: {len(wired)} | Import-only: {len(import_only)} | Orphaned: {len(orphaned)}")
    print(f"Orphaned code: {orphaned_size:,} bytes ({orphaned_size/max(total_size,1)*100:.1f}% of agent/)")
    print(f"{'=' * 60}")

    # Return structured data for programmatic use
    return {
        "wired": wired,
        "import_only": import_only,
        "orphaned": orphaned,
        "orphaned_bytes": orphaned_size,
        "total_bytes": total_size,
    }


if __name__ == "__main__":
    modules = check_wiring_status()
    print_report(modules)
