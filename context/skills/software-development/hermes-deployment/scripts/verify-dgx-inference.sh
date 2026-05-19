#!/bin/bash
# Verify DGX inference deployment health
# Usage: bash verify-dgx-inference.sh [DGX_IP]

DGX_IP="${1:-10.0.0.171}"
VLLM_PORT="${2:-8000}"

echo "=== DGX Inference Verification ==="
echo "Target: http://${DGX_IP}:${VLLM_PORT}"
echo ""

# 1. Check vLLM model list
echo "[1/5] Checking vLLM model list..."
MODELS=$(curl -s "http://${DGX_IP}:${VLLM_PORT}/v1/models" 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$MODELS" ]; then
    echo "  ✓ vLLM responding"
    echo "  Models: $(echo "$MODELS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(', '.join([m['id'] for m in d.get('data',[])]))" 2>/dev/null)"
else
    echo "  ✗ vLLM not responding"
    exit 1
fi

# 2. Check merged-lora model
echo ""
echo "[2/5] Checking merged-lora model..."
HAS_MERGED=$(echo "$MODELS" | python3 -c "import sys,json; d=json.load(sys.stdin); ids=[m['id'] for m in d.get('data',[])]; print('merged-lora' in ids)" 2>/dev/null)
if [ "$HAS_MERGED" = "True" ]; then
    echo "  ✓ merged-lora model available"
else
    echo "  ✗ merged-lora model NOT found"
fi

# 3. Test chat completion
echo ""
echo "[3/5] Testing chat completion..."
CHAT_RESP=$(curl -s "http://${DGX_IP}:${VLLM_PORT}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 5, "temperature": 0.1}' 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$CHAT_RESP" ]; then
    CONTENT=$(echo "$CHAT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','no-content'))" 2>/dev/null)
    echo "  ✓ Chat working (response: '$CONTENT')"
else
    echo "  ✗ Chat completion failed"
fi

# 4. Test tool calling
echo ""
echo "[4/5] Testing tool calling..."
TOOL_RESP=$(curl -s "http://${DGX_IP}:${VLLM_PORT}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Search for recent AI news"}], "tools": [{"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}], "tool_choice": "auto", "max_tokens": 200}' 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$TOOL_RESP" ]; then
    HAS_TOOL=$(echo "$TOOL_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); tc=d.get('choices',[{}])[0].get('message',{}).get('tool_calls',[]); print(len(tc) > 0)" 2>/dev/null)
    if [ "$HAS_TOOL" = "True" ]; then
        echo "  ✓ Tool calling working"
    else
        echo "  ⚠ No tool calls in response (may need more tokens)"
    fi
else
    echo "  ✗ Tool calling test failed"
fi

# 5. Check Hermes config
echo ""
echo "[5/5] Checking Hermes config..."
if [ -f ~/.hermes/config.yaml ]; then
    CONTEXT_LEN=$(grep "context_length:" ~/.hermes/config.yaml | head -1 | awk '{print $2}')
    echo "  ✓ Hermes config found"
    echo "  Context length: $CONTEXT_LEN"
    
    HAS_SPARK=$(grep -A5 "spark-bf16:" ~/.hermes/config.yaml 2>/dev/null | grep "api:" | head -1)
    if [ -n "$HAS_SPARK" ]; then
        echo "  ✓ spark-bf16 provider configured"
    else
        echo "  ⚠ spark-bf16 provider not found"
    fi
else
    echo "  ✗ Hermes config not found"
fi

echo ""
echo "=== Verification Complete ==="
