#!/bin/sh
# 5-benchmark-dual-process.sh
# 压测双进程架构性能

echo "Benchmarking Dual Process Architecture..."

# 安装 ab 工具
apt update && apt install apache2-utils -y

# 压测业务服务
# 超时时间 120 秒（防止慢请求卡死
# 从文件读取请求体数据
echo ""
echo "[Load Test] Business Service (/analyze endpoint)"
echo "Requests: 100, Concurrency: 10"
ab -n 100 -c 10 \
    -T 'text/plain' \
    -l \
    -s 120 \
    -p ../request.data \
    http://localhost:8000/analyze

echo ""
echo "Benchmark completed!"