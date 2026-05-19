#!/usr/bin/env python3
"""
Autobrowse Live Tip Injector
============================
Direct real-time integration of autobrowse R191 pipeline for CLI sessions.
Records tool calls, analyzes patterns, generates actionable tips.

Usage:
    python3 autobrowse_injector.py --tool terminal --args '{"command":"ls"}' \
        --result "files" --success 1 --duration 100

    python3 autobrowse_injector.py --get-tips --n 10
"""

import sys
import os
import json
import time
import hashlib
from pathlib import Path

# Ensure hermes_cli is on path
HERMES_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(HERMES_ROOT / "hermes_cli") not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT / "hermes_cli"))

from subconscious.autobrowse_tracer import AutobrowseTracer
from subconscious.autobrowse_analyzer import AutobrowseAnalyzer
from subconscious.autobrowse_synthesizer import AutobrowseSynthesizer
from subconscious.autobrowse_graduator import AutobrowseGraduator

STATE_FILE = "/tmp/autobrowse_state.json"

_tracer = None
_analyzer = None
_synthesizer = None
_graduator = None

def _get_modules():
    global _tracer, _analyzer, _synthesizer, _graduator
    if _tracer is None:
        _tracer = AutobrowseTracer(session_id="cli_injector")
    if _analyzer is None:
        _analyzer = AutobrowseAnalyzer()
    if _synthesizer is None:
        _synthesizer = AutobrowseSynthesizer()
    if _graduator is None:
        _graduator = AutobrowseGraduator()
    return _tracer, _analyzer, _synthesizer, _graduator

def record_tool_call(tool_name, args, result, success=True, duration_ms=0):
    """Record a tool call for analysis. Call this after EVERY tool call."""
    tracer, _, _, _ = _get_modules()
    status = "success" if success else "error"
    error_type = None
    error_message = None
    if not success:
        error_type = "execution_error"
        error_message = str(result)[:500] if isinstance(result, str) else "Unknown error"
    tracer.record_call(
        tool_name=tool_name,
        model_used="cli",
        input_data=args,
        output_data=result,
        execution_time_ms=duration_ms,
        status=status,
        error_type=error_type,
        error_message=error_message,
    )

def get_tips_for_last_calls(n=10, min_tips=1):
    """Get actionable tips from the last N tool calls."""
    tracer, analyzer, synthesizer, graduator = _get_modules()
    traces = tracer.get_recent_traces(n)
    if not traces:
        return []
    
    patterns = analyzer.analyze_traces(traces)
    tips = synthesizer.generate_tips(patterns)
    
    scored_tips = []
    for tip in tips:
        if tip.get("confidence", 0) >= 0.6:
            scored_tips.append(tip)
    
    if len(scored_tips) < min_tips and len(traces) >= 3:
        trace_dicts = []
        for t in traces:
            if hasattr(t, '__dict__'):
                trace_dicts.append(t.__dict__)
            elif isinstance(t, dict):
                trace_dicts.append(t)
            else:
                trace_dicts.append({"tool": str(t), "success": True})
        
        failures = [t for t in trace_dicts if not t.get("success", True)]
        if len(failures) >= 2:
            scored_tips.append({
                "text": f"Tool '{failures[0].get('tool_name', '?')}' failed {len(failures)} times recently. Consider alternative approach.",
                "confidence": 0.7,
                "source": "failure_pattern",
                "tool": failures[0].get('tool_name', '?'),
            })
        
        tool_counts = {}
        for t in trace_dicts:
            tool_counts[t.get('tool_name', '?')] = tool_counts.get(t.get('tool_name', '?'), 0) + 1
        most_common = max(tool_counts.items(), key=lambda x: x[1])
        if most_common[1] >= 3:
            scored_tips.append({
                "text": f"Using '{most_common[0]}' {most_common[1]} times in last {n} calls. Verify this is necessary.",
                "confidence": 0.6,
                "source": "repetition_pattern",
                "tool": most_common[0],
            })
    
    return scored_tips

def format_tips_for_prompt(tips):
    """Format tips for injection into agent reasoning."""
    if not tips:
        return ""
    lines = ["[AUTOBROWSE TIPS]"]
    for tip in tips[:3]:
        lines.append(f"  • {tip['text']} (conf: {tip['confidence']})")
    return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", help="Tool name")
    parser.add_argument("--args", help="Tool args (JSON)")
    parser.add_argument("--result", help="Tool result")
    parser.add_argument("--success", type=int, default=1)
    parser.add_argument("--duration", type=int, default=0)
    parser.add_argument("--get-tips", action="store_true")
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()
    
    if args.get_tips:
        tips = get_tips_for_last_calls(n=args.n)
        print(format_tips_for_prompt(tips))
    elif args.tool:
        tool_args = json.loads(args.args) if args.args else {}
        record_tool_call(args.tool, tool_args, args.result, bool(args.success), args.duration)
        print(f"Recorded: {args.tool}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
