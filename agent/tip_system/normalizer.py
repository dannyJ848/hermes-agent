#!/usr/bin/env python3
"""
tip_normalizer.py — Normalize tips into consistent WHEN/THEN format.

Converts free-form tips into structured behavioral tips:
  "WHEN <condition>, DO <action> <rationale>"

Also validates tips for:
  - Proper trigger condition
  - Actionable recommendation
  - Reasonable length (not too vague, not too specific)
  - No hallucinated facts

Usage:
    python3 tip_normalizer.py --file tips.json
    python3 tip_normalizer.py --text "Always check the docs first"
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TipNormalizer:
    """Normalizes and validates behavioral tips."""
    
    # Trigger words that indicate a condition
    TRIGGER_WORDS = [
        'when', 'if', 'before', 'after', 'during', 'while', 'upon',
        'given', 'in case', 'unless', 'until', 'once'
    ]
    
    # Action words that indicate a recommendation
    ACTION_WORDS = [
        'do', 'use', 'check', 'verify', 'run', 'try', 'ensure',
        'avoid', 'prefer', 'choose', 'enable', 'disable', 'set',
        'configure', 'install', 'update', 'restart', 'kill',
        'monitor', 'log', 'backup', 'test', 'validate'
    ]
    
    # Vague words that reduce tip quality
    VAGUE_WORDS = [
        'careful', 'carefully', 'maybe', 'perhaps', 'possibly',
        'might', 'could', 'should probably', 'try to', 'consider',
        'think about', 'be aware', 'keep in mind', 'remember to'
    ]
    
    def __init__(self):
        self.stats = {
            'processed': 0,
            'normalized': 0,
            'rejected': 0,
            'already_formatted': 0
        }
    
    def normalize(self, text: str, domain: str = "general") -> Optional[Dict]:
        """
        Normalize a tip into WHEN/THEN format.
        
        Returns:
            {
                'text': normalized_text,
                'condition': extracted_condition,
                'recommendation': extracted_recommendation,
                'rationale': extracted_rationale or None,
                'quality_score': 0.0-1.0,
                'issues': [list of issues],
                'is_valid': bool
            }
        """
        self.stats['processed'] += 1
        
        text = text.strip()
        if not text or len(text) < 10:
            self.stats['rejected'] += 1
            return None
        
        # Check if already in WHEN/THEN format
        if self._is_already_formatted(text):
            self.stats['already_formatted'] += 1
            return self._parse_formatted(text, domain)
        
        # Try to normalize
        normalized = self._attempt_normalization(text)
        
        if normalized:
            self.stats['normalized'] += 1
            return self._validate(normalized, domain)
        
        # Can't normalize - return as-is with low quality
        self.stats['rejected'] += 1
        return self._validate(text, domain)
    
    def _is_already_formatted(self, text: str) -> bool:
        """Check if tip is already in WHEN/THEN format."""
        text_lower = text.lower()
        return (
            text_lower.startswith('when ') or 
            text_lower.startswith('if ') or
            ' do ' in text_lower or
            ' do,' in text_lower
        )
    
    def _parse_formatted(self, text: str, domain: str) -> Dict:
        """Parse an already-formatted tip."""
        # Extract condition (before DO or comma)
        condition = None
        recommendation = text
        
        # Split on " DO " or " do "
        for marker in [' DO ', ' do ', ' DO,', ' do,']:
            if marker in text:
                parts = text.split(marker, 1)
                condition = parts[0].strip()
                recommendation = marker.strip() + ' ' + parts[1].strip()
                break
        
        # Extract rationale (after "to " or "because ")
        rationale = None
        for marker in [' to ', ' because ', ' in order to ', ' so that ']:
            if marker in recommendation.lower():
                idx = recommendation.lower().find(marker)
                rationale = recommendation[idx:].strip()
                recommendation = recommendation[:idx].strip()
                break
        
        return self._validate(text, domain, condition, recommendation, rationale)
    
    def _attempt_normalization(self, text: str) -> Optional[str]:
        """Try to convert free-form text into WHEN/THEN format."""
        text_lower = text.lower()
        
        # Strategy 1: Already starts with trigger word
        for trigger in self.TRIGGER_WORDS:
            if text_lower.startswith(trigger + ' '):
                # Add DO if missing
                if ' do ' not in text_lower and ' do,' not in text_lower:
                    # Find the action and insert DO
                    words = text.split()
                    for i, word in enumerate(words):
                        if word.lower() in self.ACTION_WORDS:
                            words.insert(i, 'DO')
                            return ' '.join(words)
                return text
        
        # Strategy 2: Contains "should" or "must" - convert to DO
        if ' should ' in text_lower or ' must ' in text_lower:
            # Replace should/must with DO
            new_text = re.sub(r'\b(should|must)\b', 'DO', text, flags=re.IGNORECASE)
            return f"WHEN relevant, {new_text}"
        
        # Strategy 3: Imperative sentence (starts with verb)
        first_word = text.split()[0].lower() if text.split() else ''
        if first_word in self.ACTION_WORDS:
            return f"WHEN applicable, DO {text}"
        
        # Strategy 4: General advice - wrap with WHEN/THEN
        return f"WHEN encountering this situation, DO {text}"
    
    def _validate(self, text: str, domain: str, condition: Optional[str] = None,
                  recommendation: Optional[str] = None, rationale: Optional[str] = None) -> Dict:
        """Validate a tip and compute quality score."""
        issues = []
        score = 0.5  # Base score
        
        # Check length
        word_count = len(text.split())
        if word_count < 5:
            issues.append("Too short - lacks specificity")
            score -= 0.2
        elif word_count > 50:
            issues.append("Too long - may be over-specific")
            score -= 0.1
        else:
            score += 0.1
        
        # Check for trigger condition
        has_trigger = any(t in text.lower() for t in self.TRIGGER_WORDS)
        if not has_trigger:
            issues.append("Missing trigger condition (WHEN/IF)")
            score -= 0.15
        else:
            score += 0.1
        
        # Check for action word
        has_action = any(a in text.lower() for a in self.ACTION_WORDS)
        if not has_action:
            issues.append("Missing actionable recommendation")
            score -= 0.15
        else:
            score += 0.1
        
        # Check for vague words
        vague_count = sum(1 for v in self.VAGUE_WORDS if v in text.lower())
        if vague_count > 0:
            issues.append(f"Contains {vague_count} vague word(s)")
            score -= 0.1 * vague_count
        
        # Check for specific technical terms (good sign)
        technical_terms = ['api', 'config', 'database', 'docker', 'git', 'json',
                          'python', 'sql', 'ssh', 'terminal', 'url', 'yaml',
                          'error', 'exception', 'timeout', 'cache', 'token']
        tech_count = sum(1 for t in technical_terms if t in text.lower())
        if tech_count > 0:
            score += 0.05 * min(tech_count, 3)
        
        # Check for hallucination patterns
        hallucination_patterns = [
            r'\b(never|always|all|every|none)\b.*\b(must|should)\b',
            r'\b100%\b',
            r'\bguaranteed\b',
        ]
        for pattern in hallucination_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("May contain overconfident/unverifiable claim")
                score -= 0.1
        
        # Clamp score
        score = max(0.0, min(1.0, score))
        
        # Determine validity
        is_valid = score >= 0.3 and len(issues) <= 2
        
        return {
            'text': text,
            'condition': condition or self._extract_condition(text),
            'recommendation': recommendation or text,
            'rationale': rationale,
            'quality_score': round(score, 3),
            'issues': issues,
            'is_valid': is_valid,
            'domain': domain,
            'word_count': word_count
        }
    
    def _extract_condition(self, text: str) -> Optional[str]:
        """Extract the condition part from a tip."""
        text_lower = text.lower()
        for trigger in self.TRIGGER_WORDS:
            if text_lower.startswith(trigger + ' '):
                # Find the boundary (comma, DO, or end of clause)
                rest = text[len(trigger)+1:]
                for marker in [', DO', ', do', ' DO ', ' do ', ',']:
                    if marker in rest:
                        return trigger + ' ' + rest[:rest.find(marker)].strip()
                return trigger + ' ' + rest
        return None
    
    def batch_normalize(self, tips: List[Dict]) -> List[Dict]:
        """Normalize a batch of tips."""
        results = []
        for tip in tips:
            text = tip.get('text', tip.get('content', ''))
            domain = tip.get('domain', 'general')
            
            normalized = self.normalize(text, domain)
            if normalized and normalized['is_valid']:
                results.append(normalized)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get normalization statistics."""
        return self.stats.copy()


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tip Normalizer')
    parser.add_argument('--file', help='JSON file with tips')
    parser.add_argument('--text', help='Single tip text to normalize')
    parser.add_argument('--output', help='Output file for normalized tips')
    
    args = parser.parse_args()
    
    normalizer = TipNormalizer()
    
    if args.text:
        result = normalizer.normalize(args.text)
        print(json.dumps(result, indent=2))
    
    elif args.file:
        with open(args.file) as f:
            tips = json.load(f)
        
        results = normalizer.batch_normalize(tips)
        
        print(f"Processed: {normalizer.stats['processed']}")
        print(f"Normalized: {normalizer.stats['normalized']}")
        print(f"Already formatted: {normalizer.stats['already_formatted']}")
        print(f"Rejected: {normalizer.stats['rejected']}")
        print(f"Valid output: {len(results)}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Wrote {len(results)} tips to {args.output}")
    
    else:
        # Interactive mode
        print("Tip Normalizer - Enter tips (Ctrl+D to finish):")
        tips = []
        while True:
            try:
                line = input("> ")
                if line.strip():
                    tips.append({'text': line})
            except EOFError:
                break
        
        results = normalizer.batch_normalize(tips)
        print(f"\nNormalized {len(results)} valid tips:")
        for r in results:
            print(f"  [{r['quality_score']:.2f}] {r['text']}")


if __name__ == "__main__":
    main()
