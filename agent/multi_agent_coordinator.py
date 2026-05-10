"""Multi-Agent Coordinator — Collaborative worker dispatch for Hermes Agent.

Integrates with delegate_task to spawn parallel workers that share a blackboard.
Workers can message each other, share tool results, and report findings.

Usage:
    from agent.multi_agent_coordinator import MultiAgentCoordinator
    coord = MultiAgentCoordinator(agent_instance)
    results = coord.dispatch_parallel([
        {"goal": "Research X", "model": "nemotron-free"},
        {"goal": "Research Y", "model": "llama70b-free"},
    ])
"""
import json, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from agent.multi_agent_blackboard import get_blackboard, get_tool_cache

class MultiAgentCoordinator:
    """Coordinates multiple Hermes workers via shared blackboard."""

    def __init__(self, agent_instance, max_workers: int = 3):
        self.agent = agent_instance
        self.max_workers = max_workers
        self.blackboard = get_blackboard()
        self.tool_cache = get_tool_cache()
        self._worker_counter = 0

    def _next_worker_id(self) -> str:
        self._worker_counter += 1
        return f"worker-{self._worker_counter}"

    def dispatch_parallel(self, tasks: List[dict],
                          shared_context: str = "",
                          timeout: int = 300) -> Dict[str, Any]:
        """Dispatch multiple tasks to parallel workers.

        Args:
            tasks: List of {"goal": str, "model": str, "context": str}
            shared_context: Extra context shared with all workers
            timeout: Max seconds per worker

        Returns:
            Dict mapping worker_id -> result dict
        """
        self.blackboard.clear()
        self.tool_cache.clear()

        workers = []
        for task in tasks:
            worker_id = self._next_worker_id()
            workers.append({
                "id": worker_id,
                "goal": task["goal"],
                "model": task.get("model", "nemotron-free"),
                "context": task.get("context", ""),
            })
            self.blackboard.set_status(worker_id, "queued")

        results = {}

        def run_worker(worker: dict) -> dict:
            wid = worker["id"]
            self.blackboard.set_status(wid, "running",
                                       f"Goal: {worker['goal'][:50]}")

            # Build context from blackboard
            bb_context = self.blackboard.get_context_for_worker(wid)
            full_context = f"""{shared_context}

BLACKBOARD CONTEXT:
- Artifacts: {bb_context['artifacts']}
- Findings: {bb_context['findings']}
- Blockers: {bb_context['blockers']}
- Plan updates: {bb_context['plan_updates']}

Your task: {worker['goal']}
{worker['context']}
"""
            try:
                # Use delegate_task for the actual work
                # Note: delegate_task runs synchronously in a subagent
                result = self._delegate_with_blackboard(
                    goal=worker["goal"],
                    model=worker["model"],
                    context=full_context,
                    worker_id=wid,
                )
                self.blackboard.set_status(wid, "done", "Completed successfully")
                self.blackboard.add_finding(wid, f"Completed: {worker['goal'][:80]}")
                return {"worker_id": wid, "status": "success", "result": result}
            except Exception as e:
                self.blackboard.set_status(wid, "failed", str(e)[:200])
                self.blackboard.add_blocker(wid, str(e)[:200], "high")
                return {"worker_id": wid, "status": "failed", "error": str(e)}

        # Run workers in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(run_worker, w): w for w in workers}
            for future in as_completed(futures):
                worker = futures[future]
                try:
                    result = future.result(timeout=timeout)
                    results[worker["id"]] = result
                except Exception as e:
                    results[worker["id"]] = {
                        "worker_id": worker["id"],
                        "status": "timeout",
                        "error": str(e),
                    }

        return {
            "results": results,
            "blackboard_summary": self.blackboard.get_state_summary(),
            "tool_cache_stats": self.tool_cache.stats(),
        }

    def _delegate_with_blackboard(self, goal: str, model: str,
                                   context: str, worker_id: str) -> str:
        """Delegate to a subagent with blackboard integration.

        This is a simplified version — in practice, delegate_task would
        be called directly. The blackboard context is injected into
        the subagent's prompt.
        """
        # For now, return a placeholder — actual integration would
        # call self.agent.delegate_task() or similar
        # The key is that the blackboard state is available
        return f"[Worker {worker_id} result placeholder]"

    def get_collaboration_summary(self) -> str:
        """Get a human-readable summary of the collaboration."""
        state = self.blackboard.get_state_summary()
        lines = [
            "═══ Multi-Agent Collaboration Summary ═══",
            f"Messages: {state['messages_count']}",
            f"Artifacts: {state['artifacts_count']}",
            f"Findings: {state['findings_count']}",
            f"Blockers: {state['blockers_count']}",
            f"Plan updates: {state['plan_updates_count']}",
            "",
            "Worker Status:",
        ]
        for worker, status in state['worker_status'].items():
            lines.append(f"  {worker}: {status['status']} — {status['detail'][:60]}")

        if state['blockers_count'] > 0:
            lines.extend(["", "Active Blockers:"])
            for b in self.blackboard.blockers[-5:]:
                lines.append(f"  [{b['worker']}] {b['blocker'][:80]}")

        return "\n".join(lines)

    def message_worker(self, from_worker: str, to_worker: str,
                       message: str, msg_type: str = "info"):
        """Send a message between workers."""
        self.blackboard.post_message(from_worker, to_worker, message, msg_type)

    def share_artifact(self, worker: str, path: str, description: str):
        """Register an artifact created by a worker."""
        self.blackboard.register_artifact(worker, path, description)

    def report_blocker(self, worker: str, blocker: str, severity: str = "medium"):
        """Report a blocker that needs coordination help."""
        self.blackboard.add_blocker(worker, blocker, severity)

    def update_plan(self, instruction: str, source: str = "coordinator"):
        """Add a plan update for all workers."""
        self.blackboard.add_plan_update(instruction, source)
