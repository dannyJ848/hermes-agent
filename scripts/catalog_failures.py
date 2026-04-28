#!/usr/bin/env python3
"""Hermes Test Suite Failure Catalog — auto-generated diagnostic report.

Parses pytest output and categorizes failures by:
1. Test file / subsystem
2. Failure type (assertion error, import error, missing attribute, etc.)
3. Whether it's likely a pre-existing issue or caused by recent changes
4. Estimated fix complexity

Usage: python3 catalog_failures.py /path/to/pytest_output.log
"""

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set

@dataclass
class Failure:
    test_file: str
    test_name: str
    error_type: str
    error_message: str
    subsystem: str
    likely_cause: str = "unknown"
    fix_complexity: str = "unknown"


def parse_pytest_output(log_path: str) -> List[Failure]:
    """Parse pytest output and extract failures."""
    failures = []
    current_failure = None
    collecting_traceback = False
    traceback_lines = []

    with open(log_path) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        # Match FAILED line
        failed_match = re.match(r'^FAILED\s+(\S+)::(.+)$', line.strip())
        if failed_match:
            test_path = failed_match.group(1)
            test_name = failed_match.group(2)
            subsystem = test_path.split('/')[1] if '/' in test_path else 'unknown'
            current_failure = {
                'test_file': test_path,
                'test_name': test_name,
                'subsystem': subsystem,
                'traceback': [],
            }
            collecting_traceback = True
            traceback_lines = []
            i += 1
            continue

        # Match ERROR line (import errors, collection errors)
        error_match = re.match(r'^ERROR\s+(\S+)\s+-\s+(.+)$', line.strip())
        if error_match:
            test_path = error_match.group(1)
            error_msg = error_match.group(2)
            subsystem = test_path.split('/')[1] if '/' in test_path else 'unknown'
            failures.append(Failure(
                test_file=test_path,
                test_name="COLLECTION_ERROR",
                error_type="ImportError/CollectionError",
                error_message=error_msg,
                subsystem=subsystem,
                likely_cause="missing_dependency_or_broken_import",
                fix_complexity="low" if "No module named" in error_msg else "medium"
            ))
            i += 1
            continue

        # Collect traceback until we hit a blank line or next test
        if collecting_traceback:
            if line.strip() == '' and len(traceback_lines) > 5:
                # End of traceback, extract error
                error_type, error_message = extract_error_from_traceback(traceback_lines)
                failures.append(Failure(
                    test_file=current_failure['test_file'],
                    test_name=current_failure['test_name'],
                    error_type=error_type,
                    error_message=error_message,
                    subsystem=current_failure['subsystem'],
                    likely_cause=infer_likely_cause(error_type, error_message),
                    fix_complexity=estimate_complexity(error_type, error_message)
                ))
                collecting_traceback = False
                current_failure = None
            else:
                traceback_lines.append(line.rstrip())

        i += 1

    # Handle any dangling traceback
    if collecting_traceback and current_failure:
        error_type, error_message = extract_error_from_traceback(traceback_lines)
        failures.append(Failure(
            test_file=current_failure['test_file'],
            test_name=current_failure['test_name'],
            error_type=error_type,
            error_message=error_message,
            subsystem=current_failure['subsystem'],
            likely_cause=infer_likely_cause(error_type, error_message),
            fix_complexity=estimate_complexity(error_type, error_message)
        ))

    return failures


def extract_error_from_traceback(lines: List[str]) -> tuple:
    """Extract the final error type and message from traceback lines."""
    # Look for the last "E   AssertionError:" or similar line
    for line in reversed(lines):
        if line.startswith('E   '):
            # Parse "E   AssertionError: message" or "E   assert x == y"
            match = re.match(r'^E\s+([A-Za-z_][A-Za-z0-9_]*Error|assert\s.*):\s*(.*)$', line)
            if match:
                return match.group(1), match.group(2)
            # Handle plain assert lines
            if line.startswith('E   assert'):
                return 'AssertionError', line[4:].strip()
    return 'Unknown', 'Could not parse error'


def infer_likely_cause(error_type: str, error_message: str) -> str:
    """Infer the likely cause from error type and message."""
    msg_lower = error_message.lower()
    if 'has no attribute' in msg_lower or "'NoneType' has no" in msg_lower:
        return 'missing_attribute_initialization'
    if 'assert' in error_type.lower() or 'assert' in msg_lower:
        if 'expected' in msg_lower and 'actual' in msg_lower:
            return 'mock_assertion_mismatch'
        if '== ' in msg_lower:
            return 'value_mismatch'
        return 'assertion_failure'
    if 'import' in msg_lower or 'module' in msg_lower:
        return 'import_error'
    if 'timeout' in msg_lower:
        return 'timeout'
    if 'file' in msg_lower and ('not found' in msg_lower or 'exists' in msg_lower):
        return 'file_system_issue'
    return 'unknown'


