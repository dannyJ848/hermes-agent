#!/usr/bin/env python3
"""Remote Terminal — SSH with Auto-Retry, Reconnection, and Output Buffering.

SSH connections to remote hosts (DGX, VPS, etc.) drop frequently during heavy
operations. Each drop costs a turn to reconnect and retry. This tool wraps SSH
with automatic retry, connection timeout handling, and output buffering so
transient failures are handled transparently.

Features:
- Auto-retry on connection failure (configurable, default 3 attempts)
- Exponential backoff between retries (1s, 2s, 4s)
- ConnectTimeout and ServerAliveInterval to detect dead connections faster
- Output buffering: if the command produces >10KB output, it's truncated with
  a note to use the tail/head for full output
- Exit code propagation
- Optional: save full output to disk for large results

Usage:
  remote_terminal(host="dgx", command="nvidia-smi")
  remote_terminal(host="spark-85e8", command="python3 train.py", retry=5, timeout=600)
"""

import json
import logging
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

_MAX_OUTPUT = 15000  # 15KB cap in result
_DEFAULT_RETRIES = 3
_DEFAULT_TIMEOUT = 120
_CONNECT_TIMEOUT = 15


def _workspace_dir() -> Path:
    d = get_hermes_home() / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _build_ssh_command(
    host: str,
    command: str,
    ssh_key: Optional[str] = None,
    port: Optional[int] = None,
    connect_timeout: int = _CONNECT_TIMEOUT,
    extra_opts: Optional[list] = None,
) -> list:
    """Build a robust SSH command array."""
    parts = [
        "ssh",
        "-o", f"ConnectTimeout={connect_timeout}",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "BatchMode=yes",  # Never prompt for password; fail fast if key auth fails
    ]
    if ssh_key:
        parts.extend(["-i", ssh_key])
    if port:
        parts.extend(["-p", str(port)])
    if extra_opts:
        parts.extend(extra_opts)
    parts.append(host)
    parts.append(command)
    return parts


