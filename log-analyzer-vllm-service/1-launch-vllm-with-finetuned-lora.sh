#!/bin/sh
# 用vllm来验证我们的项目结果 - 监听所有ip，只用一个Lora（本地），模型最长上下文
# 给微调的目录起名字叫my-lora

uv run vllm serve ../qwen25-3b \
    --host 0.0.0.0 \
    --port 8000 \
    --enable-lora \
    --lora-moudles my-lora=./finetuned_lora \
    --max-model-len=4k


