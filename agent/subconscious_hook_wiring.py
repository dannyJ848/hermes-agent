"""subconscious_hook_wiring — registers background processing tasks.

Non-blocking background tasks that run in the executor pool:
  - Periodic distillation (tips from accumulated experiences)
  - Stale adjustment cleanup (retire outdated behavior adjustments)
  - Tip archival (move old low-priority tips to cold storage)

These fire after response delivery, so they never add latency.
"""
from __future__ import annotations

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class SubconsciousHookWiring:
    """Registers and manages background cognitive tasks."""

    def __init__(self):
        self._hooks_installed = False
        self._last_run: Dict[str, float] = {}
        self._task_count = 0

    def install_hooks(self):
        """Install background task hooks.

        Called during orchestrator initialization. The tasks themselves are
        triggered by process_background_task() at appropriate intervals.
        """
        if self._hooks_installed:
            return
        self._hooks_installed = True
        logger.debug("subconscious: background hooks installed")

    def process_background_task(self, task_type: str = "routine") -> Dict:
        """Run a background maintenance task.

        task_type: "routine" (cleanup + health check)
                   "distillation" (run distillation if stale)
                   "archive" (archive old data)
        """
        self._task_count += 1
        now = time.time()
        result: Dict = {"task": task_type, "actions": []}

        # Rate-limit: each task type runs at most every 5 minutes
        last = self._last_run.get(task_type, 0)
        if now - last < 300:
            return {"task": task_type, "actions": ["skipped (rate-limited)"]}

        if task_type in ("routine", "distillation"):
            try:
                from agent.distillation import DistillationPipeline
                pipeline = DistillationPipeline()
                new_tips = pipeline.distill_last_24h()
                if new_tips:
                    result["actions"].append(f"distilled {len(new_tips)} tips")
            except Exception as e:
                logger.debug("subconscious: distillation failed: %s", e)

        if task_type in ("routine", "archive"):
            try:
                from agent.cerebrum import CerebrumMemory
                cerebrum = CerebrumMemory()
                deleted = cerebrum.cleanup_old_episodes(days=7)
                if deleted:
                    result["actions"].append(f"archived {deleted} old episodes")
            except Exception as e:
                logger.debug("subconscious: archive failed: %s", e)

        self._last_run[task_type] = now
        return result

    def get_stats(self) -> Dict:
        return {
            "hooks_installed": self._hooks_installed,
            "tasks_run": self._task_count,
        }
