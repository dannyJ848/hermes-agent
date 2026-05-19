#!/usr/bin/env python3
"""
Autonomous Hermes Agent Runner for DGX — Screen-based (no daemon)

This script runs Hermes Agent autonomously in a loop, cycling through predefined tasks.
Designed to run inside a screen/tmux session for persistence without systemd.

Usage:
    screen -dmS hermes_auto bash -c 'cd /data/SpecForge/hermes-agent && \
        PYTHONPATH=/data/SpecForge/hermes-agent \
        /data/SpecForge/hermes-agent/venv/bin/python3 \
        /path/to/autonomous_runner_screen.py > /tmp/hermes_auto_out.txt 2>&1'

    # Attach to watch
    screen -r hermes_auto
    
    # Detach (Ctrl+A then D)
    
    # Stop
    screen -S hermes_auto -X quit
"""

import sys
import os
import importlib.util
import time
import json
import re
import subprocess
from datetime import datetime

# === Module Shadowing Fix ===
# Pre-import plugins package before hermes_cli.plugins can shadow it
project_root = '/data/SpecForge/hermes-agent'
sys.path.insert(0, project_root)

gateway_init = os.path.join(project_root, 'gateway', '__init__.py')
if os.path.exists(gateway_init) and 'gateway' not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        'gateway', gateway_init,
        submodule_search_locations=[os.path.join(project_root, 'gateway')]
    )
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules['gateway'] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)

plugins_init = os.path.join(project_root, 'plugins', '__init__.py')
if os.path.exists(plugins_init) and 'plugins' not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        'plugins', plugins_init,
        submodule_search_locations=[os.path.join(project_root, 'plugins')]
    )
    plugins_pkg = importlib.util.module_from_spec(spec)
    sys.modules['plugins'] = plugins_pkg
    spec.loader.exec_module(plugins_pkg)

from run_agent import main

# === Configuration ===
AUTONOMOUS_TASKS = [
    'Check system status and report any issues',
    'Review recent logs for errors or warnings',
    'Update knowledge base with new findings',
    'Run self-diagnostic on all subsystems',
    'Check for updates or improvements needed',
    'Monitor DGX GPU utilization and temperature',
    'Verify vLLM service health and performance',
    'Check disk space and cleanup if needed',
    'Review and optimize configuration files',
    'Run security audit on exposed services',
]

MODEL = '/data/models/Qwen3.6-27B-Uncensored'
BASE_URL = 'http://localhost:8000/v1'
API_KEY = 'not-needed'
MAX_TURNS = 10
TASK_INTERVAL = 30  # seconds between tasks

# === Text-based Tool Execution (for Qwen XML format) ===

def parse_tool_calls(text):
    """Parse Qwen XML tool calls from model output."""
    tool_calls = []
    tool_pattern = r'<tool_call>\s*<function=(\w+)>\s*(.*?)</function>\s*</tool_call>'
    matches = re.findall(tool_pattern, text, re.DOTALL)
    
    for func_name, params_text in matches:
        params = {}
        param_pattern = r'<parameter=(\w+)>\s*(.*?)\s*</parameter>'
        param_matches = re.findall(param_pattern, params_text, re.DOTALL)
        for param_name, param_value in param_matches:
            params[param_name] = param_value.strip()
        
        tool_calls.append({'name': func_name, 'arguments': params})
    
    return tool_calls

def execute_tool(tool_name, arguments):
    """Execute a tool manually."""
    print(f"  [TOOL] Executing: {tool_name}({arguments})")
    
    if tool_name == 'terminal':
        cmd = arguments.get('command', '')
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            print(f"  [TOOL] Output: {output[:200]}...")
            return output
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == 'web_search':
        query = arguments.get('query', '')
        try:
            result = subprocess.run(
                f"curl -s 'https://duckduckgo.com/html/?q={query}' | grep -oP 'class=\"result__a\" href=\"\K[^\"]*' | head -5",
                shell=True, capture_output=True, text=True, timeout=15
            )
            return result.stdout or "No results found"
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == 'read_file':
        path = arguments.get('path', '')
        try:
            with open(path, 'r') as f:
                return f.read()[:1000]
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == 'write_file':
        path = arguments.get('path', '')
        content = arguments.get('content', '')
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"File written: {path}"
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == 'execute_code':
        code = arguments.get('code', '')
        try:
            result = subprocess.run(
                f"python3 -c '{code}'",
                shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {e}"
    
    else:
        return f"Unknown tool: {tool_name}"

# === Task Management ===

def get_next_task():
    """Get next task from rotating list, with optional custom task queue override."""
    # Check for custom tasks first
    custom_queue = '/tmp/hermes_custom_tasks.jsonl'
    if os.path.exists(custom_queue):
        with open(custom_queue, 'r') as f:
            lines = f.readlines()
        if lines:
            task = json.loads(lines[0])
            with open(custom_queue, 'w') as f:
                f.writelines(lines[1:])
            return task.get('query', task.get('task', 'Unknown task'))
    
    # Fall back to rotating autonomous tasks
    task_file = '/tmp/hermes_autonomous_state.json'
    if os.path.exists(task_file):
        with open(task_file, 'r') as f:
            state = json.load(f)
        idx = state.get('task_index', 0) % len(AUTONOMOUS_TASKS)
    else:
        idx = 0
    
    task = AUTONOMOUS_TASKS[idx]
    with open(task_file, 'w') as f:
        json.dump({'task_index': (idx + 1) % len(AUTONOMOUS_TASKS)}, f)
    
    return task

# === Main Loop ===

def main_loop():
    print(f'[{datetime.now()}] AUTONOMOUS HERMES STARTED')
    print(f'[{datetime.now()}] Model: {MODEL}')
    print(f'[{datetime.now()}] Provider: local-dgx')
    print(f'[{datetime.now()}] Mode: Fully autonomous with text-based tool execution')
    print('=' * 60)
    
    iteration = 0
    while True:
        iteration += 1
        try:
            task = get_next_task()
            print(f'\n[{datetime.now()}] TASK {iteration}: {task}')
            
            # Run agent (disable native tool calling, use text-based)
            result = main(
                query=task,
                model=MODEL,
                api_key=API_KEY,
                base_url=BASE_URL,
                max_turns=MAX_TURNS,
                verbose=True,
                enabled_toolsets=''  # Disable native tool calling
            )
            
            # Parse and execute any tool calls in the response
            if result and result.get('final_response'):
                response_text = result['final_response']
                print(f"\n[{datetime.now()}] Response: {response_text[:200]}...")
                
                tool_calls = parse_tool_calls(response_text)
                if tool_calls:
                    print(f"[{datetime.now()}] Found {len(tool_calls)} tool calls to execute")
                    for tc in tool_calls:
                        tool_result = execute_tool(tc['name'], tc['arguments'])
                        print(f"  [TOOL] Result: {tool_result[:200]}")
                else:
                    print(f"[{datetime.now()}] No tool calls found in response")
            
            print(f'[{datetime.now()}] Task completed')
            print(f'[{datetime.now()}] Waiting {TASK_INTERVAL}s before next task...')
            time.sleep(TASK_INTERVAL)
            
        except KeyboardInterrupt:
            print(f'\n[{datetime.now()}] Stopped by user')
            break
        except Exception as e:
            print(f'[{datetime.now()}] Error: {e}')
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == '__main__':
    main_loop()
