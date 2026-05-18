"""
Test suite for Task Queue with Priority and Delayed Execution.
Features:
1. enqueue with priority and optional delay
2. dequeue by priority then FIFO
3. delayed tasks become available only after delay expires
4. task retry with exponential backoff on failure
5. queue persistence to JSON file for crash recovery
"""

import pytest
import time
import os
import json
import tempfile
from task_queue import TaskQueue, Task


class TestFeature1Enqueue:
    """Feature 1: enqueue with priority and optional delay"""
    
    def test_enqueue_basic(self):
        q = TaskQueue()
        q.enqueue("task1", priority=5)
        assert q.size() == 1
    
    def test_enqueue_with_delay(self):
        q = TaskQueue()
        q.enqueue("task1", priority=5, delay_ms=100)
        assert q.size() == 1  # Task is in queue but not ready


class TestFeature2DequeuePriority:
    """Feature 2: dequeue by priority then FIFO"""
    
    def test_dequeue_highest_priority_first(self):
        q = TaskQueue()
        q.enqueue("low", priority=1)
        q.enqueue("high", priority=10)
        q.enqueue("med", priority=5)
        
        assert q.dequeue() == "high"
        assert q.dequeue() == "med"
        assert q.dequeue() == "low"
    
    def test_dequeue_fifo_same_priority(self):
        q = TaskQueue()
        q.enqueue("first", priority=5)
        q.enqueue("second", priority=5)
        q.enqueue("third", priority=5)
        
        assert q.dequeue() == "first"
        assert q.dequeue() == "second"
        assert q.dequeue() == "third"


class TestFeature3DelayedExecution:
    """Feature 3: delayed tasks become available only after delay expires"""
    
    def test_delayed_task_not_immediately_available(self):
        q = TaskQueue()
        q.enqueue("delayed", priority=10, delay_ms=200)
        assert q.dequeue() is None  # Not ready yet
    
    def test_delayed_task_available_after_delay(self):
        q = TaskQueue()
        q.enqueue("delayed", priority=10, delay_ms=50)
        time.sleep(0.08)  # Wait for delay to expire
        assert q.dequeue() == "delayed"


class TestFeature4RetryWithBackoff:
    """Feature 4: task retry with exponential backoff on failure
    
    max_retries=2 means 2 TOTAL attempts (initial + 1 retry).
    """
    
    def test_retry_on_failure(self):
        q = TaskQueue()
        attempts = []
        
        def failing_task():
            attempts.append(1)
            raise ValueError("fail")
        
        q.enqueue(failing_task, priority=5, max_retries=2)
        task = q._peek_raw()
        
        # First attempt fails
        q.execute_task(task)
        assert len(attempts) == 1
        assert task.attempts == 1
        
        # Should be scheduled for retry with backoff
        assert task.next_available_at > time.time()
    
    def test_max_retries_total_attempts(self):
        """max_retries=2 means exactly 2 total attempts, then marked dead."""
        q = TaskQueue()
        attempts = []
        
        def failing_task():
            attempts.append(1)
            raise ValueError("fail")
        
        q.enqueue(failing_task, priority=5, max_retries=2)
        task = q._peek_raw()
        
        # Attempt 1
        q.execute_task(task)
        assert task.attempts == 1
        
        # Simulate backoff elapsed
        task.next_available_at = 0
        
        # Attempt 2 (final)
        q.execute_task(task)
        assert task.attempts == 2
        assert task.dead
        
        # No more attempts
        q.execute_task(task)
        assert len(attempts) == 2  # Only 2 total attempts


class TestFeature5Persistence:
    """Feature 5: queue persistence to JSON file for crash recovery"""
    
    def test_persistence_save_and_load(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            q1 = TaskQueue(persistence_path=path)
            q1.enqueue("task1", priority=5)
            q1.enqueue("task2", priority=10, delay_ms=1000)
            q1.save()
            
            q2 = TaskQueue(persistence_path=path)
            q2.load()
            
            # Both tasks should be restored
            assert q2.size() == 2
            
            # Priority order preserved
            assert q2.dequeue() == "task1"  # No delay
            # task2 has delay, may or may not be ready depending on timing
        finally:
            os.unlink(path)
    
    def test_persistence_with_ready_delayed_tasks(self):
        """Delayed tasks that have expired should be ready after load."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            q1 = TaskQueue(persistence_path=path)
            q1.enqueue("delayed", priority=10, delay_ms=50)
            q1.save()
            
            time.sleep(0.08)  # Wait for delay to expire
            
            q2 = TaskQueue(persistence_path=path)
            q2.load()
            
            # Task should be available (delay expired before load)
            result = q2.dequeue()
            assert result == "delayed"
        finally:
            os.unlink(path)
