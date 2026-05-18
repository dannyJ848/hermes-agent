"""
Rate Limiter Suite.

Features:
1. token bucket algorithm with configurable capacity and refill rate
2. sliding window counter with time-bucket granularity
3. fixed window counter with atomic increment
4. leaky bucket algorithm that smooths burst traffic
5. multi-rate limiter that enforces different limits per key

All implementations are thread-safe.
"""

import time
import threading
from typing import Dict, Optional


class TokenBucket:
    """Token bucket rate limiter.
    
    Allows bursts up to capacity, then refills at refill_rate tokens per second.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def allow(self, tokens: int = 1) -> bool:
        """Request tokens. Returns True if allowed, False if not enough tokens."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            # Refill tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class SlidingWindow:
    """Sliding window counter rate limiter.
    
    Uses time-bucket granularity to track requests in a sliding time window.
    """
    
    def __init__(self, limit: int, window_ms: int, bucket_ms: int = 100):
        self.limit = limit
        self.window_ms = window_ms
        self.bucket_ms = bucket_ms
        self.buckets: Dict[int, int] = {}  # bucket_start_ms -> count
        self._lock = threading.Lock()
    
    def allow(self) -> bool:
        """Check if request is allowed under sliding window limit."""
        with self._lock:
            now_ms = int(time.time() * 1000)
            window_start = now_ms - self.window_ms
            
            # Remove expired buckets
            self.buckets = {
                k: v for k, v in self.buckets.items() 
                if k >= window_start
            }
            
            # Count requests in current window
            current_count = sum(self.buckets.values())
            
            if current_count < self.limit:
                # Add to current bucket
                bucket_start = (now_ms // self.bucket_ms) * self.bucket_ms
                self.buckets[bucket_start] = self.buckets.get(bucket_start, 0) + 1
                return True
            return False


class FixedWindow:
    """Fixed window counter rate limiter with atomic increment.
    
    Resets counter at window boundaries.
    """
    
    def __init__(self, limit: int, window_ms: int):
        self.limit = limit
        self.window_ms = window_ms
        self.count = 0
        self.window_start = int(time.time() * 1000)
        self._lock = threading.Lock()
    
    def allow(self) -> bool:
        """Check if request is allowed under fixed window limit."""
        with self._lock:
            now_ms = int(time.time() * 1000)
            
            # Check if window has reset
            if now_ms >= self.window_start + self.window_ms:
                self.window_start = now_ms
                self.count = 0
            
            if self.count < self.limit:
                self.count += 1
                return True
            return False


class LeakyBucket:
    """Leaky bucket rate limiter.
    
    Smooths burst traffic by leaking at a constant rate.
    """
    
    def __init__(self, rate: float, per_ms: float = 1000.0):
        self.rate = rate  # requests allowed
        self.per_ms = per_ms  # per this many milliseconds
        self.water = 0.0  # current "water level"
        self.last_leak = time.time()
        self._lock = threading.Lock()
    
    def allow(self) -> bool:
        """Check if request is allowed. Rejects if bucket is full."""
        with self._lock:
            now = time.time()
            elapsed_ms = (now - self.last_leak) * 1000
            
            # Leak water at constant rate
            leaked = elapsed_ms * (self.rate / self.per_ms)
            self.water = max(0, self.water - leaked)
            self.last_leak = now
            
            # Check if we can add more water
            if self.water < 1.0:
                self.water += 1.0
                return True
            return False


class MultiRateLimiter:
    """Multi-rate limiter that enforces different limits per key."""
    
    def __init__(self):
        self.limiters: Dict[str, object] = {}
        self._lock = threading.Lock()
    
    def add_limit(self, key: str, limiter):
        """Add a rate limiter for a specific key."""
        with self._lock:
            self.limiters[key] = limiter
    
    def allow(self, key: str, tokens: int = 1) -> bool:
        """Check if request for key is allowed.
        
        If key has no limiter, allows by default.
        """
        with self._lock:
            limiter = self.limiters.get(key)
        
        if limiter is None:
            return True
        
        # Delegate to specific limiter
        if hasattr(limiter, 'allow'):
            if tokens == 1:
                return limiter.allow()
            else:
                return limiter.allow(tokens)
        return True
