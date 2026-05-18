"""
Session State Publisher — auto-commit and push before context compression.

This module provides a lightweight git publisher that stages, commits, and
pushes session-critical files to the remote repo before a session's context
is compressed (and potentially lost). It is designed to be non-blocking and
failure-tolerant: if the network is down or git is in a weird state, the
compression proceeds anyway and the failure is logged.

Usage (inside AIAgent._compress_context, after commit_memory_session):

    from agent.session_publisher import SessionPublisher
    publisher = SessionPublisher(self.session_id, self.model)
    publisher.publish_session_checkpoint(messages, focus_topic)

What gets committed:
- All tracked files that are modified (MEMORY.md, SOUL.md, USER.md, MASTER.md,
  config.yaml, skills/, etc.)
- Untracked files under ~/.hermes/ that match a whitelist (cron/jobs.json,
  skills/, memory/, etc.) — these are auto-added

What is excluded:
- Build artifacts, __pycache__, node_modules, .venv
- Large binary files (>1MB)
- Files matching .gitignore

Conflict strategy: local-wins (force-push not used; we pull --rebase first,
then push. If rebase fails, we stash, pull, apply stash, commit, push).
"""

import fnmatch
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

# Files under ~/.hermes/ that should be auto-tracked if not already
# BE CAREFUL: only include files that are safe to push (no secrets, small size)
_HERMES_AUTO_TRACK = [
    "MEMORY.md",
    "SOUL.md",
    "USER.md",
    "MASTER.md",
    "AGENTS.md",
    "TOOLS.md",
    "goals.md",
    "cron/jobs.json",
    # Memory daily notes (not the full DB)
    "memory/",
    # Only specific skill files — NOT the whole skills/ tree (too large, may contain secrets)
    # Skills are handled separately via _should_copy_skill_file()
]

# File patterns to NEVER copy (secrets, large binaries, caches)
_HERMES_EXCLUDE_PATTERNS = [
    "*.env",
    "*.key",
    "*.pem",
    "*.p12",
    "*.pfx",
    "*token*",
    "*secret*",
    "*password*",
    "*api_key*",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "node_modules/",
    ".git/",
    "*.xsd",  # XML schemas (large, from powerpoint skill)
    "*.wasm",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.bin",
    # Config files with API keys
    "config.yaml",  # Has API keys — skip, we'll handle separately
]

# Max file size for auto-add (bytes)
_MAX_AUTO_ADD_SIZE = 1024 * 1024  # 1 MB