def estimate_complexity(error_type: str, error_message: str) -> str:
    """Estimate fix complexity."""
    msg_lower = error_message.lower()
    cause = infer_likely_cause(error_type, error_message)

    if cause == 'missing_attribute_initialization':
        return 'low'  # Usually just add attr to __init__ or test setup
    if cause == 'mock_assertion_mismatch':
        return 'low'  # Update mock expected call
    if cause == 'value_mismatch' and 'expected' in msg_lower:
        return 'low'  # Update expected value
    if 'import' in msg_lower:
        return 'low'
    if 'timeout' in msg_lower:
        return 'medium'
    if 'assert' in error_type.lower():
        return 'medium'  # Need to investigate logic
    return 'high'


def generate_report(failures: List[Failure]) -> str:
    """Generate a structured diagnostic report."""
    # Group by subsystem
    by_subsystem = defaultdict(list)
    for f in failures:
        by_subsystem[f.subsystem].append(f)

    # Group by error type
    by_error_type = defaultdict(list)
    for f in failures:
        by_error_type[f.error_type].append(f)

    # Group by complexity
    by_complexity = defaultdict(list)
    for f in failures:
        by_complexity[f.fix_complexity].append(f)

    report = []
    report.append("=" * 80)
    report.append("HERMES TEST SUITE FAILURE CATALOG")
    report.append("=" * 80)
    report.append(f"Total failures: {len(failures)}")
    report.append("")

    # Summary by subsystem
    report.append("BY SUBSYSTEM:")
    report.append("-" * 40)
    for subsystem in sorted(by_subsystem.keys(), key=lambda s: -len(by_subsystem[s])):
        count = len(by_subsystem[subsystem])
        report.append(f"  {subsystem:30s} {count:3d} failures")
    report.append("")

    # Summary by error type
    report.append("BY ERROR TYPE:")
    report.append("-" * 40)
    for error_type in sorted(by_error_type.keys(), key=lambda e: -len(by_error_type[e])):
        count = len(by_error_type[error_type])
        report.append(f"  {error_type:30s} {count:3d} failures")
    report.append("")

    # Summary by complexity
    report.append("BY FIX COMPLEXITY:")
    report.append("-" * 40)
    for complexity in ['low', 'medium', 'high']:
        count = len(by_complexity[complexity])
        report.append(f"  {complexity:10s} {count:3d} failures")
    report.append("")

    # Detailed breakdown per subsystem
    report.append("=" * 80)
    report.append("DETAILED BREAKDOWN")
    report.append("=" * 80)

    for subsystem in sorted(by_subsystem.keys(), key=lambda s: -len(by_subsystem[s])):
        report.append("")
        report.append(f"--- {subsystem.upper()} ({len(by_subsystem[subsystem])} failures) ---")

        # Group by test file within subsystem
        by_file = defaultdict(list)
        for f in by_subsystem[subsystem]:
            by_file[f.test_file].append(f)

        for test_file in sorted(by_file.keys()):
            report.append(f"\n  File: {test_file}")
            for f in by_file[test_file]:
                report.append(f"    • {f.test_name}")
                report.append(f"      Error: {f.error_type}: {f.error_message[:80]}")
                report.append(f"      Cause: {f.likely_cause} | Complexity: {f.fix_complexity}")

    report.append("")
    report.append("=" * 80)
    report.append("RECOMMENDED FIX ORDER (low complexity first):")
    report.append("=" * 80)

    low_complexity = [f for f in failures if f.fix_complexity == 'low']
    for f in low_complexity:
        report.append(f"  [{f.subsystem}] {f.test_file}::{f.test_name}")
        report.append(f"    → {f.error_type}: {f.error_message[:60]}")

    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 catalog_failures.py /path/to/pytest_output.log")
        sys.exit(1)

    log_path = sys.argv[1]
    failures = parse_pytest_output(log_path)

    if not failures:
        print("No failures found in log file!")
        sys.exit(0)

    report = generate_report(failures)
    print(report)

    # Save report
    report_path = log_path.replace('.log', '_catalog.md')
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\n\nReport saved to: {report_path}")


if __name__ == '__main__':
    main()
