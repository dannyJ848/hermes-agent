#!/usr/bin/env python3
"""
llm_judge.py — LLM-based evaluation of distilled tips.

Uses DeepSeek API (or OpenRouter fallback) to compare two tips and
judge which is more useful, accurate, and actionable.

Key features:
  - Structured JSON output with winner + confidence + reasoning
  - Cost tracking (per-call and cumulative)
  - Retry with exponential backoff
  - Fallback to heuristic if LLM fails
"""

import os
import json
import time
import hashlib
from typing import Dict, Tuple, Optional
from pathlib import Path

# Load env from ~/.hermes/.env if present
_ENV_PATH = Path.home() / ".hermes" / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = val

# Try to import requests, fallback to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


class LLMJudge:
    """LLM-based tip evaluator using OpenRouter or local model."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-v4-pro", base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.total_cost = 0.0
        self.total_calls = 0
        self.failed_calls = 0
        
        # Cost per 1M tokens (input, output) for common models
        self.cost_map = {
            "deepseek-v4-pro": (0.109, 0.218),  # 75% discount until 2026/05/31
            "deepseek-chat": (0.14, 0.28),
            "openrouter/deepseek/deepseek-chat-v3-0324": (0.27, 1.10),
            "openrouter/anthropic/claude-3.5-sonnet": (3.00, 15.00),
            "openrouter/anthropic/claude-3.5-haiku": (0.80, 4.00),
            "openrouter/google/gemini-2.5-flash": (0.15, 0.60),
            "openrouter/moonshotai/kimi-k2": (1.00, 4.00),
        }
    
    def _call_llm(self, messages: list, temperature: float = 0.3, max_tokens: int = 2000, response_format: dict = None) -> str:
        """Call LLM API with retry logic.
        
        DeepSeek V4 Pro puts JSON output in reasoning_content when using
        response_format. We check both fields and extract JSON from reasoning.
        """
        if not self.api_key:
            raise ValueError("No API key available for LLM judge")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if HAS_REQUESTS:
                    resp = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    resp.raise_for_status()
                    data = resp.json()
                else:
                    req = urllib.request.Request(
                        f"{self.base_url}/chat/completions",
                        data=json.dumps(payload).encode(),
                        headers=headers,
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data = json.loads(resp.read().decode())
                
                msg = data['choices'][0]['message']
                content = msg.get('content', '')
                
                # DeepSeek V4 Pro: JSON may be in reasoning_content when using response_format
                if not content and 'reasoning_content' in msg:
                    reasoning = msg['reasoning_content']
                    # Extract JSON object from reasoning text
                    content = self._extract_json_from_text(reasoning)
                
                # Track cost
                usage = data.get('usage', {})
                input_toks = usage.get('prompt_tokens', 0)
                output_toks = usage.get('completion_tokens', 0)
                self._track_cost(input_toks, output_toks)
                
                self.total_calls += 1
                return content
                
            except Exception as e:
                self.failed_calls += 1
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        
        raise RuntimeError("Max retries exceeded")
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON object from text that may contain markdown or explanations."""
        import re
        
        # Try to find JSON between ```json fences
        code_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try to find JSON between ``` fences
        code_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try to find first { ... } block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text.strip()
    
    def _track_cost(self, input_tokens: int, output_tokens: int):
        """Track API cost."""
        costs = self.cost_map.get(self.model, (1.0, 4.0))
        cost = (input_tokens * costs[0] + output_tokens * costs[1]) / 1_000_000
        self.total_cost += cost
    
    def compare_tips(self, tip_a, tip_b) -> Dict:
        """Compare two tips and return structured evaluation.
        
        Accepts either dict (with 'text', 'domain', 'confidence' keys) or plain strings.
        
        Returns:
            {
                "winner": "a" | "b" | "t",
                "confidence": 0.0-1.0,
                "reasoning": "explanation",
                "dimensions": {
                    "specificity": {"a": 0-10, "b": 0-10},
                    "actionability": {"a": 0-10, "b": 0-10},
                    "accuracy": {"a": 0-10, "b": 0-10},
                    "generality": {"a": 0-10, "b": 0-10}
                }
            }
        """
        # Normalize to dict
        if isinstance(tip_a, str):
            tip_a = {"text": tip_a, "domain": "general", "confidence": 0.5}
        if isinstance(tip_b, str):
            tip_b = {"text": tip_b, "domain": "general", "confidence": 0.5}
        
        prompt = f"""You are an expert evaluator of AI assistant behavioral tips.

Evaluate these two tips and judge which is MORE USEFUL for an AI assistant.

Tip A:
"{tip_a['text']}"
Domain: {tip_a.get('domain', 'general')}
Confidence: {tip_a.get('confidence', 0.5)}

Tip B:
"{tip_b['text']}"
Domain: {tip_b.get('domain', 'general')}
Confidence: {tip_b.get('confidence', 0.5)}

Rate each tip on these dimensions (0-10):
1. Specificity: How concrete and detailed is the advice?
2. Actionability: Can the AI immediately act on this tip?
3. Accuracy: Is the technical advice correct?
4. Generality: Does it apply broadly or just to one edge case?

Return a JSON object with these exact keys:
- "winner": "a" or "b" or "t" (for tie)
- "confidence": a number between 0.0 and 1.0
- "reasoning": a 1-2 sentence explanation
- "dimensions": an object with "specificity", "actionability", "accuracy", "generality", each containing {{"a": 0, "b": 0}} with scores 0-10

Example response:
{{"winner": "a", "confidence": 0.9, "reasoning": "Tip A is more specific.", "dimensions": {{"specificity": {{"a": 8, "b": 4}}, "actionability": {{"a": 7, "b": 6}}, "accuracy": {{"a": 9, "b": 8}}, "generality": {{"a": 6, "b": 5}}}}}}
"""
        
        messages = [
            {"role": "system", "content": "You are a precise evaluator. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_llm(messages)
            result = json.loads(response)
            
            # Validate structure
            if 'winner' not in result or result['winner'] not in ('a', 'b', 't'):
                result['winner'] = 't'
            if 'confidence' not in result:
                result['confidence'] = 0.5
            if 'reasoning' not in result:
                result['reasoning'] = "No reasoning provided"
            if 'dimensions' not in result:
                result['dimensions'] = {}
            
            return result
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            # Fallback to tie with low confidence
            return {
                "winner": "t",
                "confidence": 0.5,
                "reasoning": f"LLM evaluation failed: {str(e)}",
                "dimensions": {}
            }
    
    def evaluate_single(self, tip: Dict) -> Dict:
        """Evaluate a single tip for quality issues."""
        prompt = f"""Evaluate this AI assistant behavioral tip for quality issues:

"{tip['text']}"
Domain: {tip.get('domain', 'general')}

Check for:
1. Vagueness (e.g., "be careful", "try to")
2. Incorrect technical advice
3. Missing trigger condition (no WHEN/IF)
4. Missing action (no DO/USE/CHECK)
5. Over-specificity (only applies to one rare case)

Return a JSON object with these exact keys:
- "quality_score": a number between 0.0 and 1.0
- "issues": a list of strings describing any problems found (empty list if none)
- "suggested_fix": either an improved version of the tip, or null
- "is_actionable": true or false

Example response:
{{"quality_score": 0.85, "issues": [], "suggested_fix": null, "is_actionable": true}}
"""
        
        messages = [
            {"role": "system", "content": "You are a quality auditor. After thinking, output ONLY valid JSON in the content field. No markdown, no explanations outside JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_llm(messages, max_tokens=2000, response_format={"type": "json_object"})
            return json.loads(response)
        except Exception as e:
            return {
                "quality_score": 0.5,
                "issues": [f"Evaluation failed: {str(e)}"],
                "suggested_fix": None,
                "is_actionable": True
            }
    
    def get_cost_report(self) -> Dict:
        """Get cost tracking report."""
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round((self.total_calls - self.failed_calls) / max(self.total_calls, 1), 3),
            "model": self.model
        }


def main():
    """CLI test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM Judge Test')
    parser.add_argument('--tip-a', required=True, help='First tip text')
    parser.add_argument('--tip-b', required=True, help='Second tip text')
    parser.add_argument('--model', default='deepseek-v4-pro', help='Model to use')
    
    args = parser.parse_args()
    
    judge = LLMJudge(model=args.model)
    
    tip_a = {"text": args.tip_a, "domain": "general", "confidence": 0.8}
    tip_b = {"text": args.tip_b, "domain": "general", "confidence": 0.7}
    
    result = judge.compare_tips(tip_a, tip_b)
    print(json.dumps(result, indent=2))
    print(f"\nCost: ${judge.total_cost:.4f}")


if __name__ == "__main__":
    main()

    def compare_prompt_fragments(self, fragment_a: str, fragment_b: str, fragment_type: str) -> int:
        """Compare two prompt fragments. Returns 1 if A wins, 2 if B wins."""
        prompt = f"""You are evaluating AI system prompt fragments for a CLI agent.

Fragment A ({fragment_type}):
{fragment_a}

Fragment B ({fragment_type}):
{fragment_b}

Which fragment would produce more effective, precise, and safe behavior from an AI assistant?

Consider:
1. Clarity — is the instruction unambiguous?
2. Actionability — can the assistant follow it directly?
3. Safety — does it prevent harmful outcomes?
4. Specificity — is it concrete rather than vague?

Return ONLY "A" or "B"."""
        
        messages = [
            {"role": "system", "content": "You are a precise evaluator. Return only A or B."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages).strip().upper()
        if response.startswith("A"):
            return 1
        elif response.startswith("B"):
            return 2
        else:
            # Tie-break: random
            import random
            return random.choice([1, 2])

    def compare_prompt_fragments(self, fragment_a: str, fragment_b: str, fragment_type: str) -> int:
        """Compare two prompt fragments. Returns 1 if A wins, 2 if B wins."""
        prompt = f"""You are evaluating AI system prompt fragments for a CLI agent.

Fragment A ({fragment_type}):
{fragment_a}

Fragment B ({fragment_type}):
{fragment_b}

Which fragment would produce more effective, precise, and safe behavior from an AI assistant?

Consider:
1. Clarity — is the instruction unambiguous?
2. Actionability — can the assistant follow it directly?
3. Safety — does it prevent harmful outcomes?
4. Specificity — is it concrete rather than vague?

Return ONLY "A" or "B"."""
        
        messages = [
            {"role": "system", "content": "You are a precise evaluator. Return only A or B."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages).strip().upper()
        if response.startswith("A"):
            return 1
        elif response.startswith("B"):
            return 2
        else:
            # Tie-break: random
            import random
            return random.choice([1, 2])
