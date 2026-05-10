#!/usr/bin/env python3
"""
Autobrowse R191 Test Suite — 6 tests
Tests all 4 modules: tracer, analyzer, synthesizer, graduator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_tracer_imports():
    """Test 1: tracer module loads without errors"""
    import autobrowse_tracer
    assert hasattr(autobrowse_tracer, 'AutobrowseTracer'), "Missing AutobrowseTracer class"
    print("✓ test_tracer_imports")

def test_analyzer_imports():
    """Test 2: analyzer module loads without errors"""
    import autobrowse_analyzer
    assert hasattr(autobrowse_analyzer, 'AutobrowseAnalyzer'), "Missing AutobrowseAnalyzer class"
    print("✓ test_analyzer_imports")

def test_synthesizer_imports():
    """Test 3: synthesizer module loads without errors"""
    import autobrowse_synthesizer
    assert hasattr(autobrowse_synthesizer, 'AutobrowseSynthesizer'), "Missing AutobrowseSynthesizer class"
    print("✓ test_synthesizer_imports")

def test_graduator_imports():
    """Test 4: graduator module loads without errors"""
    import autobrowse_graduator
    assert hasattr(autobrowse_graduator, 'AutobrowseGraduator'), "Missing AutobrowseGraduator class"
    print("✓ test_graduator_imports")

def test_tracer_instantiate():
    """Test 5: tracer can be instantiated"""
    import autobrowse_tracer
    tracer = autobrowse_tracer.AutobrowseTracer()
    assert tracer is not None
    print("✓ test_tracer_instantiate")

def test_analyzer_instantiate():
    """Test 6: analyzer can be instantiated"""
    import autobrowse_analyzer
    analyzer = autobrowse_analyzer.AutobrowseAnalyzer()
    assert analyzer is not None
    print("✓ test_analyzer_instantiate")

if __name__ == '__main__':
    tests = [
        test_tracer_imports,
        test_analyzer_imports,
        test_synthesizer_imports,
        test_graduator_imports,
        test_tracer_instantiate,
        test_analyzer_instantiate,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n=== RESULTS: {passed}/{len(tests)} passed ===")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    else:
        print(f"{failed} tests failed")
        sys.exit(1)
