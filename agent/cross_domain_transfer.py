"""
cross_domain_transfer.py — Pattern generalization across domains.

Maps structural similarities between domains and proactively suggests
transfers: "You learned X about Python debugging — here's how it applies
to TypeScript" or "Patch failure pattern in Python → same in YAML."
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TransferSuggestion:
    source_domain: str
    target_domain: str
    pattern: str
    confidence: float
    explanation: str
    examples: List[str]


class CrossDomainTransfer:
    """Learn in one domain, apply in another."""

    # Domain similarity matrix — structural overlap
    DOMAIN_SIMILARITY = {
        ('python', 'typescript'): 0.85,
        ('python', 'javascript'): 0.80,
        ('typescript', 'javascript'): 0.90,
        ('bash', 'shell'): 0.95,
        ('docker', 'kubernetes'): 0.75,
        ('sql', 'postgresql'): 0.90,
        ('json', 'yaml'): 0.70,
        ('patch', 'edit'): 0.85,
        ('terminal', 'bash'): 0.90,
        ('web_search', 'web_extract'): 0.80,
        ('read_file', 'write_file'): 0.75,
    }

    # Pattern templates that generalize
    PATTERN_TEMPLATES = {
        'syntax_error': {
            'domains': ['python', 'typescript', 'javascript', 'bash', 'yaml', 'json'],
            'pattern': 'missing_delimiter',
            'signature': r'(unexpected|invalid|missing).*[:;,\[\]{}]',
        },
        'path_error': {
            'domains': ['terminal', 'read_file', 'write_file', 'patch', 'docker'],
            'pattern': 'invalid_path',
            'signature': r'(no such file|not found|invalid path|does not exist)',
        },
        'permission_error': {
            'domains': ['terminal', 'bash', 'docker', 'file'],
            'pattern': 'insufficient_permissions',
            'signature': r'(permission denied|access denied|unauthorized|forbidden)',
        },
        'timeout_error': {
            'domains': ['terminal', 'web_search', 'web_extract', 'delegate_task', 'browser'],
            'pattern': 'operation_timeout',
            'signature': r'(timeout|timed out|deadline exceeded|took too long)',
        },
        'format_error': {
            'domains': ['json', 'yaml', 'patch', 'write_file', 'xml'],
            'pattern': 'malformed_content',
            'signature': r'(invalid format|parse error|malformed|syntax error)',
        },
        'dependency_error': {
            'domains': ['python', 'typescript', 'javascript', 'docker'],
            'pattern': 'missing_dependency',
            'signature': r'(no module named|cannot find|not installed|missing package)',
        },
    }

    def __init__(self):
        self._learned_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self._transfer_history: List[TransferSuggestion] = []

    def _normalize_domain(self, text: str) -> str:
        """Extract domain from text context."""
        text_lower = text.lower()
        domains = {
            'python': ['python', '.py', 'pip', 'pytest'],
            'typescript': ['typescript', '.ts', 'tsx', 'tsc'],
            'javascript': ['javascript', '.js', 'jsx', 'npm'],
            'bash': ['bash', 'shell', '.sh', 'chmod'],
            'docker': ['docker', 'dockerfile', 'container'],
            'kubernetes': ['kubernetes', 'k8s', 'pod', 'deployment'],
            'sql': ['sql', 'database', 'query', 'select'],
            'json': ['json', '.json'],
            'yaml': ['yaml', '.yaml', '.yml'],
            'patch': ['patch', 'diff', 'replace'],
            'terminal': ['terminal', 'command line', 'cli'],
            'web_search': ['search', 'google', 'query'],
        }
        for domain, keywords in domains.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        return 'general'

    def _compute_similarity(self, domain_a: str, domain_b: str) -> float:
        """Compute similarity between two domains."""
        if domain_a == domain_b:
            return 1.0
        key = tuple(sorted([domain_a, domain_b]))
        return self.DOMAIN_SIMILARITY.get(key, 0.3)

    def record_pattern(self, domain: str, error_text: str, solution: str, success: bool):
        """Record a learned pattern from a domain."""
        # Classify the error
        pattern_type = None
        for ptype, pdef in self.PATTERN_TEMPLATES.items():
            if re.search(pdef['signature'], error_text, re.IGNORECASE):
                pattern_type = ptype
                break

        self._learned_patterns[domain].append({
            'pattern_type': pattern_type or 'unknown',
            'error': error_text[:200],
            'solution': solution[:500],
            'success': success,
        })

    def find_transfers(self, target_domain: str, limit: int = 5) -> List[TransferSuggestion]:
        """Find transferable patterns for a target domain."""
        suggestions = []

        for source_domain, patterns in self._learned_patterns.items():
            similarity = self._compute_similarity(source_domain, target_domain)
            if similarity < 0.5:
                continue

            # Group by pattern type
            by_type = defaultdict(list)
            for p in patterns:
                if p['success']:
                    by_type[p['pattern_type']].append(p)

            for ptype, pats in by_type.items():
                if not pats:
                    continue

                # Check if this pattern type applies to target
                template = self.PATTERN_TEMPLATES.get(ptype)
                if template and target_domain not in template['domains']:
                    continue

                confidence = similarity * min(1.0, len(pats) / 3)

                suggestion = TransferSuggestion(
                    source_domain=source_domain,
                    target_domain=target_domain,
                    pattern=ptype,
                    confidence=confidence,
                    explanation=f"Pattern '{ptype}' learned in {source_domain} ({len(pats)}x success) applies to {target_domain} (similarity: {similarity:.0%})",
                    examples=[p['solution'][:100] for p in pats[:2]]
                )
                suggestions.append(suggestion)

        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:limit]

    def suggest_for_action(self, action_type: str, detail: str, context: str = "") -> Optional[TransferSuggestion]:
        """Suggest a transfer before executing an action."""
        target_domain = self._normalize_domain(action_type + " " + detail + " " + context)

        suggestions = self.find_transfers(target_domain, limit=1)
        if suggestions and suggestions[0].confidence > 0.6:
            return suggestions[0]
        return None

    def get_transfer_stats(self) -> Dict:
        """Get statistics on cross-domain learning."""
        return {
            'domains_with_patterns': len(self._learned_patterns),
            'total_patterns': sum(len(p) for p in self._learned_patterns.values()),
            'successful_patterns': sum(
                1 for patterns in self._learned_patterns.values()
                for p in patterns if p['success']
            ),
            'domain_pairs': len(self.DOMAIN_SIMILARITY),
        }
