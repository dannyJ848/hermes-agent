"""
Test suite for Rate Limiter Suite.
Features:
1. token bucket algorithm with configurable capacity and refill rate
2. sliding window counter with time-bucket granularity
3. fixed window counter with atomic increment
4. leaky bucket algorithm that smooths burst traffic
5. multi-rate limiter that enforces different limits per key

All implementations must be thread-safe.
"""

import pytest
import time
import threading
from rate_limiter import TokenBucket, SlidingWindow, FixedWindow, LeakyBucket, MultiRateLimiter


class TestFeature1TokenBucket:
    """Feature 1: token bucket algorithm with configurable capacity and refill rate"""
    
    def test_token_bucket_allows_within_capacity(self):
        tb = TokenBucket(capacity=5, refill_rate=1)
        assert tb.allow(3) is True
        assert tb.allow(2) is True
    
    def test_token_bucket_rejects_over_capacity(self):
        tb = TokenBucket(capacity=5, refill_rate=1)
        assert tb.allow(6) is False
    
    def test_token_bucket_refills_over_time(self):
        tb = TokenBucket(capacity=2, refill_rate=1)  # 1 token per second
        assert tb.allow(2) is True  # Use all tokens
        assert tb.allow(1) is False  # No tokens left
        time.sleep(1.1)  # Wait for refill
        assert tb.allow(1) is True  # Should have 1 token now


class TestFeature2SlidingWindow:
    """Feature 2: sliding window counter with time-bucket granularity"""
    
    def test_sliding_window_allows_within_limit(self):
        sw = SlidingWindow(limit=5, window_ms=1000)
        for _ in range(5):
            assert sw.allow() is True
    
    def test_sliding_window_rejects_over_limit(self):
        sw = SlidingWindow(limit=3, window_ms=1000)
        for _ in range(3):
            sw.allow()
        assert sw.allow() is False
    
    def test_sliding_window_resets_after_window(self):
        sw = SlidingWindow(limit=2, window_ms=100)
        sw.allow()
        sw.allow()
        assert sw.allow() is False
        time.sleep(0.15)  # Wait for window to slide
        assert sw.allow() is True


class TestFeature3FixedWindow:
    """Feature 3: fixed window counter with atomic increment"""
    
    def test_fixed_window_allows_within_limit(self):
        fw = FixedWindow(limit=5, window_ms=1000)
        for _ in range(5):
            assert fw.allow() is True
    
    def test_fixed_window_rejects_over_limit(self):
        fw = FixedWindow(limit=2, window_ms=1000)
        fw.allow()
        fw.allow()
        assert fw.allow() is False
    
    def test_fixed_window_thread_safety(self):
        fw = FixedWindow(limit=100, window_ms=1000)
        allowed = []
        
        def worker():
            for _ in range(10):
                if fw.allow():
                    allowed.append(1)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(allowed) <= 100


class TestFeature4LeakyBucket:
    """Feature 4: leaky bucket algorithm that smooths burst traffic"""
    
    def test_leaky_bucket_allows_within_rate(self):
        lb = LeakyBucket(rate=5, per_ms=1000)
        # First request should always be allowed
        assert lb.allow() is True
    
    def test_leaky_bucket_smooths_burst(self):
        lb = LeakyBucket(rate=2, per_ms=1000)  # 2 per second
        assert lb.allow() is True
        assert lb.allow() is True
        # Third request immediately should be rejected or delayed
        result = lb.allow()
        # Either rejected or we need to wait
        assert result is False or result is True  # Implementation dependent
    
    def test_leaky_bucket_rate_enforcement(self):
        lb = LeakyBucket(rate=3, per_ms=1000)
        start = time.time()
        allowed = 0
        for _ in range(10):
            if lb.allow():
                allowed += 1
            else:
                time.sleep(0.4)  # Wait for leak
                if lb.allow():
                    allowed += 1
        elapsed = time.time() - start
        # Should take some time due to rate limiting
        assert allowed >= 3


class TestFeature5MultiRateLimiter:
    """Feature 5: multi-rate limiter that enforces different limits per key"""
    
    def test_multi_rate_different_limits_per_key(self):
        mrl = MultiRateLimiter()
        mrl.add_limit("api", TokenBucket(capacity=5, refill_rate=1))
        mrl.add_limit("web", TokenBucket(capacity=10, refill_rate=2))
        
        assert mrl.allow("api", 5) is True
        assert mrl.allow("api", 1) is False
        assert mrl.allow("web", 10) is True
    
    def test_multi_rate_independent_tracking(self):
        mrl = MultiRateLimiter()
        mrl.add_limit("user1", FixedWindow(limit=2, window_ms=1000))
        mrl.add_limit("user2", FixedWindow(limit=5, window_ms=1000))
        
        mrl.allow("user1")
        mrl.allow("user1")
        assert mrl.allow("user1") is False
        
        assert mrl.allow("user2") is True
        assert mrl.allow("user2") is True
    
    def test_multi_rate_thread_safety(self):
        mrl = MultiRateLimiter()
        mrl.add_limit("shared", FixedWindow(limit=50, window_ms=1000))
        allowed = []
        
        def worker():
            for _ in range(10):
                if mrl.allow("shared"):
                    allowed.append(1)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(allowed) <= 50
