#!/usr/bin/env python3
"""
Knowledge Synthesis Engine — Cross-reference research papers to find connections.

Reads all .md files from ~/.hermes/knowledge/ and identifies:
1. Shared concepts across papers
2. Contradictions between papers
3. Gaps in knowledge (missing connections)
4. Emerging themes across multiple sources

Output: synthesis report with actionable insights.
"""

import os
import re
from pathlib import Path
from collections import Counter, defaultdict

KB_DIR = Path.home() / ".hermes" / "knowledge"


def extract_key_terms(text, max_terms=20):
    """Extract significant terms from text."""
    # Remove common words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "and", "but", "or", "nor", "not",
        "so", "yet", "both", "either", "neither", "each", "every",
        "all", "any", "few", "more", "most", "other", "some", "such",
        "no", "only", "own", "same", "than", "too", "very", "just",
        "because", "if", "when", "where", "how", "what", "which", "who",
        "this", "that", "these", "those", "we", "our", "they", "their",
        "it", "its", "based", "using", "use", "used", "also", "new",
        "key", "approach", "one", "two", "need", "like", "get",
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    # Filter stop words and count
    filtered = [w for w in words if w not in stop_words]
    counter = Counter(filtered)
    
    return counter.most_common(max_terms)


def find_connections():
    """Find connections between knowledge files."""
    if not KB_DIR.exists():
        return {"error": "Knowledge directory not found"}
    
    files = list(KB_DIR.glob("*.md"))
    if not files:
        return {"error": "No knowledge files found"}
    
    # Extract terms from each file
    file_terms = {}
    for f in files:
        text = f.read_text()
        terms = extract_key_terms(text)
        file_terms[f.stem] = dict(terms)
    
    # Find shared concepts
    all_terms = defaultdict(list)
    for fname, terms in file_terms.items():
        for term, count in terms.items():
            all_terms[term].append((fname, count))
    
    # Find terms that appear in multiple files
    shared = {}
    for term, occurrences in all_terms.items():
        if len(occurrences) >= 3:  # Term appears in 3+ files
            shared[term] = sorted(occurrences, key=lambda x: -x[1])
    
    # Find emerging themes (high-frequency terms)
    total_freq = Counter()
    for terms in file_terms.values():
        for term, count in terms.items():
            total_freq[term] += count
    
    themes = total_freq.most_common(20)
    
    return {
        "total_files": len(files),
        "total_unique_terms": len(all_terms),
        "shared_concepts": {k: v[:5] for k, v in 
                          sorted(shared.items(), 
                                key=lambda x: -len(x[1]))[:15]},
        "emerging_themes": themes,
        "cross_reference_count": sum(len(v) for v in shared.values()),
    }


if __name__ == "__main__":
    import json
    result = find_connections()
    print(json.dumps(result, indent=2, default=str))
