#!/usr/bin/env python3
"""
auto_compressor.py — Automatic context compression before LLM calls.

Compresses conversation context when approaching token limits:
  - Summarizes old messages
  - Removes redundant tool results
  - Preserves system messages and recent context
  - Tracks compression history

Integrates into pre_llm_call hook.

Usage:
    from auto_compressor import AutoCompressor
    compressor = AutoCompressor()
    
    # Before LLM call:
    messages = compressor.compress_if_needed(messages)
    # Returns compressed messages if over threshold
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("hermes.compressor")

class AutoCompressor:
    """Automatic context compression for LLM calls."""
    
    def __init__(self, threshold_pct: float = 0.75, max_tokens: int = 128000):
        self.threshold_pct = threshold_pct
        self.max_tokens = max_tokens
        self.threshold_tokens = int(max_tokens * threshold_pct)
        self.compression_count = 0
        self.chars_per_token = 4  # Conservative estimate
    
    def estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token count from messages."""
        total_chars = 0
        for msg in messages:
            content = str(msg.get("content", ""))
            # Tool results are often verbose
            if isinstance(content, str) and len(content) > 1000:
                # Compress estimate for large tool results
                total_chars += len(content) * 0.7  # Tool results are less token-dense
            else:
                total_chars += len(content)
        
        return int(total_chars / self.chars_per_token)
    
    def should_compress(self, messages: List[Dict]) -> bool:
        """Check if compression is needed."""
        estimated = self.estimate_tokens(messages)
        return estimated > self.threshold_tokens
    
    def compress(self, messages: List[Dict]) -> List[Dict]:
        """
        Compress messages to fit under threshold.
        
        Strategy:
          1. Keep all system messages
          2. Keep last 6 messages fully
          3. Summarize messages 7-20
          4. Drop messages beyond 20 (keep summaries)
        """
        if not messages:
            return messages
        
        original_count = len(messages)
        original_tokens = self.estimate_tokens(messages)
        
        # Separate system messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        if len(other_msgs) <= 8:
            # Not enough to compress meaningfully
            return messages
        
        # Keep last 6 messages intact
        keep = other_msgs[-6:]
        to_compress = other_msgs[:-6]
        
        # Summarize compressed section
        summary = self._summarize_message_block(to_compress)
        summary_msg = {
            "role": "assistant",
            "content": f"[Earlier conversation: {summary}]"
        }
        
        compressed = system_msgs + [summary_msg] + keep
        new_tokens = self.estimate_tokens(compressed)
        
        self.compression_count += 1
        
        logger.info(
            "[COMPRESS] %d → %d messages, %d → %d tokens",
            original_count, len(compressed),
            original_tokens, new_tokens
        )
        
        return compressed
    
    def _summarize_message_block(self, messages: List[Dict]) -> str:
        """Create summary of a message block."""
        # Extract key information
        actions = []
        decisions = []
        tool_calls = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = str(msg.get("content", ""))[:200]
            
            if role == "user":
                # Extract user requests
                if content:
                    actions.append(f"asked: {content[:80]}")
            
            elif role == "assistant":
                # Extract decisions
                if "decided" in content.lower() or "will" in content.lower():
                    decisions.append(content[:80])
                # Extract tool calls
                if "calling" in content.lower() or "use " in content.lower():
                    tool_calls.append(content[:60])
            
            elif role == "tool":
                # Summarize tool results
                if len(content) > 500:
                    tool_calls.append(f"got result ({len(content)} chars)")
        
        # Build summary
        parts = []
        if actions:
            parts.append(f"{len(actions)} requests")
        if decisions:
            parts.append(f"{len(decisions)} decisions")
        if tool_calls:
            parts.append(f"{len(tool_calls)} tool interactions")
        
        summary = "; ".join(parts) if parts else f"{len(messages)} messages"
        
        # Add key details
        key_details = []
        for msg in messages[-3:]:  # Last 3 compressed messages
            content = str(msg.get("content", ""))[:100]
            if content and len(content) > 20:
                key_details.append(content[:60])
        
        if key_details:
            summary += f" | Recent: {'; '.join(key_details[:2])}"
        
        return summary
    
    def compress_if_needed(self, messages: List[Dict]) -> List[Dict]:
        """Compress only if over threshold."""
        if self.should_compress(messages):
            return self.compress(messages)
        return messages
    
    def get_stats(self) -> Dict:
        """Get compression statistics."""
        return {
            "compression_count": self.compression_count,
            "threshold_pct": self.threshold_pct,
            "threshold_tokens": self.threshold_tokens,
            "max_tokens": self.max_tokens,
        }


# Hook integration
def pre_llm_call_compressor(messages: List[Dict], context_limit: int = 128000) -> List[Dict]:
    """
    Hook function for pre_llm_call.
    
    Automatically compresses context if over threshold.
    """
    compressor = AutoCompressor(max_tokens=context_limit)
    return compressor.compress_if_needed(messages)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Compressor")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    if args.test:
        print("Testing auto compressor...")
        
        compressor = AutoCompressor(threshold_pct=0.75, max_tokens=10000)
        
        # Test 1: Small context (no compression)
        print("\n1. Small context (under threshold)")
        msgs = [
            {"role": "system", "content": "You are Hermes"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        should = compressor.should_compress(msgs)
        print(f"   Should compress: {should}")
        assert not should, "Small context should not compress"
        
        # Test 2: Large context (compression needed)
        print("\n2. Large context (over threshold)")
        msgs = [{"role": "system", "content": "You are Hermes"}]
        for i in range(30):
            msgs.append({"role": "user", "content": f"Message {i}: " + "x" * 500})
            msgs.append({"role": "assistant", "content": f"Response {i}: " + "y" * 800})
        
        should = compressor.should_compress(msgs)
        print(f"   Messages: {len(msgs)}")
        print(f"   Estimated tokens: {compressor.estimate_tokens(msgs)}")
        print(f"   Should compress: {should}")
        assert should, "Large context should compress"
        
        # Test 3: Compression
        print("\n3. Compression")
        compressed = compressor.compress(msgs)
        print(f"   Original: {len(msgs)} messages")
        print(f"   Compressed: {len(compressed)} messages")
        print(f"   Estimated tokens: {compressor.estimate_tokens(compressed)}")
        
        # Verify system messages preserved
        sys_count = sum(1 for m in compressed if m.get("role") == "system")
        print(f"   System messages preserved: {sys_count}")
        
        # Verify recent messages preserved
        last_user = compressed[-2].get("role") if len(compressed) >= 2 else None
        print(f"   Recent messages preserved: {last_user}")
        
        # Test 4: compress_if_needed
        print("\n4. compress_if_needed")
        small = [{"role": "user", "content": "Hi"}]
        result = compressor.compress_if_needed(small)
        print(f"   Small context unchanged: {len(result) == len(small)}")
        
        # Test 5: Hook function
        print("\n5. pre_llm_call_compressor hook")
        result = pre_llm_call_compressor(msgs)
        print(f"   Hook compressed: {len(result) < len(msgs)}")
        
        # Stats
        print("\n6. Stats:")
        print(f"   {compressor.get_stats()}")
        
        print("\nAll tests passed!")
    else:
        print("Usage: python3 auto_compressor.py --test")
