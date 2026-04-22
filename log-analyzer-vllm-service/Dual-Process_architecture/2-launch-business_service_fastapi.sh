#!/bin/sh
# 2-launch-business_service_fastapi.sh
# 启动 FastAPI 业务服务（端口 8000）

echo "Starting FastAPI Business Service on port 8000..."

uv run uvicorn business_service_fastapi:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4


echo "FastAPI Business Service started."


# 参数详解：
# --workers 4:
#   Uvicorn 使用多进程模式运行 FastAPI 应用
#   每个 worker 是一个独立的 Python 进程
#   4 个进程可以同时处理 4 组请求，提升吞吐量
#   生产环境建议设置为 CPU 核心数的 2-4 倍
#
# --reload:
#   开发调试神器！检测到代码文件变化时自动重启服务
#   无需手动 kill 再启动，实时看到代码修改效果
#   ⚠️ 注意：生产环境请关闭此选项（有性能开销）