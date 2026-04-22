#!/bin/sh
# 3-start-all.sh
# 一键启动双进程架构

echo "========================================"
echo "  Starting Dual-Process Architecture... "
echo "========================================"

cd "$(dirname "$0")"


# 清理旧进程
echo "[1/5] Cleaning old processes..."
pkill -f "vllm serve.*8001" 2>/dev/null || true             
pkill -f "uvicorn.*business_service" 2>/dev/null || true     
sleep 2


# 启动 vLLM 推理服务
echo "[2/5] Starting vLLM Inference Service (port 8001)..."
nohup sh 1-launch-vllm-inference.sh > vllm_inference.log 2>&1 & 
VLLM_PID=$!                                 # 获取刚启动进程的 PID（进程 ID）
echo "  vLLM PID: $VLLM_PID"                # 打印 PID，方便后续管理和调试

# 等待 vLLM 服务就绪
echo "[3/5] Waiting for vLLM to be ready..."
MAX_RETRIES=120          # 最多等待 120 秒（120 次 × 1 秒）
RETRY_COUNT=0

# 循环检查vllm服务是否启动成功
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s --fail http://localhost:8001/health > /dev/null 2>&1; then
        echo "  ✓ vLLM service is ready (took ${RETRY_COUNT}s)"
        break
    fi
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

# 超时未就绪则报错退出
if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "  ✗ vLLM service failed to start within ${MAX_RETRIES}s. Check vllm_inference.log"
    exit 1
fi

# 启动 FastAPI 业务服务
echo "[4/5] Starting FastAPI Business Service (port 8000)..."
nohup sh 2-launch-business_service_fastapi.sh > business_service.log 2>&1 &
BUSINESS_PID=$!                                 # 获取 FastAPI 进程 PID
echo "  FastAPI PID: $BUSINESS_PID"             # 打印 PID


# 等待 FastAPI 服务就绪
sleep 5

# 验证 FastAPI 是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then      
    echo "  ✓ FastAPI service is ready"
else
    echo "  ✗ FastAPI service failed to start. Check business_service.log"
    exit 1
fi


# 显示状态
echo ""
echo "[5/5] Dual Process Architecture Started Successfully!"
echo "========================================"
echo "  vLLM Inference:  http://localhost:8001 (PID: $VLLM_PID)"     
echo "  Business API:    http://localhost:8000 (PID: $BUSINESS_PID)" 
echo "========================================"
echo ""
echo "To stop services:"
echo "  kill $VLLM_PID $BUSINESS_PID"       # 使用 kill 命令终止指定 PID 的进程
echo "  # or run: ./stop-all.sh"            # 或者运行 stop-all.sh 脚本统一停止
