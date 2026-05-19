#!/usr/bin/env python3
"""
Manual cognitive apparatus audit — fallback when cognitive_systems_audit.py
is missing or when you need a comprehensive health check without dependencies.

Run: python3 ~/.hermes/skills/hermes-apparatus-audit/scripts/manual_audit.py

Produces: health scores, database inventory, hook wiring check, skills audit,
plugin status, external directory scan, and prioritized action list.
"""

import os, glob, sqlite3, json
from pathlib import Path

def run_audit():
    home = os.path.expanduser("~")
    hermes_home = os.path.join(home, ".hermes")
    hermes_agent = os.path.join(home, "hermes-agent")

    results = {"scores": {}, "findings": [], "actions": []}

    # 1. CEREBRUM
    cerebrum_db = os.path.join(hermes_home, "cerebrum_memory.db")
    if os.path.exists(cerebrum_db):
        try:
            conn = sqlite3.connect(cerebrum_db)
            tips = conn.execute("SELECT COUNT(*) FROM distilled_tips").fetchone()[0]
            cols = conn.execute("PRAGMA table_info(distilled_tips)").fetchall()
            col_names = [c[1] for c in cols]
            expected = ['tip_type','condition','recommendation','rationale','tool_name',
                        'domain','confidence','upvotes','downvotes','frequency','source_ids',
                        'created_at','last_seen','last_used']
            missing = [c for c in expected if c not in col_names]
            schema_ok = len(missing) == 0 and len(col_names) >= 15
            results["scores"]["cerebrum"] = 95 if schema_ok and tips > 1000 else 70 if tips > 0 else 0
            results["findings"].append(("PASS" if schema_ok else "FAIL", "Cerebrum",
                f"{tips} tips, schema {'OK' if schema_ok else 'BAD: ' + str(missing)}"))
            conn.close()
        except Exception as e:
            results["scores"]["cerebrum"] = 0
            results["findings"].append(("FAIL", "Cerebrum", str(e)))
    else:
        results["scores"]["cerebrum"] = 0
        results["findings"].append(("FAIL", "Cerebrum", "DB missing"))

    # 2. HOOK WIRING
    run_agent = os.path.join(hermes_agent, "run_agent.py")
    if os.path.exists(run_agent):
        content = open(run_agent).read()
        hooks_found = {h: content.count(h) for h in [
            'invoke_hook','pre_llm_call','post_llm_call','pre_tool_call',
            'post_tool_call','before_action','after_action'
        ]}
        has_orchestrator = 'cognitive_orchestrator' in content
        score = 85
        if hooks_found['post_tool_call'] == 0:
            score -= 10
            results["findings"].append(("WARN", "Hooks", "post_tool_call missing (asymmetric)"))
        if not has_orchestrator:
            score -= 20
        results["scores"]["hooks"] = score
        results["findings"].append(("PASS", "Hooks",
            f"invoke_hook:{hooks_found['invoke_hook']}, pre_llm_call:{hooks_found['pre_llm_call']}, "
            f"pre_tool_call:{hooks_found['pre_tool_call']}, before_action:{hooks_found['before_action']}, "
            f"orchestrator:{has_orchestrator}"))
    else:
        results["scores"]["hooks"] = 0

    # 3. DATABASES
    dbs = glob.glob(os.path.join(hermes_home, "*.db"))
    healthy = 0
    empty = 0
    corrupted = 0
    for db in dbs:
        try:
            conn = sqlite3.connect(db)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            rows = sum(conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0] for t in tables)
            if rows == 0 and len(tables) > 0:
                empty += 1
            elif rows > 0:
                healthy += 1
            conn.close()
        except:
            corrupted += 1
    total = len(dbs)
    results["scores"]["databases"] = int((healthy / max(total, 1)) * 100)
    results["findings"].append(("INFO", "Databases",
        f"{total} DBs: {healthy} healthy, {empty} empty, {corrupted} corrupted"))

    # 4. SKILLS
    skills_dir = os.path.join(hermes_home, "skills")
    if os.path.exists(skills_dir):
        count = len([d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))])
        results["scores"]["skills"] = min(100, max(50, count))
        results["findings"].append(("PASS", "Skills", f"{count} skills installed"))
    else:
        results["scores"]["skills"] = 0

    # 5. MEMORY FILES
    has_memory_dir = os.path.exists(os.path.join(hermes_home, "memory"))
    has_memory_md = os.path.exists(os.path.join(hermes_home, "MEMORY.md"))
    score = 100 if has_memory_dir and has_memory_md else 50 if has_memory_dir or has_memory_md else 0
    results["scores"]["memory"] = score
    results["findings"].append(("PASS" if score == 100 else "FAIL", "Memory",
        f"memory/: {has_memory_dir}, MEMORY.md: {has_memory_md}"))

    # 6. EXTERNAL DIRS
    standalone = ["subconscious", "atropos", "training_gym", "cortex", "hindsight"]
    existing = [d for d in standalone if os.path.exists(os.path.join(home, d))]
    results["scores"]["external"] = 100 if len(existing) == 0 else max(0, 100 - len(existing) * 20)
    if existing:
        results["findings"].append(("WARN", "External", f"Still exist: {existing}"))

    # 7. GOALS
    goals_file = os.path.join(hermes_home, "GOALS.md")
    if os.path.exists(goals_file):
        content = open(goals_file).read()
        active = content.count("- [ ]")
        completed = content.count("- [x]")
        results["findings"].append(("PASS", "Goals", f"{active} active, {completed} completed"))
    else:
        results["findings"].append(("FAIL", "Goals", "GOALS.md missing"))

    # Summary score
    avg = sum(results["scores"].values()) / max(len(results["scores"]), 1)
    results["overall"] = round(avg, 1)

    # Actions
    if results["scores"].get("memory", 0) < 100:
        results["actions"].append(("P0", "Create MEMORY.md and memory/ directory"))
    if results["scores"].get("cerebrum", 0) < 80:
        results["actions"].append(("P0", "Fix cerebrum schema / restore from backup"))
    if hooks_found.get('post_tool_call', 1) == 0:
        results["actions"].append(("P1", "Add post_tool_call hook to run_agent.py"))
    if empty > 5:
        results["actions"].append(("P2", f"Clean {empty} empty databases"))
    if existing:
        results["actions"].append(("P2", f"Integrate/remove external dirs: {existing}"))

    return results

if __name__ == "__main__":
    r = run_audit()
    print(f"\nOverall Health: {r['overall']}/100")
    print("\nScores:")
    for k, v in sorted(r["scores"].items(), key=lambda x: -x[1]):
        print(f"  {k:15s}: {v}")
    print("\nFindings:")
    for status, comp, detail in r["findings"]:
        print(f"  [{status}] {comp}: {detail}")
    print("\nActions:")
    for p, a in r["actions"]:
        print(f"  {p} {a}")
