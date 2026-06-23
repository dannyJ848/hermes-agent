#!/usr/bin/env python3
"""Parallel Terminal — Concurrent Execution of Independent Commands.

When multiple independent commands need to run (e.g., check two machines,
build and test in parallel, fetch from multiple endpoints), serial execution
wastes wall-clock time. This tool runs commands concurrently using threads
and collects results.

Usage:
  parallel_terminal(action="run", commands=[
    {"label": "check_macbook", "command": "ssh macbook 'uname -a'"},
    {"label": "check_dgx", "command": "ssh dgx 'nvidia-smi --query-gpu=name,memory.used --format=csv,noheader'"},
    {"label": "disk_usage", "command": "df -h /"},
  ])

Returns each command's output, exit code, and duration.
Max concurrency: 5 threads. Max timeout per command: 300s (configurable).
"""

import json
import logging
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

_MAX_CONCURRENT = 5
_DEFAULT_TIMEOUT = 120


def _run_single_command(
    command: str,
    timeout: int = _DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
    shell: bool = True,
) -> Dict[str, Any]:
    """Run a single command and return structured result."""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        duration = round(time.monotonic() - start, 2)
        return {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[:10000],  # Cap output
            "stderr": proc.stderr[:5000],
            "duration_seconds": duration,
            "success": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        duration = round(time.monotonic() - start, 2)
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "duration_seconds": duration,
            "success": False,
            "timed_out": True,
        }
    except Exception as e:
        duration = round(time.monotonic() - start, 2)
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)[:500],
            "duration_seconds": duration,
            "success": False,
        }


def parallel_terminal_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle parallel_terminal tool calls."""
    action = args.get("action", "run")

    if action == "run":
        commands = args.get("commands", [])
        if not commands or not isinstance(commands, list):
            return tool_error("'commands' must be a non-empty array")

        # Parse command specs
        specs = []
        for i, cmd_spec in enumerate(commands):
            if isinstance(cmd_spec, str):
                specs.append({
                    "label": f"cmd_{i}",
                    "command": cmd_spec,
                    "timeout": args.get("timeout", _DEFAULT_TIMEOUT),
                    "cwd": args.get("cwd"),
                })
            elif isinstance(cmd_spec, dict):
                specs.append({
                    "label": cmd_spec.get("label", f"cmd_{i}"),
                    "command": cmd_spec.get("command", ""),
                    "timeout": cmd_spec.get("timeout", args.get("timeout", _DEFAULT_TIMEOUT)),
                    "cwd": cmd_spec.get("cwd", args.get("cwd")),
                })
            else:
                return tool_error(f"Command spec at index {i} must be a string or object")

        # Validate commands
        for spec in specs:
            if not spec["command"]:
                return tool_error(f"Empty command in spec '{spec['label']}'")

        # Cap concurrency
        concurrency = min(len(specs), _MAX_CONCURRENT)

        start = time.monotonic()
        results = {}

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_label = {}
            for spec in specs:
                future = executor.submit(
                    _run_single_command,
                    command=spec["command"],
                    timeout=spec["timeout"],
                    cwd=spec.get("cwd"),
                )
                future_to_label[future] = spec["label"]

            for future in as_completed(future_to_label):
                label = future_to_label[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = {
                        "command": "",
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": str(e)[:500],
                        "success": False,
                    }
                result["label"] = label
                results[label] = result

        total_duration = round(time.monotonic() - start, 2)
        total_serial_est = sum(r.get("duration_seconds", 0) for r in results.values())

        # Order results by original spec order
        ordered = [results.get(spec["label"], {"label": spec["label"], "error": "missing"}) for spec in specs]

        return json.dumps({
            "status": "success",
            "total_duration": total_duration,
            "serial_estimate": round(total_serial_est, 2),
            "speedup": round(total_serial_est / total_duration, 1) if total_duration > 0 else 0,
            "concurrency": concurrency,
            "results": ordered,
        }, ensure_ascii=False)

    elif action == "batch":
        """Run the same command on multiple hosts (SSH batch)."""
        command = args.get("command", "")
        hosts = args.get("hosts", [])
        ssh_key = args.get("ssh_key")
        timeout = args.get("timeout", _DEFAULT_TIMEOUT)

        if not command:
            return tool_error("'command' is required for 'batch' action")
        if not hosts:
            return tool_error("'hosts' array is required for 'batch' action")

        # Build SSH commands for each host
        specs = []
        for host in hosts:
            ssh_cmd = f"ssh"
            if ssh_key:
                ssh_cmd += f" -i {ssh_key}"
            ssh_cmd += f" -o ConnectTimeout=10 -o StrictHostKeyChecking=no {host} '{command}'"
            specs.append({"label": host, "command": ssh_cmd, "timeout": timeout})

        # Delegate to run logic
        args["commands"] = specs
        return parallel_terminal_handler(args, session_id=session_id, **kwargs)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: run, batch")


PARALLEL_TERMINAL_SCHEMA = {
    "name": "parallel_terminal",
    "description": (
        "Run multiple independent shell commands concurrently for faster multi-check operations. "
        "Takes an array of commands (each with optional label, timeout, cwd) and runs them "
        "in parallel threads (max 5). Returns each command's stdout, stderr, exit code, and "
        "duration, plus overall speedup vs serial execution. "
        "Also supports 'batch' mode: run the same command across multiple SSH hosts at once. "
        "Use when you need to check multiple things simultaneously (disk on 3 machines, "
        "build + lint + test, fetch from multiple endpoints)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["run", "batch"],
                "description": "run: execute an array of different commands. batch: run the same command across multiple SSH hosts.",
            },
            "commands": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "command": {"type": "string"},
                                "timeout": {"type": "integer", "description": "Max seconds (default 120)"},
                                "cwd": {"type": "string"},
                            },
                        },
                    ]
                },
                "description": "Array of commands for 'run' action. Each item is a string or an object with label/command/timeout/cwd.",
            },
            "command": {
                "type": "string",
                "description": "Single command for 'batch' action (run on each host).",
            },
            "hosts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "SSH host aliases for 'batch' action (e.g., ['macbook', 'dgx', 'user@1.2.3.4']).",
            },
            "ssh_key": {
                "type": "string",
                "description": "Path to SSH key file for 'batch' action.",
            },
            "timeout": {
                "type": "integer",
                "description": "Default timeout per command in seconds (default 120).",
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for commands (default: current).",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="parallel_terminal",
    toolset="terminal",
    schema=PARALLEL_TERMINAL_SCHEMA,
    handler=parallel_terminal_handler,
    emoji="⚡",
    max_result_size_chars=50_000,
)
