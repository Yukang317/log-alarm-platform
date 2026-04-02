#!/bin/sh
# stop-all.sh
# 停止所有双进程服务


echo "Stopping all services..."

pkill -f "vllm serve.*8001"                 
pkill -f "uvicorn.*business_service"        

echo "All services stopped."