def _run_ssh_with_retry(
    host: str,
    command: str,
    retries: int = _DEFAULT_RETRIES,
    timeout: int = _DEFAULT_TIMEOUT,
    ssh_key: Optional[str] = None,
    port: Optional[int] = None,
    save_output: bool = False,
    session: Optional[str] = None,
) -> Dict[str, Any]:
    """Run an SSH command with automatic retry on transient failures."""
    ssh_cmd = _build_ssh_command(host, command, ssh_key=ssh_key, port=port)
    attempts = []
    last_error = ""

    for attempt_num in range(1, retries + 1):
        start = time.monotonic()
        try:
            proc = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = round(time.monotonic() - start, 2)
            success = proc.returncode == 0

            # Check for SSH-level errors (connection refused, timeout, etc.)
            ssh_error = ""
            if not success:
                stderr_lower = proc.stderr.lower()
                if any(e in stderr_lower for e in [
                    "connection refused", "connection timed out", "connection reset",
                    "broken pipe", "no route to host", "network is unreachable",
                    "permission denied", "host key verification",
                ]):
                    ssh_error = proc.stderr.strip()[:500]
                    last_error = ssh_error
                    attempts.append({
                        "attempt": attempt_num,
                        "exit_code": proc.returncode,
                        "error": ssh_error,
                        "duration": duration,
                    })
                    if attempt_num < retries:
                        backoff = min(2 ** (attempt_num - 1), 8)  # 1, 2, 4, 8s cap
                        time.sleep(backoff)
                        continue

            # Success or non-retryable failure
            stdout = proc.stdout
            truncated = False
            saved_to = None

            if len(stdout) > _MAX_OUTPUT:
                if save_output and session:
                    # Save full output to disk
                    saved_to = _workspace_dir() / f"remote_output_{session}_{int(time.time())}.txt"
                    saved_to.write_text(stdout, encoding="utf-8")
                    stdout = stdout[:_MAX_OUTPUT] + f"\n\n... [output truncated, full output saved to {saved_to}]"
                    truncated = True
                else:
                    # Keep head and tail
                    head = stdout[:_MAX_OUTPUT // 2]
                    tail = stdout[-_MAX_OUTPUT // 4:]
                    lines_total = stdout.count('\n')
                    stdout = f"{head}\n\n... [{lines_total} lines total, output truncated — use save_output=true for full] ...\n\n{tail}"
                    truncated = True

            return {
                "status": "success" if success else "error",
                "host": host,
                "command": command,
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": proc.stderr[:3000],
                "duration_seconds": duration,
                "attempts": attempt_num,
                "attempt_history": attempts,
                "truncated": truncated,
                "saved_to": str(saved_to) if saved_to else None,
            }

        except subprocess.TimeoutExpired:
            duration = round(time.monotonic() - start, 2)
            last_error = f"Command timed out after {timeout}s"
            attempts.append({
                "attempt": attempt_num,
                "exit_code": -1,
                "error": last_error,
                "duration": duration,
            })
            if attempt_num < retries:
                backoff = min(2 ** (attempt_num - 1), 8)
                time.sleep(backoff)
                continue

        except Exception as e:
            duration = round(time.monotonic() - start, 2)
            last_error = str(e)[:500]
            attempts.append({
                "attempt": attempt_num,
                "exit_code": -1,
                "error": last_error,
                "duration": duration,
            })
            if attempt_num < retries:
                backoff = min(2 ** (attempt_num - 1), 8)
                time.sleep(backoff)
                continue

    # All retries exhausted
    return {
        "status": "failed",
        "host": host,
        "command": command,
        "exit_code": -1,
        "stdout": "",
        "stderr": last_error,
        "duration_seconds": sum(a["duration"] for a in attempts),
        "attempts": len(attempts),
        "attempt_history": attempts,
        "message": f"All {retries} attempts failed. Last error: {last_error}",
    }


def remote_terminal_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle remote_terminal tool calls."""
    action = args.get("action", "run")
    session = (session_id or "default").replace("/", "_")[:128]

    if action == "run":
        host = args.get("host", "")
        command = args.get("command", "")
        if not host:
            return tool_error("'host' is required (e.g., 'dgx', 'user@1.2.3.4', 'spark-85e8')")
        if not command:
            return tool_error("'command' is required")

        result = _run_ssh_with_retry(
            host=host,
            command=command,
            retries=args.get("retry", _DEFAULT_RETRIES),
            timeout=args.get("timeout", _DEFAULT_TIMEOUT),
            ssh_key=args.get("ssh_key"),
            port=args.get("port"),
            save_output=args.get("save_output", False),
            session=session,
        )
        return json.dumps(result, ensure_ascii=False)

    elif action == "test":
        """Quick connectivity test to one or more hosts."""
        hosts = args.get("hosts", [])
        if isinstance(hosts, str):
            hosts = [hosts]
        if not hosts:
            return tool_error("'hosts' is required for 'test' action")

        results = {}
        for host in hosts:
            result = _run_ssh_with_retry(
                host=host,
                command="echo HERMES_OK",
                retries=1,
                timeout=20,
            )
            results[host] = {
                "reachable": result["status"] == "success" and "HERMES_OK" in result.get("stdout", ""),
                "latency_ms": int(result.get("duration_seconds", 0) * 1000),
                "error": result.get("stderr", "")[:200] if result["status"] != "success" else "",
            }
        return json.dumps({"status": "success", "results": results}, ensure_ascii=False)

    elif action == "multi":
        """Run different commands on different hosts in sequence (or parallel)."""
        commands = args.get("commands", [])
        if not commands:
            return tool_error("'commands' array is required for 'multi' action")

        results = []
        for spec in commands:
            host = spec.get("host", "")
            cmd = spec.get("command", "")
            if not host or not cmd:
                results.append({"host": host, "error": "missing host or command"})
                continue
            result = _run_ssh_with_retry(
                host=host,
                command=cmd,
                retries=spec.get("retry", _DEFAULT_RETRIES),
                timeout=spec.get("timeout", _DEFAULT_TIMEOUT),
            )
            results.append({
                "host": host,
                "command": cmd,
                "status": result["status"],
                "exit_code": result["exit_code"],
                "stdout": result["stdout"][:5000],
                "stderr": result["stderr"][:2000],
                "duration_seconds": result["duration_seconds"],
            })
        return json.dumps({"status": "success", "results": results}, ensure_ascii=False)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: run, test, multi")


REMOTE_TERMINAL_SCHEMA = {
    "name": "remote_terminal",
    "description": (
        "SSH command execution with automatic retry, reconnection, and output buffering. "
        "Handles transient SSH failures (connection refused, timeout, broken pipe) transparently "
        "with exponential backoff. Large outputs are truncated (head+tail) or saved to disk. "
        "Actions: run (single command), test (connectivity check), multi (commands on multiple hosts). "
        "Use instead of terminal('ssh host ...') for any remote operation to get automatic resilience."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["run", "test", "multi"],
                "description": "run: execute a command on a remote host. test: connectivity check. multi: different commands on different hosts.",
            },
            "host": {
                "type": "string",
                "description": "SSH host alias or user@ip for 'run' action.",
            },
            "command": {
                "type": "string",
                "description": "Shell command to execute on the remote host.",
            },
            "retry": {
                "type": "integer",
                "description": "Max retry attempts on transient failures (default 3).",
            },
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds (default 120).",
            },
            "ssh_key": {
                "type": "string",
                "description": "Path to SSH private key file.",
            },
            "port": {
                "type": "integer",
                "description": "SSH port (default 22).",
            },
            "save_output": {
                "type": "boolean",
                "description": "Save large outputs to disk instead of truncating (default false).",
            },
            "hosts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Host list for 'test' action.",
            },
            "commands": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "command": {"type": "string"},
                        "timeout": {"type": "integer"},
                        "retry": {"type": "integer"},
                    },
                },
                "description": "Command specs for 'multi' action.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="remote_terminal",
    toolset="terminal",
    schema=REMOTE_TERMINAL_SCHEMA,
    handler=remote_terminal_handler,
    emoji="🔗",
    max_result_size_chars=30_000,
)
