#!/usr/bin/env python3
"""
Skill Content Scanner v0.1
Scans skill files for malicious patterns before loading.

Inspired by SkillFortify (arXiv:2603.00195) and the 341/2857 malicious skills
found on ClawHub (Koi Security audit, Feb 2026).

Checks for:
1. Network calls (data exfiltration risk)
2. File system access outside allowed dirs
3. API key / credential patterns
4. Shell injection patterns
5. Memory poisoning patterns (writing to agent memory/context)
6. Obfuscated code patterns

Usage: python3 skill_scanner.py [--scan-all] [--skill NAME]
"""
import re
import json
import sys
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path.home() / ".hermes" / "skills"
PLUGINS_DIR = Path.home() / ".hermes" / "plugins"

# Threat patterns
PATTERNS = {
    'network_exfil': {
        'severity': 'HIGH',
        'patterns': [
            r'requests\.(get|post|put|delete|patch)',
            r'urllib\.request',
            r'http\.client',
            r'socket\.connect',
            r'fetch\(',
            r'curl',
            r'wget',
            r'subprocess.*curl',
            r'subprocess.*wget',
        ]
    },
    'credential_theft': {
        'severity': 'CRITICAL',
        'patterns': [
            r'(?:api[_-]?key|secret|password|token)\s*=\s*["\'][A-Za-z0-9_\-]{8,}["\']',
            r'os\.environ\[\s*["\'](?:API_KEY|SECRET_KEY|PASSWORD|AUTH_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY)',
            r'(?:keyring|keychain)\s*\.\s*(?:get_password|set_password)',
            r'\bexfiltrat\w+\b',
        ]
    },
    'shell_injection': {
        'severity': 'HIGH',
        'patterns': [
            r'os\.system\(',
            r'subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True',
            r'eval\(',
            r'exec\(',
            r'__import__',
        ]
    },
    'memory_poisoning': {
        'severity': 'MEDIUM',
        'patterns': [
            r'memory\(.*action\s*=\s*"add"',
            r'write_file.*cerebrum',
            r'INSERT\s+INTO.*semantic_facts',
            r'sqlite3.*execute.*INSERT',
        ]
    },
    'file_system_escape': {
        'severity': 'HIGH',
        'patterns': [
            r'\.\./\.\.',
            r'/etc/passwd',
            r'/etc/shadow',
            r'/root/',
            r'rm\s+-rf\s+/',
            r'shutil\.rmtree',
        ]
    },
    'agent_behavior_mod': {
        'severity': 'MEDIUM',
        'patterns': [
            r'ignore.*previous.*instructions',
            r'you are now',
            r'new instructions',
            r'forget.*everything',
            r'system prompt',
        ]
    }
}

def scan_file(filepath):
    """Scan a single file for threats."""
    try:
        content = filepath.read_text(errors='ignore')
    except:
        return {'file': str(filepath), 'error': 'could not read', 'threats': []}
    
    findings = []
    
    for category, config in PATTERNS.items():
        for pattern in config['patterns']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Get line number
                line_num = content[:match.start()].count('\n') + 1
                line = content.split('\n')[line_num - 1].strip()
                findings.append({
                    'category': category,
                    'severity': config['severity'],
                    'pattern': pattern,
                    'line': line_num,
                    'context': line[:100],
                })
    
    return {
        'file': str(filepath),
        'threats': findings,
        'threat_count': len(findings),
        'max_severity': max([f['severity'] for f in findings], default='NONE'),
    }

def scan_all_skills():
    """Scan all skill and plugin files."""
    results = []
    
    # Scan skills
    for f in SKILLS_DIR.rglob('*.md'):
        results.append(scan_file(f))
    
    # Scan plugins
    for f in PLUGINS_DIR.rglob('*.py'):
        results.append(scan_file(f))
    
    return results

def print_report(results):
    """Print scan report."""
    total_files = len(results)
    files_with_threats = sum(1 for r in results if r['threat_count'] > 0)
    total_threats = sum(r['threat_count'] for r in results)
    
    print("=== SKILL/PLUGIN SECURITY SCAN ===")
    print(f"Files scanned: {total_files}")
    print(f"Files with threats: {files_with_threats}")
    print(f"Total threats: {total_threats}")
    
    # Severity breakdown
    severities = {}
    for r in results:
        for t in r['threats']:
            sev = t['severity']
            severities[sev] = severities.get(sev, 0) + 1
    
    if severities:
        print(f"\nSeverity breakdown:")
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if sev in severities:
                print(f"  {sev}: {severities[sev]}")
    
    # Print details for high/critical
    for r in sorted(results, key=lambda x: x['threat_count'], reverse=True):
        if r['threat_count'] == 0:
            continue
        
        high_threats = [t for t in r['threats'] if t['severity'] in ('CRITICAL', 'HIGH')]
        if high_threats:
            print(f"\n{r['file']}:")
            for t in high_threats:
                print(f"  [{t['severity']}] {t['category']} (line {t['line']}): {t['context'][:80]}")

if __name__ == '__main__':
    if '--scan-all' in sys.argv:
        results = scan_all_skills()
    else:
        # Quick scan of just skill files
        results = []
        for f in SKILLS_DIR.rglob('*.md'):
            results.append(scan_file(f))
    
    print_report(results)
