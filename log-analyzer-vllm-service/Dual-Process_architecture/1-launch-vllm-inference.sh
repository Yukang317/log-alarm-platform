#!/bin/sh
# 1-launch-vllm-inference.sh
# 启动 vLLM 官方推理服务（端口 8001）

echo "Starting vLLM Inference Service on port 8001.."

# 监听所有网络接口，允许远程访问
# 注册 LoRA 模块，命名为"my-lora"
uv run vllm serve /root/autodl-tmp/code/qwen25-3b \
    --host 0.0.0.0 \
    --port 8001 \
    --enable-lora \
    --lora-modules my-lora=/root/autodl-tmp/code/log-analyzer-via-llm/finetuned_lora \
    --max-model-len=2048 \
    --max_num_batched_tokens=65536 \
    --gpu-memory-utilization=0.85 \
    --max-num-seqs=128 \
    --block-size=16

echo "vLLM Inference Service started."


# 参数详解：
# --max-num-seqs=64: 
#   控制同一时间最多处理 64 个独立的请求序列
#   值越大并发越高，但显存占用也越大
#
# --block-size=16:
#   vLLM 使用 PagedAttention 技术管理 KV Cache
#   将连续序列分成固定大小的块（类似内存分页）
#   优点：减少显存碎片，提升并发能力