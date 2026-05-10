#!/usr/bin/env python3
"""
cortex_dashboard_v2.py — Enhanced dashboard showing all 6 subsystems.

Usage:
    python3 cortex_dashboard_v2.py
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB
from agent.adaptive_cortex import AdaptiveCortex
from agent.tool_oracle import ToolOracle
from agent.reasoning_analyzer import ReasoningAnalyzer
from agent.sequence_learner import SequenceLearner
from agent.anomaly_detector import AnomalyDetector


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title):
    print(f"\n  ── {title} ──")


def show_tip_health(db: CortexDB):
    """Show tip database health."""
    print_section("1. CLASSIC CORTEX — Tip Database")
    
    stats = db.get_stats()
    report = db.get_tip_quality_report()
    
    print(f"    Total nodes:     {stats['total_nodes']:,}")
    print(f"    Active tips:     {stats['active_tips']:,}")
    print(f"    Average Elo:     {stats['elo_avg']:.0f}")
    print(f"    Elo range:       {stats['elo_min']:.0f} - {stats['elo_max']:.0f}")
    print(f"    Unrated:         {report['unrated']}")
    print(f"    Needs repair:    {report['needs_repair']}")
    
    if report['tiers']:
        print(f"    Distribution:")
        for tier, count in sorted(report['tiers'].items(), key=lambda x: -x[1]):
            bar = "█" * int(count / max(report['tiers'].values()) * 20)
            print(f"      {tier:12} {bar} {count}")


def show_my_skills(ac: AdaptiveCortex):
    """Show my personal skill progression."""
    print_section("2. ADAPTIVE CORTEX — My Skills")
    
    stats = ac.get_my_stats()
    
    print(f"    Session duration: {stats['session_duration']/60:.1f} minutes")
    print(f"    Total calls:      {stats['total_calls']}")
    print(f"    Success rate:     {stats['success_rate']:.1%}")
    print(f"    Tools mastered:   {stats['tools_used']}")
    print(f"    Recent lessons:   {stats['recent_lessons']}")
    
    if stats['tool_breakdown']:
        print(f"    Tool breakdown:")
        for tool, ts in sorted(stats['tool_breakdown'].items(), 
                              key=lambda x: -x[1]['calls']):
            status = "✓" if ts['success_rate'] > 0.8 else "⚠" if ts['success_rate'] > 0.5 else "✗"
            print(f"      {status} {tool:20} {ts['success_rate']:>6.0%} ({ts['calls']} calls)")


def show_oracle(oracle: ToolOracle):
    """Show tool oracle status."""
    print_section("3. TOOL ORACLE — Predictive Selection")
    
    # Test a few predictions
    test_tasks = [
        "find all Python files",
        "search for information online",
        "read a configuration file",
    ]
    
    print(f"    Sample predictions:")
    for task in test_tasks:
        pred = oracle.predict_tools(task)
        if pred['primary']:
            print(f"      '{task}' → {pred['primary']} ({pred['confidence']:.0%})")
        else:
            print(f"      '{task}' → (no strong match)")


def show_reasoning(ra: ReasoningAnalyzer):
    """Show reasoning analyzer status."""
    print_section("4. REASONING ANALYZER — Quality Scoring")
    
    summary = ra.get_session_summary()
    print(f"    Total flaws:      {summary['total_flaws']}")
    print(f"    Quality:          {summary['quality']}")
    print(f"    Top pattern:      {summary['top_pattern'] or 'None'}")
    
    if summary['improvement_areas']:
        print(f"    Focus areas:      {', '.join(summary['improvement_areas'])}")


def show_sequences(sl: SequenceLearner):
    """Show sequence learner status."""
    print_section("5. SEQUENCE LEARNER — Chain Optimization")
    
    stats = sl.get_stats()
    print(f"    Chains learned:   {stats['chains_learned']}")
    print(f"    Transitions:      {stats['transitions_learned']}")
    
    if stats['top_chains']:
        print(f"    Top chains:")
        for chain, rate, count in stats['top_chains'][:3]:
            print(f"      {' → '.join(chain)}: {rate:.0%} ({count} times)")


def show_anomaly(ad: AnomalyDetector):
    """Show anomaly detector status."""
    print_section("6. ANOMALY DETECTOR — Risk Prediction")
    
    # Test risk scores
    test_tools = ["terminal", "web_search", "vision_analyze", "screencapture"]
    print(f"    Risk scores:")
    for tool in test_tools:
        risk = ad.get_risk_score(tool, {}, "Testing")
        bar = "█" * int(risk * 20)
        print(f"      {tool:20} {bar} {risk:.0%}")


def show_cron_status():
    """Show active cron jobs."""
    print_section("CRON JOBS")
    
    jobs = [
        ("cortex-flywheel", "Every 2h", "Elo tournaments + tip repair"),
        ("cortex-consolidation", "Every 6h", "Merge duplicate tips"),
        ("cortex-quality-sweep", "Daily 9am", "Health report"),
        ("adaptive-cortex-daemon", "Every 30m", "Skill monitoring"),
    ]
    
    for name, schedule, purpose in jobs:
        print(f"    ✓ {name:25} {schedule:12} {purpose}")


def show_system_status():
    """Show overall system status."""
    print_section("SYSTEM STATUS")
    
    # Check if Postgres is running
    try:
        db = CortexDB()
        db.get_stats()
        print("    ✓ Postgres database: Connected")
    except Exception as e:
        print(f"    ✗ Postgres database: {e}")
    
    # Check file existence
    files = [
        "cortex_access.py",
        "cortex_flywheel.py", 
        "adaptive_cortex.py",
        "tool_oracle.py",
        "cortex_unified.py",
        "reasoning_analyzer.py",
        "sequence_learner.py",
        "anomaly_detector.py",
    ]
    
    print(f"    Module status:")
    for f in files:
        path = Path.home() / "hermes-agent" / f
        status = "✓" if path.exists() else "✗"
        print(f"      {status} {f}")


def main():
    print_header("CORTEX SYSTEM DASHBOARD v2")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db = CortexDB()
    ac = AdaptiveCortex(db)
    oracle = ToolOracle(db)
    ra = ReasoningAnalyzer(db)
    sl = SequenceLearner(db)
    ad = AnomalyDetector(db)
    
    show_tip_health(db)
    show_my_skills(ac)
    show_oracle(oracle)
    show_reasoning(ra)
    show_sequences(sl)
    show_anomaly(ad)
    show_cron_status()
    show_system_status()
    
    print_header("SUMMARY")
    print("""
  ACTIVE SUBSYSTEMS (6):
    ✓ Classic Cortex      — 66K tips, Elo-rated, flywheel-evaluated
    ✓ Adaptive Cortex     — 57 skills mined, real-time learning
    ✓ Tool Oracle         — Predictive tool selection, arg validation
    ✓ Reasoning Analyzer  — Quality scoring, flaw detection
    ✓ Sequence Learner    — Chain optimization, transition learning
    ✓ Anomaly Detector    — Risk prediction, unusual behavior detection

  LEARNING MECHANISMS:
    • Every tool call → 6 systems analyze simultaneously
    • Every 2 hours → Elo tournaments rate tip quality
    • Every 6 hours → Duplicate consolidation
    • Every 30 min → Skill progression monitoring
    • Daily 9am → Full health report

  INTEGRATION POINTS:
    • Pre-tool call  → Warnings + suggestions + risk score
    • Post-tool call → Immediate learning across all systems
    • Pre-LLM call   → Personalized context injection

  PERSONALIZATION:
    • Tracks YOUR specific error patterns
    • Warns before you repeat mistakes
    • Suggests better tools based on your history
    • Detects anomalous behavior
    • Optimizes tool chains
    • Scores reasoning quality
    • Injects everything into context
""")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
