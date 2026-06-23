#!/usr/bin/env python3
"""Background Check — Smart Status & Summary for Background Processes.

When a background build/test/install finishes, the notification says "process
finished" but not whether it passed or failed. This tool checks a background
process and returns a structured summary: exit code, pass/fail determination
based on common output patterns, last N lines of relevant output, and key
metrics (test counts, build duration, errors found).

Eliminates the wasted turn of reading full output just to determine outcome.

Uses the existing process_registry singleton — no duplicate infrastructure.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)


# Pass/fail pattern matching for common build/test/install outputs
_PASS_PATTERNS = [
    (r"\b(\d+) passed\b", "tests_passed"),
    (r"\bBUILD SUCCESSFUL\b", "build_success"),
    (r"\bAll tests passed\b", "tests_passed"),
    (r"\b✓.*(\d+)\b.*passing\b", "tests_passed"),
    (r"\bSuccessfully installed\b", "install_success"),
    (r"\bcompilation finished\b", "compile_success"),
    (r"\b✅\b", "success_marker"),
    (r"\bPASSED\b", "tests_passed"),
    (r"\bDone\s*[.\s]", "task_done"),
]

_FAIL_PATTERNS = [
    (r"\b(\d+) failed\b", "tests_failed"),
    (r"\bBUILD FAILED\b", "build_failed"),
    (r"\bFAILED\b", "tests_failed"),
    (r"\bERROR[:\s]", "error"),
    (r"\bError[:\s]", "error"),
    (r"\bTraceback\b", "traceback"),
    (r"\bFAILED \[", "tests_failed"),
    (r"\b❌\b", "fail_marker"),
    (r"\bAssertionError\b", "assertion_error"),
    (r"\bFAILED TO\b", "build_failed"),
    (r"\bFATAL\b", "fatal"),
    (r"\bpanic\b", "panic"),
    (r"\bcore dumped\b", "crash"),
    (r"\berror TS\d+", "typescript_error"),
    (r"\bModule not found\b", "module_not_found"),
    (r"\bcannot find module\b", "module_not_found"),
    (r"\bImportError\b", "import_error"),
    (r"\bPermission denied\b", "permission_denied"),
    (r"\bNo such file or directory\b", "file_not_found"),
    (r"\bcommand not found\b", "command_not_found"),
    (r"\bconnection refused\b", "connection_refused"),
    (r"\bTimeoutError\b", "timeout"),
]

_WARN_PATTERNS = [
    (r"\b(\d+) warnings?\b", "warnings"),
    (r"\bWARNING[:\s]", "warning"),
    (r"\bWarning[:\s]", "warning"),
    (r"\b⚠️\b", "warning_marker"),
    (r"\bDeprecationWarning\b", "deprecation"),
]


def _analyze_output(output: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
    """Analyze process output for pass/fail signals."""
    analysis = {
        "determination": "unknown",
        "confidence": 0,
        "signals": [],
        "metrics": {},
    }

    output_lower = output.lower()

    # Check pass patterns
    pass_signals = []
    for pattern, signal_type in _PASS_PATTERNS:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            pass_signals.append(signal_type)
            # Extract numeric metrics
            for m in re.finditer(pattern, output, re.IGNORECASE):
                if m.groups() and m.group(1).isdigit():
                    analysis["metrics"][signal_type] = int(m.group(1))

    # Check fail patterns
    fail_signals = []
    for pattern, signal_type in _FAIL_PATTERNS:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            fail_signals.append(signal_type)
            if signal_type == "tests_failed":
                for m in re.finditer(pattern, output, re.IGNORECASE):
                    if m.groups() and m.group(1).isdigit():
                        analysis["metrics"]["tests_failed_count"] = int(m.group(1))

    # Check warning patterns
    warn_signals = []
    for pattern, signal_type in _WARN_PATTERNS:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            warn_signals.append(signal_type)

    analysis["signals"] = {
        "pass": list(dict.fromkeys(pass_signals)),
        "fail": list(dict.fromkeys(fail_signals)),
        "warn": list(dict.fromkeys(warn_signals)),
    }

    # Determine outcome
    if exit_code is not None and exit_code == 0 and not fail_signals:
        analysis["determination"] = "passed"
        analysis["confidence"] = 95
    elif exit_code is not None and exit_code != 0:
        analysis["determination"] = "failed"
        analysis["confidence"] = 90
    elif fail_signals and not pass_signals:
        analysis["determination"] = "failed"
        analysis["confidence"] = 80
    elif pass_signals and not fail_signals:
        analysis["determination"] = "passed"
        analysis["confidence"] = 80
    elif fail_signals and pass_signals:
        analysis["determination"] = "partial"
        analysis["confidence"] = 70
    elif warn_signals:
        analysis["determination"] = "passed_with_warnings"
        analysis["confidence"] = 60

    return analysis


def _extract_key_lines(output: str, max_lines: int = 20) -> List[str]:
    """Extract the most informative lines from output."""
    lines = output.splitlines()
    key_lines = []

    # Priority patterns
    important_patterns = [
        r"error|Error|ERROR",
        r"failed|FAILED|Failed",
        r"passed|PASSED|Passed",
        r"Traceback",
        r"Exception",
        r"BUILD",
        r"SUCCESS|FAILURE",
        r"✅|❌|⚠️|🔴|🟢",
        r"\d+ (tests?|passed|failed|errors?|warnings?)",
        r"summary|Summary|SUMMARY",
        r"result|Result|RESULT",
    ]

    important_re = re.compile("|".join(f"({p})" for p in important_patterns), re.IGNORECASE)

    # First pass: lines matching important patterns
    for line in lines:
        if important_re.search(line) and len(key_lines) < max_lines:
            key_lines.append(line.strip())

    # If not enough key lines, take last N lines
    if len(key_lines) < 5:
        remaining = max_lines - len(key_lines)
        tail = [l.strip() for l in lines[-remaining:] if l.strip()]
        key_lines.extend(tail)

    return key_lines[:max_lines]


def _get_process_registry():
    """Lazy import of process_registry singleton."""
    try:
        from tools.process_registry import process_registry
        return process_registry
    except ImportError:
        return None


def background_check_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle background_check tool calls."""
    action = args.get("action", "check")
    pr = _get_process_registry()

    if pr is None:
        return tool_error("Process registry not available")

    if action == "check":
        """Check a specific process and summarize its status."""
        proc_id = args.get("id", "")
        if not proc_id:
            return tool_error("'id' is required for 'check' action (use 'list' to find process IDs)")

        # Poll the process
        poll_result = pr.poll(proc_id)
        if poll_result.get("status") == "not_found":
            return tool_error(f"Process '{proc_id}' not found")

        # Read full output for analysis
        log_result = pr.read_log(proc_id, limit=500)
        output = log_result.get("output", "")
        total_lines = log_result.get("total_lines", 0)

        # Analyze
        exit_code = poll_result.get("exit_code")
        analysis = _analyze_output(output, exit_code)
        key_lines = _extract_key_lines(output, max_lines=args.get("lines", 20))

        is_running = poll_result["status"] == "running"

        return json.dumps({
            "status": "success",
            "process_id": proc_id,
            "command": poll_result.get("command", ""),
            "running": is_running,
            "exited": not is_running,
            "exit_code": exit_code,
            "uptime_seconds": poll_result.get("uptime_seconds", 0),
            "determination": analysis["determination"] if not is_running else "running",
            "confidence": analysis["confidence"],
            "metrics": analysis["metrics"],
            "signals": analysis["signals"],
            "key_lines": key_lines,
            "total_output_lines": total_lines,
        }, ensure_ascii=False)

    elif action == "list":
        """List all tracked background processes with quick status."""
        sessions = pr.list_sessions()
        if not sessions:
            return json.dumps({"status": "success", "processes": [], "message": "No background processes tracked"}, ensure_ascii=False)

        summaries = []
        for proc_id in sessions:
            try:
                poll_result = pr.poll(proc_id)
                exit_code = poll_result.get("exit_code")
                is_running = poll_result.get("status") == "running"

                # Quick analysis of last output
                log_result = pr.read_log(proc_id, limit=50)
                output = log_result.get("output", "")
                analysis = _analyze_output(output, exit_code) if not is_running else {"determination": "running", "confidence": 0}

                summaries.append({
                    "id": proc_id,
                    "command": poll_result.get("command", "")[:80],
                    "running": is_running,
                    "exit_code": exit_code,
                    "uptime_seconds": poll_result.get("uptime_seconds", 0),
                    "determination": analysis.get("determination", "unknown"),
                })
            except Exception as e:
                summaries.append({"id": proc_id, "error": str(e)[:100]})

        return json.dumps({"status": "success", "count": len(summaries), "processes": summaries}, ensure_ascii=False)

    elif action == "wait_check":
        """Wait for a process to finish, then return summary."""
        proc_id = args.get("id", "")
        timeout = args.get("timeout", 300)
        if not proc_id:
            return tool_error("'id' is required for 'wait_check' action")

        # Wait
        wait_result = pr.wait(proc_id, timeout=timeout)
        if wait_result.get("status") == "not_found":
            return tool_error(f"Process '{proc_id}' not found")
        if wait_result.get("status") == "timeout":
            return json.dumps({
                "status": "timeout",
                "process_id": proc_id,
                "message": f"Process still running after {timeout}s",
            }, ensure_ascii=False)

        # Now analyze
        exit_code = wait_result.get("exit_code")
        log_result = pr.read_log(proc_id, limit=500)
        output = log_result.get("output", "")
        analysis = _analyze_output(output, exit_code)
        key_lines = _extract_key_lines(output, max_lines=args.get("lines", 20))

        return json.dumps({
            "status": "success",
            "process_id": proc_id,
            "command": wait_result.get("command", ""),
            "exited": True,
            "exit_code": exit_code,
            "duration_seconds": wait_result.get("uptime_seconds", 0),
            "completion_reason": wait_result.get("completion_reason", ""),
            "determination": analysis["determination"],
            "confidence": analysis["confidence"],
            "metrics": analysis["metrics"],
            "signals": analysis["signals"],
            "key_lines": key_lines,
            "total_output_lines": log_result.get("total_lines", 0),
        }, ensure_ascii=False)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: check, list, wait_check")


BACKGROUND_CHECK_SCHEMA = {
    "name": "background_check",
    "description": (
        "Smart status checker for background processes. Instead of reading full output "
        "to determine if a build/test/install passed or failed, this tool analyzes the "
        "output automatically and returns: pass/fail determination, confidence score, "
        "extracted metrics (test counts, errors), and only the key lines of output. "
        "Actions: check (analyze a specific process), list (all processes with quick status), "
        "wait_check (block until done, then summarize). "
        "Call after a background task notification to get the outcome in one call."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["check", "list", "wait_check"],
                "description": (
                    "check: analyze a specific process's status and output. "
                    "list: show all background processes with quick pass/fail. "
                    "wait_check: block until process finishes, then return summary."
                ),
            },
            "id": {
                "type": "string",
                "description": "Process session ID (from terminal background=true output).",
            },
            "timeout": {
                "type": "integer",
                "description": "Max seconds to wait for 'wait_check' (default 300).",
            },
            "lines": {
                "type": "integer",
                "description": "Max key lines to extract from output (default 20).",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="background_check",
    toolset="terminal",
    schema=BACKGROUND_CHECK_SCHEMA,
    handler=background_check_handler,
    emoji="📊",
    max_result_size_chars=30_000,
)
