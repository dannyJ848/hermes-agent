#!/usr/bin/env python3
"""
Smoke test for Hermes learning apparatus brain modules.
Run from hermes_cli/ directory after deploying new cognitive modules.

This script verifies:
1. All brain modules import cleanly
2. Each module's core function works
3. HermesBrain integration wiring is correct
4. Schema alignment with existing cerebrum_memory.db
5. Loop guard, self-healing, intent verification all operational

Usage: cd hermes_cli && python3 references/may6-2026-smoke-test-script.py
"""

import sys
sys.path.insert(0, '.')

def test_module_imports():
    """Phase 1: Verify all modules import."""
    modules = [
        'loop_guard', 'self_healing_dispatch', 'failure_post_mortem',
        'intent_verifier', 'proactive_tip_injector', 'token_budget_tracker',
        'confidence_calibrator', 'context_updater', 'hermes_brain'
    ]
    results = {}
    for mod in modules:
        try:
            __import__(mod)
            results[mod] = 'OK'
        except Exception as e:
            results[mod] = f'FAIL: {str(e)[:60]}'
    return results

def test_loop_guard():
    """Phase 2: Loop detection fires at threshold."""
    from loop_guard import LoopGuard
    lg = LoopGuard()
    results = []
    for i in range(5):
        result = lg.check_loop('web_search', {'query': 'test'}, 'session_1')
        results.append((i+1, result['is_loop'], result['count']))
    # Should detect loop at 4th repeat
    assert results[3][1] == True, "Loop guard should detect at 4th repeat"
    return results

def test_self_healing():
    """Phase 3: Patch failure routes to write_file."""
    from self_healing_dispatch import SelfHealingDispatch
    sh = SelfHealingDispatch()
    result = sh.dispatch_with_fallback('patch', {'path': 'test.py'})
    assert result['success'] == True
    assert result['tool_used'] == 'write_file'
    return result

def test_intent_verifier():
    """Phase 4: Intent recording and verification."""
    from intent_verifier import IntentVerifier
    iv = IntentVerifier()
    check_id = iv.record_intent('deploy app', 'app is live')
    result = iv.verify_outcome(check_id, 'app deployed successfully')
    assert 'match_score' in result
    assert 'needs_clarification' in result
    return result

def test_token_budget():
    """Phase 5: Budget tracking with schema-aligned DB."""
    from token_budget_tracker import TokenBudgetTracker
    tbt = TokenBudgetTracker()
    result = tbt.get_budget_status('current_session')
    assert result['status'] == 'OK'
    assert result['budget'] == 1000000
    return result

def test_confidence():
    """Phase 6: Confidence calibration."""
    from confidence_calibrator import ConfidenceCalibrator
    cc = ConfidenceCalibrator()
    result = cc.assess_confidence('deploy to production', 'inferred')
    assert 'confidence' in result
    assert 'should_verify' in result
    return result

def test_hermes_brain():
    """Phase 7: Full integration via HermesBrain."""
    from hermes_brain import HermesBrain
    brain = HermesBrain()
    
    # Pre-flight
    pre = brain.before_tool_call('web_search', {'query': 'test'}, 'session_1')
    assert pre['action'] in ('PROCEED', 'BLOCK')
    
    # Post-flight success
    post_ok = brain.after_tool_call('web_search', {'query': 'test'}, 'results found')
    assert post_ok['status'] == 'OK'
    
    # Post-flight failure
    post_err = brain.after_tool_call('patch', {'path': 'test.py'}, None, 'old_string not found')
    assert post_err['healed'] == True
    
    # Task lifecycle
    start = brain.on_task_start('deploy to production')
    assert 'tips' in start
    assert 'confidence' in start
    
    return {'pre': pre, 'post_ok': post_ok, 'post_err': post_err, 'start': start}

def test_schema_alignment():
    """Phase 8: Verify DB schema matches module expectations."""
    import sqlite3
    import os
    
    cerebrum = os.path.expanduser('~/.hermes/cerebrum_memory.db')
    if not os.path.exists(cerebrum):
        return {'status': 'SKIP', 'reason': 'cerebrum_memory.db not found'}
    
    conn = sqlite3.connect(cerebrum)
    c = conn.cursor()
    
    # Check token_usage table (used by token_budget_tracker)
    c.execute("PRAGMA table_info(token_usage)")
    columns = [col[1] for col in c.fetchall()]
    conn.close()
    
    expected = {'tokens_in', 'tokens_out', 'created_at', 'session_id'}
    missing = expected - set(columns)
    
    return {
        'status': 'OK' if not missing else 'MISMATCH',
        'columns': columns,
        'missing': list(missing)
    }

def run_all():
    """Execute full smoke test suite."""
    print("=" * 60)
    print("HERMES BRAIN MODULES - SMOKE TEST")
    print("=" * 60)
    
    phases = [
        ("Module Imports", test_module_imports),
        ("Loop Guard", test_loop_guard),
        ("Self-Healing", test_self_healing),
        ("Intent Verifier", test_intent_verifier),
        ("Token Budget", test_token_budget),
        ("Confidence", test_confidence),
        ("Hermes Brain", test_hermes_brain),
        ("Schema Alignment", test_schema_alignment),
    ]
    
    all_pass = True
    for name, test_fn in phases:
        print(f"\n[{name}]")
        try:
            result = test_fn()
            if isinstance(result, dict) and result.get('status') == 'MISMATCH':
                print(f"  [WARN] Schema mismatch: {result['missing']}")
                all_pass = False
            else:
                print(f"  [OK] {result}")
        except Exception as e:
            print(f"  [FAIL] {str(e)[:80]}")
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("ALL PHASES PASSED")
    else:
        print("SOME PHASES FAILED — review output above")
    print("=" * 60)
    return all_pass

if __name__ == '__main__':
    import sys
    success = run_all()
    sys.exit(0 if success else 1)
