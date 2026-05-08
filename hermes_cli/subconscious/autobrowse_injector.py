#!/usr/bin/env python3
"""
Autobrowse Live Tip Injector — Direct integration for real-time tip feedback.

Usage:
    python3 /tmp/autobrowse_injector.py --tool terminal --result "some result text"
    
Or import and call:
    from autobrowse_injector import get_tips_for_last_calls
    tips = get_tips_for_last_calls(n=5)
"""

import sys
import os
import json
import argparse

# Add paths
sys.path.insert(0, "/Users/dannygomez/hermes-agent/hermes_cli")

from subconscious.autobrowse_tracer import AutobrowseTracer
from subconscious.autobrowse_analyzer import AutobrowseAnalyzer
from subconscious.autobrowse_synthesizer import AutobrowseSynthesizer
from subconscious.autobrowse_graduator import AutobrowseGraduator

# Singleton instances (persist across calls in same process)
_tracer = None
_analyzer = None
_synthesizer = None
_graduator = None

def _get_modules():
    global _tracer, _analyzer, _synthesizer, _graduator
    if _tracer is None:
        _tracer = AutobrowseTracer()
        _analyzer = AutobrowseAnalyzer()
        _synthesizer = AutobrowseSynthesizer()
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
    """
    Analyze last N tool calls and return actionable tips.
    
    Args:
        n: Number of recent traces to analyze
        min_tips: Minimum tips to return (even if patterns are weak)
    
    Returns:
        List of dicts: [{"text": "tip text", "confidence": 0.8, "source": "pattern_type"}]
    """
    tracer, analyzer, synthesizer, graduator = _get_modules()
    
    # 1. Get traces
    traces = tracer.get_recent_traces(n)
    if len(traces) < 2:
        return []  # Need at least 2 traces for pattern detection
    
    # 2. Analyze
    patterns = analyzer.analyze_traces(traces)
    
    # 3. Synthesize tips
    tips = synthesizer.generate_tips(patterns)
    
    # 4. Score and filter
    scored_tips = []
    for tip in tips:
        score = tip.get("confidence", 0.5)
        if score >= 0.6:  # Quality threshold
            scored_tips.append({
                "text": tip.get("text", ""),
                "confidence": score,
                "source": tip.get("source", "autobrowse"),
                "tool": tip.get("tool", "any"),
            })
    
    # 5. If no tips but we have traces, generate a generic one
    if len(scored_tips) < min_tips and len(traces) >= 3:
        # Convert dataclass to dict for uniform access
        trace_dicts = []
        for t in traces:
            if hasattr(t, '__dict__'):
                trace_dicts.append(t.__dict__)
            elif isinstance(t, dict):
                trace_dicts.append(t)
            else:
                trace_dicts.append({"tool": str(t), "success": True})
        
        # Check for failures
        failures = [t for t in trace_dicts if not t.get("success", True)]
        if len(failures) >= 2:
            scored_tips.append({
                "text": f"Tool '{failures[0].get('tool_name', '?')}' failed {len(failures)} times recently. Consider alternative approach.",
                "confidence": 0.7,
                "source": "failure_pattern",
                "tool": failures[0].get('tool_name', '?'),
            })
        
        # Check for repetition
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
    
    return scored_tips[:3]  # Max 3 tips

def format_tips_for_prompt(tips):
    """Format tips for injection into system prompt."""
    if not tips:
        return ""
    
    lines = ["\n[AUTOBROWSE TIPS — Based on recent tool usage:]"]
    for i, tip in enumerate(tips, 1):
        conf_str = "✓" if tip["confidence"] >= 0.8 else "~"
        lines.append(f"  {conf_str} {tip['text']}")
    lines.append("[END TIPS]\n")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Autobrowse live tip injector")
    parser.add_argument("--tool", help="Tool name that was just called")
    parser.add_argument("--args", help="JSON string of args")
    parser.add_argument("--result", help="Result string")
    parser.add_argument("--success", type=int, default=1, help="1=success, 0=failure")
    parser.add_argument("--duration", type=int, default=0, help="Duration in ms")
    parser.add_argument("--get-tips", action="store_true", help="Get tips for recent calls")
    parser.add_argument("--n", type=int, default=10, help="Number of recent calls to analyze")
    
    args = parser.parse_args()
    
    if args.get_tips:
        tips = get_tips_for_last_calls(n=args.n)
        print(format_tips_for_prompt(tips))
        return
    
    if args.tool:
        tool_args = json.loads(args.args) if args.args else {}
        record_tool_call(
            args.tool,
            tool_args,
            args.result or "",
            success=bool(args.success),
            duration_ms=args.duration
        )
        print(f"Recorded: {args.tool}")
        
        # Also get tips
        tips = get_tips_for_last_calls(n=args.n)
        if tips:
            print(format_tips_for_prompt(tips))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
