# 双进程架构 - FFmpeg 日志智能分析系统

基于 **vLLM 官方服务** + **自定义 FastAPI** 的双进程架构实现。

---

## 🏗️ 架构设计

```
┌─────────────────────┐         HTTP          ┌─────────────────────┐
│  FastAPI 业务服务    │ ←──────────────────→  │  vLLM 推理服务       │
│  (Port 8000)        │      Port 8001        │  (Port 8001)        │
│                     │                       │                     │
│  - 接收用户请求      │                       │  - AI 模型推理       │
│  - 调用 vLLM API     │                       │  - GPU 计算          │
│  - 飞书告警通知      │                       │  - LoRA 微调支持     │
│  - 重试机制          │                       │                     │
└─────────────────────┘                       └─────────────────────┘
```

**核心优势**：资源隔离、故障隔离、独立扩展、生产就绪

---

## 🚀 快速开始

### 前置条件

- ✅ Python 3.10+ 和 UV 包管理器
- ✅ NVIDIA GPU 和 CUDA 驱动
- ✅ 已准备模型：`../qwen25-3b` 和 `./finetuned_lora`

### 一键启动

```bash
cd Dual-Process_architecture
./3-start-all.sh
```

**预期输出**：
```
========================================
  Starting Dual-Process Architecture... 
========================================
[1/5] Cleaning old processes...
[2/5] Starting vLLM Inference Service (port 8001)...
  vLLM PID: 12345
[3/5] Waiting for vLLM to be ready...
  ✓ vLLM service is ready
[4/5] Starting FastAPI Business Service (port 8000)...
  FastAPI PID: 12346
  ✓ FastAPI service is ready
[5/5] Dual Process Architecture Started Successfully!
========================================
  vLLM Inference:  http://localhost:8001 (PID: 12345)
  Business API:    http://localhost:8000 (PID: 12346)
========================================
```

### 功能验证

```bash
./4-validation-dual-process.sh
```

### 停止服务

```bash
./6-stop-all.sh
```

---

## 📁 文件说明

### 核心代码

| 文件 | 说明 | 端口 |
|------|------|------|
| `business_service_fastapi.py` | FastAPI 业务服务（唯一需要编写的 Python 代码） | 8000 |

### 启动脚本

| 文件 | 功能 |
|------|------|
| `1-launch-vllm-inference.sh` | 启动 vLLM 推理服务 |
| `2-launch-business_service_fastapi.sh` | 启动 FastAPI 业务服务 |
| `3-start-all.sh` | 一键启动双进程（含健康检查） |
| `6-stop-all.sh` | 停止所有服务 |

### 测试脚本

| 文件 | 功能 |
|------|------|
| `4-validation-dual-process.sh` | 功能验证（成功 + 失败案例测试） |
| `5-benchmark-dual-process.sh` | 性能压测（Apache Bench） |

---

## 🔧 配置说明

### vLLM 关键参数（`1-launch-vllm-inference.sh`）

```bash
--max-num-seqs=32              # 最大并发序列数
--gpu-memory-utilization=0.90  # GPU 显存使用率 90%
--max-model-len=4096           # 最大上下文长度
--block-size=16                # PagedAttention 块大小
```

### FastAPI 关键参数（`2-launch-business_service_fastapi.sh`）

```bash
--workers 4    # 工作进程数（建议 CPU 核心数的 2-4 倍）
--reload       # 热重载（开发环境用，生产环境请移除）
```

---

## 🧪 测试示例

### 健康检查

```bash
curl http://localhost:8000/health
# 返回：{"status":"healthy","architecture":"dual-process","service":"business-api"}
```

### 分析 FFmpeg 日志

```bash
curl -X POST \
  -d "你的 FFmpeg 日志内容" \
  http://localhost:8000/analyze | jq
```

### 测试成功案例

```bash
curl -X POST \
  -d "ffmpeg version N-random-g897d21b1b44 shared... PSNR Y:46.39..." \
  http://localhost:8000/analyze | jq
```

### 测试失败案例（会触发飞书告警）

```bash
curl -X POST \
  -d "ffmpeg version... Error while opening encoder..." \
  http://localhost:8000/analyze | jq
```

---

## ❓ 常见问题

### Q1: 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8000
lsof -i :8001

# 停止所有服务
./6-stop-all.sh
```

### Q2: vLLM 显存不足

降低显存使用率（编辑 `1-launch-vllm-inference.sh`）：
```bash
--gpu-memory-utilization=0.80  # 从 0.90 降至 0.80
```

### Q3: 查看运行日志

```bash
# 实时查看日志
tail -f vllm_inference.log
tail -f business_service.log
```

### Q4: 服务无法访问

```bash
# 检查 vLLM 是否运行
curl http://localhost:8001/health

# 检查 FastAPI 是否运行
curl http://localhost:8000/health

# 检查进程状态
ps aux | grep -E "vllm|uvicorn"
```

---

## 📊 性能优化建议

### 1. 提升并发能力

```bash
# 增加 vLLM 并发序列数（需要更多显存）
--max-num-seqs=64  # 默认 32

# 提高 GPU 显存利用率
--gpu-memory-utilization=0.95
```

### 2. 增加 FastAPI 工作进程

```bash
# 根据 CPU 核心数调整
--workers 8  # 默认 4
```

### 3. 延长超时时间

对于长文本分析，在 `business_service_fastapi.py` 中：
```python
async with httpx.AsyncClient(timeout=120.0) as client:  # 默认 60 秒
```

---

## 🔍 调试技巧

### 手动启动单个服务

```bash
# 只启动 vLLM
./1-launch-vllm-inference.sh

# 只启动 FastAPI
./2-launch-business_service_fastapi.sh
```

### 检查 GPU 状态

```bash
nvidia-smi
# 查看 GPU 利用率、显存占用、温度等
```

### 测试 vLLM 直接推理

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-lora",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | jq
```

---

## 📈 下一步

- [ ] 添加 Prometheus + Grafana 监控
- [ ] 集成 Kubernetes 部署
- [ ] 实现自动扩缩容（HPA）
- [ ] 添加 Redis 缓存层
- [ ] 支持多模型动态切换

---

## 📞 技术支持

**检查顺序**：
1. 查看日志文件（`*.log`）
2. 运行验证脚本（`./4-validation-dual-process.sh`）
3. 检查 GPU 状态（`nvidia-smi`）
4. 查阅 vLLM 官方文档：https://docs.vllm.ai

---

**🎉 双进程架构搭建完成！**
