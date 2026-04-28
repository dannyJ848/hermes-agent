#!/usr/bin/env python3
"""Quick fix scanner — identifies common failure patterns and suggests fixes.

Run after catalog_failures.py to get actionable fix recommendations.
"""

import sys
import re
from collections import Counter

def analyze_failures(log_path):
    with open(log_path) as f:
        content = f.read()

    # Extract all failure blocks
    failure_blocks = re.findall(
        r'FAILED\s+(\S+)::(\S+)\n(.*?)(?=\nFAILED|\nERROR|\n=+ short test summary|\Z)',
        content,
        re.DOTALL
    )

    patterns = {
        'missing_attribute': [],
        'mock_assertion_mismatch': [],
        'value_mismatch_simple': [],
        'import_error': [],
        'timeout': [],
        'file_not_found': [],
        'other_assertion': [],
    }

    for test_file, test_name, traceback in failure_blocks:
        tb_lower = traceback.lower()

        if 'has no attribute' in tb_lower or "'NoneType' has no" in tb_lower:
            patterns['missing_attribute'].append((test_file, test_name, traceback))
        elif 'assertionerror' in tb_lower and 'expected call' in tb_lower:
            patterns['mock_assertion_mismatch'].append((test_file, test_name, traceback))
        elif 'assertionerror' in tb_lower and '==' in tb_lower:
            # Check if it's a simple value mismatch
            match = re.search(r"assert\s+(.+?)\s+==\s+(.+)", traceback)
            if match:
                patterns['value_mismatch_simple'].append((test_file, test_name, traceback))
            else:
                patterns['other_assertion'].append((test_file, test_name, traceback))
        elif 'importerror' in tb_lower or 'modulenotfound' in tb_lower:
            patterns['import_error'].append((test_file, test_name, traceback))
        elif 'timeout' in tb_lower:
            patterns['timeout'].append((test_file, test_name, traceback))
        elif 'filenotfound' in tb_lower or 'no such file' in tb_lower:
            patterns['file_not_found'].append((test_file, test_name, traceback))
        else:
            patterns['other_assertion'].append((test_file, test_name, traceback))

    return patterns


def suggest_fix(test_file, test_name, traceback, pattern_type):
    """Generate a fix suggestion for a specific failure."""
    suggestions = []

    if pattern_type == 'missing_attribute':
        # Extract the missing attribute name
        match = re.search(r"'\w+' object has no attribute '(\w+)'", traceback)
        if match:
            attr = match.group(1)
            suggestions.append(f"Add `{attr}` initialization to the object's __init__ or test setup")
            suggestions.append(f"  grep -r "def __init__" {test_file.replace('tests/', '').replace('test_', '')}")

    elif pattern_type == 'mock_assertion_mismatch':
        # Extract expected vs actual call
        match = re.search(r"Expected: (.*?)\n\s*Actual: (.*?)(?:\n|$)", traceback, re.DOTALL)
        if match:
            expected = match.group(1).strip()
            actual = match.group(2).strip()
            suggestions.append(f"Mock call mismatch:")
            suggestions.append(f"  Expected: {expected}")
            suggestions.append(f"  Actual:   {actual}")
            suggestions.append(f"  Fix: Update test assertion or the code being tested")

    elif pattern_type == 'value_mismatch_simple':
        match = re.search(r"assert\s+(.+?)\s+==\s+(.+)", traceback)
        if match:
            got = match.group(1).strip()
            expected = match.group(2).strip()
            suggestions.append(f"Value mismatch: expected {expected}, got {got}")
            suggestions.append(f"  Check if the expected value is still correct after recent changes")

    return suggestions


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 quick_fix_scan.py /path/to/pytest_output.log")
        sys.exit(1)

    log_path = sys.argv[1]
    patterns = analyze_failures(log_path)

    print("=" * 80)
    print("QUICK FIX ANALYSIS")
    print("=" * 80)

    total_fixable = 0
    for pattern_type, failures in sorted(patterns.items(), key=lambda x: -len(x[1])):
        count = len(failures)
        if count == 0:
            continue

        print(f"\n{pattern_type.upper().replace('_', ' ')}: {count} failures")
        print("-" * 60)

        for test_file, test_name, traceback in failures[:5]:  # Show first 5
            print(f"\n  {test_file}::{test_name}")
            suggestions = suggest_fix(test_file, test_name, traceback, pattern_type)
            for s in suggestions:
                print(f"    → {s}")

        if len(failures) > 5:
            print(f"    ... and {len(failures) - 5} more similar failures")

        if pattern_type in ('missing_attribute', 'mock_assertion_mismatch', 'value_mismatch_simple'):
            total_fixable += count

    print(f"\n\nEstimated quick fixes: {total_fixable} failures")
    print("These are likely fixable in <5 minutes each with targeted patches")


if __name__ == '__main__':
    main()
