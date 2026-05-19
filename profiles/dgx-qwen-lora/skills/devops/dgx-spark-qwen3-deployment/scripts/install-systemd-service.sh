#!/bin/bash
# vLLM DFlash systemd service deploy script
# Run on DGX Spark to install auto-start service

set -e

cat > /tmp/vllm-dflash.service << 'EOF'
[Unit]
Description=vLLM DFlash Inference Server
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e VLLM_LOGGING_LEVEL=INFO \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":16}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
ExecStop=/usr/bin/docker stop -t 30 vllm-merged
ExecStopPost=/usr/bin/docker rm -f vllm-merged

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/vllm-dflash.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm-dflash.service

echo "vLLM DFlash systemd service installed."
echo "Status: sudo systemctl status vllm-dflash.service"
echo "Start:  sudo systemctl start vllm-dflash.service"
echo "Stop:   sudo systemctl stop vllm-dflash.service"