class SessionPublisher:
    """Publishes session state to git before context compression."""

    def __init__(self, session_id: Optional[str], model: str, repo_dir: Optional[Path] = None):
        self.session_id = session_id or "unknown"
        self.model = model
        self.repo_dir = repo_dir or self._find_repo_dir()
        self.hermes_home = get_hermes_home()

    def _find_repo_dir(self) -> Optional[Path]:
        """Find the hermes-agent repo root from the module path."""
        try:
            # This module lives in agent/session_publisher.py, repo root is parent
            return Path(__file__).parent.parent.resolve()
        except Exception:
            return None

    def _git(self, *args: str, check: bool = False, timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a git command in the repo directory."""
        if not self.repo_dir:
            raise RuntimeError("No repo directory configured")
        return subprocess.run(
            ["git", *args],
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout,
        )

    def _has_changes(self) -> bool:
        """Check if there are any staged or unstaged changes."""
        result = self._git("status", "--porcelain", "-uno")
        return bool(result.stdout.strip())

    def _stage_tracked_changes(self) -> List[str]:
        """Stage all modified tracked files and new untracked files in the repo.
        Returns list of staged paths."""
        # Stage all modified tracked files
        self._git("add", "-u", check=False)
        # Stage new untracked files that are part of the repo (not in state/)
        # We use git add -A for the repo root but exclude state/ since those
        # are handled separately via _stage_untracked_hermes_files
        status = self._git("status", "--porcelain", check=False)
        new_files = []
        for line in status.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Status format: XY PATH or XY  "PATH" for renames
            # Untracked files start with ??
            if line.startswith("?? "):
                path = line[3:].strip().strip('"')
                # Skip state/ directory (handled by _stage_untracked_hermes_files)
                # Skip run-history/ (session logs, not state)
                if path.startswith("state/") or path.startswith("run-history/"):
                    continue
                new_files.append(path)
        
        for nf in new_files:
            self._git("add", nf, check=False)
        
        # Get list of all staged files
        result = self._git("diff", "--cached", "--name-only")
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

    def _should_copy_file(self, path: Path) -> bool:
        """Check if a file should be copied based on exclude patterns."""
        name = path.name.lower()
        str_path = str(path).lower()
        
        for pattern in _HERMES_EXCLUDE_PATTERNS:
            if pattern.endswith("/"):
                if pattern.rstrip("/") in str_path.split(os.sep):
                    return False
            elif fnmatch.fnmatch(name, pattern.lower()) or fnmatch.fnmatch(str_path, pattern.lower()):
                return False
        
        # Size check
        try:
            if path.stat().st_size > _MAX_AUTO_ADD_SIZE:
                logger.debug("Skipping large file: %s", path)
                return False
        except OSError:
            return False
        
        return True

    def _sanitize_config_yaml(self, src: Path, dest: Path) -> bool:
        """Copy config.yaml with API keys redacted."""
        try:
            import yaml
            with open(src, 'r') as f:
                config = yaml.safe_load(f)
            
            # Redact known secret fields
            def _redact(obj):
                if isinstance(obj, dict):
                    result = {}
                    for k, v in obj.items():
                        k_lower = k.lower()
                        if any(s in k_lower for s in ('api_key', 'token', 'secret', 'password', 'pat')):
                            result[k] = '***REDACTED***'
                        else:
                            result[k] = _redact(v)
                    return result
                elif isinstance(obj, list):
                    return [_redact(i) for i in obj]
                else:
                    return obj
            
            redacted = _redact(config)
            
            with open(dest, 'w') as f:
                yaml.dump(redacted, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            logger.warning("Failed to sanitize config.yaml: %s", e)
            return False

    def _copy_hermes_file_to_repo(self, hermes_path: Path) -> Optional[Path]:
        """Copy a ~/.hermes file into repo's state/ directory for tracking."""
        if not self.repo_dir or not self.hermes_home:
            return None
        try:
            rel = hermes_path.relative_to(self.hermes_home)
        except ValueError:
            return None

        if not self._should_copy_file(hermes_path):
            return None

        state_dir = self.repo_dir / "state"
        dest = state_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Special handling for config.yaml — sanitize it
        if hermes_path.name == "config.yaml":
            if self._sanitize_config_yaml(hermes_path, dest):
                return dest.relative_to(self.repo_dir)
            return None

        # Normal copy for everything else
        import shutil
        shutil.copy2(str(hermes_path), str(dest))
        return dest.relative_to(self.repo_dir)

    def _stage_untracked_hermes_files(self) -> List[str]:
        """Copy and stage untracked files under ~/.hermes/ that match the whitelist."""
        staged: List[str] = []
        if not self.hermes_home or not self.hermes_home.exists():
            return staged

        for pattern in _HERMES_AUTO_TRACK:
            path = self.hermes_home / pattern
            if not path.exists():
                continue

            # For directories, find files and copy each
            if path.is_dir():
                for file_path in path.rglob("*"):
                    if not file_path.is_file():
                        continue
                    rel = self._copy_hermes_file_to_repo(file_path)
                    if rel:
                        self._git("add", str(rel), check=False)
                        staged.append(str(rel))
            else:
                rel = self._copy_hermes_file_to_repo(path)
                if rel:
                    self._git("add", str(rel), check=False)
                    staged.append(str(rel))

        return staged

    def _build_commit_message(self, messages: List[Dict], focus_topic: Optional[str]) -> str:
        """Build a descriptive commit message from session context."""
        # Extract key info from messages
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

        # Get last user query as summary
        last_query = ""
        if user_msgs:
            last_query = str(user_msgs[-1].get("content", ""))[:80]

        # Count tool calls
        tool_calls = sum(
            1 for m in messages
            if m.get("role") == "assistant" and m.get("tool_calls")
        )

        lines = [
            f"session: auto-checkpoint before compression",
            f"",
            f"session_id: {self.session_id}",
            f"model: {self.model}",
            f"messages: {len(messages)} | user: {len(user_msgs)} | assistant: {len(assistant_msgs)} | tool_calls: {tool_calls}",
        ]

        if focus_topic:
            lines.append(f"focus: {focus_topic}")

        if last_query:
            lines.append(f"last_query: {last_query}")

        lines.append(f"timestamp: {datetime.now().isoformat()}")

        return "\n".join(lines)

    def _sync_remote(self) -> bool:
        """Pull rebase and push. Returns True on success."""
        # Fetch first
        fetch = self._git("fetch", "origin", timeout=15)
        if fetch.returncode != 0:
            logger.warning("SessionPublisher: fetch failed: %s", fetch.stderr.strip())
            # Continue anyway — maybe we can still push

        # Try rebase
        rebase = self._git("pull", "--rebase", "origin", self._current_branch(), timeout=30)
        if rebase.returncode != 0:
            logger.warning("SessionPublisher: rebase failed: %s", rebase.stderr.strip())
            # Stash, pull, apply stash strategy
            self._git("stash", "push", "-m", "session-publisher-auto-stash", check=False)
            self._git("pull", "origin", self._current_branch(), check=False)
            stash_pop = self._git("stash", "pop", check=False)
            if stash_pop.returncode != 0:
                logger.error("SessionPublisher: stash recovery failed: %s", stash_pop.stderr.strip())
                return False

        # Push
        push = self._git("push", "origin", self._current_branch(), timeout=30)
        if push.returncode != 0:
            logger.error("SessionPublisher: push failed: %s", push.stderr.strip())
            return False

        return True

    def _current_branch(self) -> str:
        """Get current git branch."""
        result = self._git("branch", "--show-current")
        return result.stdout.strip() or "main"

    def publish_session_checkpoint(self, messages: List[Dict], focus_topic: Optional[str] = None) -> Dict:
        """
        Main entry point. Stages changes, commits, and pushes.
        Returns a dict with status info. Never raises — failures are logged.
        """
        start_time = time.time()
        result = {
            "success": False,
            "committed": False,
            "pushed": False,
            "files_staged": [],
            "commit_hash": None,
            "error": None,
            "elapsed_ms": 0,
        }

        try:
            if not self.repo_dir or not (self.repo_dir / ".git").exists():
                result["error"] = "Not a git repository"
                return result

            # Stage tracked changes
            tracked = self._stage_tracked_changes()
            # Stage untracked hermes files
            untracked = self._stage_untracked_hermes_files()
            result["files_staged"] = tracked + untracked

            if not result["files_staged"] and not self._has_changes():
                result["success"] = True
                result["error"] = "No changes to commit"
                return result

            # Commit
            msg = self._build_commit_message(messages, focus_topic)
            commit = self._git("commit", "-m", msg, check=False)
            if commit.returncode != 0:
                # Maybe nothing staged? Check status
                if not self._has_changes():
                    result["success"] = True
                    result["error"] = "Nothing to commit after staging"
                    return result
                result["error"] = f"Commit failed: {commit.stderr.strip()}"
                return result

            result["committed"] = True
            result["commit_hash"] = self._git("rev-parse", "HEAD").stdout.strip()

            # Push
            if self._sync_remote():
                result["pushed"] = True
                result["success"] = True
            else:
                result["error"] = "Push failed (commit saved locally)"

        except subprocess.TimeoutExpired as e:
            result["error"] = f"Timeout: {e.cmd}"
        except Exception as e:
            result["error"] = f"Exception: {e}"
            logger.exception("SessionPublisher failed")

        result["elapsed_ms"] = int((time.time() - start_time) * 1000)
        logger.info(
            "SessionPublisher: success=%s committed=%s pushed=%s files=%d elapsed=%dms",
            result["success"], result["committed"], result["pushed"],
            len(result["files_staged"]), result["elapsed_ms"],
        )
        return result


def publish_before_compression(session_id: Optional[str], model: str, messages: List[Dict], focus_topic: Optional[str] = None) -> Dict:
    """Convenience function for one-shot publishing."""
    publisher = SessionPublisher(session_id, model)
    return publisher.publish_session_checkpoint(messages, focus_topic)
