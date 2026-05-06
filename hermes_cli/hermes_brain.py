#!/usr/bin/env python3
# Master Integrator
# Wires all self-improvement systems together

import sys
sys.path.insert(0, '/Users/dannygomez/hermes-agent/hermes_cli')

from loop_guard import LoopGuard
from self_healing_dispatch import SelfHealingDispatch
from failure_post_mortem import FailurePostMortem
from intent_verifier import IntentVerifier
from proactive_tip_injector import ProactiveTipInjector
from token_budget_tracker import TokenBudgetTracker
from confidence_calibrator import ConfidenceCalibrator

class HermesBrain:
    """Unified self-improvement brain."""
    
    def __init__(self):
        self.loop_guard = LoopGuard()
        self.healer = SelfHealingDispatch()
        self.mortem = FailurePostMortem()
        self.verifier = IntentVerifier()
        self.injector = ProactiveTipInjector()
        self.token_tracker = TokenBudgetTracker()
        self.confidence = ConfidenceCalibrator()
    
    def before_tool_call(self, tool_name, args, session_id):
        """Pre-flight checks."""
        # Check for loops
        loop_check = self.loop_guard.check_loop(tool_name, args, session_id)
        if loop_check['is_loop']:
            return {
                'action': 'BLOCK',
                'reason': f'Loop detected ({loop_check["count"]} repeats)',
                'alternative': loop_check['recommendation']
            }
        
        return {'action': 'PROCEED'}
    
    def after_tool_call(self, tool_name, args, result, error=None):
        """Post-flight analysis."""
        if error:
            # Analyze failure
            analysis = self.mortem.analyze(tool_name, str(error))
            
            # Try healing
            healed = self.healer.dispatch_with_fallback(tool_name, args)
            
            return {
                'original_error': error,
                'analysis': analysis,
                'healed': healed['success'],
                'lesson': analysis['fix']
            }
        
        return {'status': 'OK'}
    
    def on_task_start(self, task_description):
        """Task initialization."""
        # Get relevant tips
        tips = self.injector.get_relevant_tips(task_description)
        
        # Check confidence
        conf = self.confidence.assess_confidence(task_description, 'inferred')
        
        return {
            'tips': tips,
            'confidence': conf,
            'should_verify': conf['should_verify']
        }
    
    def on_task_end(self, task_id, expected, actual):
        """Task completion."""
        # Verify intent
        result = self.verifier.verify_outcome(task_id, actual)
        
        # Check budget
        budget = self.token_tracker.get_budget_status('current_session')
        
        return {
            'intent_match': result,
            'budget_status': budget
        }

if __name__ == '__main__':
    brain = HermesBrain()
    print("Hermes Brain initialized with all self-improvement systems")
    print("Systems: loop_guard, healer, mortem, verifier, injector, token_tracker, confidence")
