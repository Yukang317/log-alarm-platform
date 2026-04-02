#!/bin/sh
# 1-launch-vllm-inference.sh
# 启动 vLLM 官方推理服务（端口 8001）

echo "Starting vLLM Inference Service on port 8001.."

uv run vllm serve ../qwen25-3b \
    --host 0.0.0.0 \                      # 监听所有网络接口，允许远程访问
    --port 8001
    --enable-lora \
    --lora-modules my-lora=./finetuned_lora \  # 注册 LoRA 模块，命名为"my-lora"
    --max-model-len=4096 \
    --gpu-memory-utilization=0.90 \ 
    --max-num-seqa=32 \
    --block-size=16

echo "vLLM Inference Service started."


# 参数详解：
# --max-num-seqs=32: 
#   控制同一时间最多处理 32 个独立的请求序列
#   值越大并发越高，但显存占用也越大
#
# --block-size=16:
#   vLLM 使用 PagedAttention 技术管理 KV Cache
#   将连续序列分成固定大小的块（类似内存分页）
#   优点：减少显存碎片，提升并发能力