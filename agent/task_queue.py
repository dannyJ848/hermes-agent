"""
Task Queue with Priority and Delayed Execution.

Features:
1. enqueue with priority and optional delay
2. dequeue by priority then FIFO
3. delayed tasks become available only after delay expires
4. task retry with exponential backoff on failure
5. queue persistence to JSON file for crash recovery
"""

import json
import time
import threading
import heapq
import os
from typing import Callable, Optional, Any


class Task:
    """Represents a task in the queue."""
    
    _counter = 0
    _lock = threading.Lock()
    
    def __init__(self, task_id: Any, priority: int = 0, delay_ms: int = 0,
                 max_retries: int = 0, created_at: Optional[float] = None):
        self.task_id = task_id
        self.priority = priority
        self.max_retries = max_retries  # TOTAL attempts allowed
        self.attempts = 0
        self.dead = False
        self.created_at = created_at or time.time()
        # delay_ms=0 means immediately available
        self.next_available_at = self.created_at + (delay_ms / 1000.0)
        self._seq = self._get_seq()
    
    @classmethod
    def _get_seq(cls):
        with cls._lock:
            cls._counter += 1
            return cls._counter
    
    def to_dict(self):
        return {
            'task_id': self.task_id if not callable(self.task_id) else None,
            'priority': self.priority,
            'max_retries': self.max_retries,
            'attempts': self.attempts,
            'dead': self.dead,
            'created_at': self.created_at,
            'next_available_at': self.next_available_at,
            '_seq': self._seq,
        }
    
    @classmethod
    def from_dict(cls, d):
        t = cls.__new__(cls)
        t.task_id = d['task_id']
        t.priority = d['priority']
        t.max_retries = d['max_retries']
        t.attempts = d['attempts']
        t.dead = d['dead']
        t.created_at = d['created_at']
        t.next_available_at = d['next_available_at']
        t._seq = d['_seq']
        return t
    
    def __lt__(self, other):
        # Higher priority first, then FIFO by sequence
        if self.priority != other.priority:
            return self.priority > other.priority
        return self._seq < other._seq


class TaskQueue:
    """Priority task queue with delayed execution and retry support."""
    
    def __init__(self, persistence_path: Optional[str] = None):
        self._heap = []
        self._lock = threading.Lock()
        self.persistence_path = persistence_path
    
    def enqueue(self, task_id: Any, priority: int = 0, delay_ms: int = 0,
                max_retries: int = 0):
        """Add a task to the queue.
        
        Args:
            task_id: Identifier or callable for the task
            priority: Higher values = higher priority
            delay_ms: Delay before task becomes available
            max_retries: TOTAL attempts allowed (including first attempt)
        """
        task = Task(task_id, priority, delay_ms, max_retries)
        with self._lock:
            heapq.heappush(self._heap, task)
    
    def dequeue(self) -> Optional[Any]:
        """Get the highest priority available task."""
        now = time.time()
        with self._lock:
            # Find highest priority task that is available (not delayed)
            # We need to scan because the highest priority task might be delayed
            # while a lower priority one is ready
            available_tasks = []
            for task in self._heap:
                if not task.dead and task.next_available_at <= now:
                    available_tasks.append(task)
            
            if not available_tasks:
                return None
            
            # Get highest priority available task
            best_task = max(available_tasks, key=lambda t: (t.priority, -t._seq))
            self._heap.remove(best_task)
            heapq.heapify(self._heap)
            return best_task.task_id
    
    def _peek_raw(self) -> Optional[Task]:
        """Peek at the highest priority task (for testing)."""
        with self._lock:
            while self._heap:
                task = self._heap[0]
                if task.dead:
                    heapq.heappop(self._heap)
                    continue
                return task
            return None
    
    def execute_task(self, task: Task):
        """Execute a task, handling retries with exponential backoff.
        
        max_retries means TOTAL attempts. If max_retries=2, we try up to 2 times.
        """
        if task.dead or task.attempts >= task.max_retries:
            task.dead = True
            return
        
        task.attempts += 1
        
        if callable(task.task_id):
            try:
                task.task_id()
                # Success - remove from queue (mark dead)
                task.dead = True
            except Exception:
                # Failure - schedule retry if attempts remain
                if task.attempts >= task.max_retries:
                    task.dead = True
                else:
                    # Exponential backoff: 2^(attempts-1) * 100ms
                    backoff_ms = (2 ** (task.attempts - 1)) * 100
                    task.next_available_at = time.time() + (backoff_ms / 1000.0)
        else:
            # Non-callable tasks are considered successfully "executed"
            task.dead = True
    
    def size(self) -> int:
        """Total tasks in queue (including delayed and dead)."""
        with self._lock:
            return len([t for t in self._heap if not t.dead])
    
    def save(self):
        """Persist queue to JSON file."""
        if not self.persistence_path:
            return
        with self._lock:
            data = [t.to_dict() for t in self._heap if not t.dead]
        with open(self.persistence_path, 'w') as f:
            json.dump(data, f)
    
    def load(self):
        """Load queue from JSON file."""
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        with open(self.persistence_path, 'r') as f:
            data = json.load(f)
        with self._lock:
            self._heap = []
            for d in data:
                task = Task.from_dict(d)
                # When loading, if the task's delay has already expired,
                # it should be immediately available (next_available_at <= now)
                self._heap.append(task)
            heapq.heapify(self._heap)
