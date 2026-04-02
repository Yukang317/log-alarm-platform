#!/bin/sh
# 这里是老师的final，是单进程异步架构（FastAPI + AsyncLLMEngine 在同一进程）

uv run uvicorn vllm-service:app --host 0.0.0.0 --port 8000