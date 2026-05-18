#!/usr/bin/env python3
"""Verify DGX port is complete and functional."""
import subprocess, sys, os

def run(cmd, host=None):
    if host:
        cmd = ['ssh', f'djg6228@{host}', cmd]
    else:
        cmd = cmd.split()
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def main():
    host = 'spark-85e8.local'
    errors = []
    
    # Check commit sync
    out, _, _ = run('cd /data/SpecForge/hermes-agent && git log --oneline -1', host)
    dgx_commit = out.split()[0]
    out, _, _ = run('git log --oneline -1')
    mac_commit = out.split()[0]
    print(f"MacBook: {mac_commit}")
    print(f"DGX:     {dgx_commit}")
    if dgx_commit != mac_commit:
        errors.append(f"Commit mismatch: {mac_commit} vs {dgx_commit}")
    
    # Check skills
    out, _, _ = run('find ~/.hermes/skills/ -name SKILL.md -maxdepth 3 | wc -l', host)
    dgx_skills = int(out) if out.isdigit() else 0
    out, _, _ = run('find skills/ -name SKILL.md -maxdepth 3 | wc -l')
    mac_skills = int(out) if out.isdigit() else 0
    print(f"Skills: MacBook={mac_skills}, DGX={dgx_skills}")
    if abs(dgx_skills - mac_skills) > 5:
        errors.append(f"Skill count mismatch: {mac_skills} vs {dgx_skills}")
    
    # Check cognitive files
    for f in ['agent/cognitive_orchestrator.py', 'agent/iteration_engine.py']:
        out, _, rc = run(f'test -f /data/SpecForge/hermes-agent/{f} && echo OK', host)
        if 'OK' not in out:
            errors.append(f"Missing on DGX: {f}")
    
    # Check hermes binary
    out, _, rc = run('which hermes', host)
    if rc != 0:
        errors.append("hermes not in PATH on DGX")
    
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("\n✓ DGX port verified")
        sys.exit(0)

if __name__ == '__main__':
    main()
