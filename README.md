# Log Analyzer VLLM Service

基于 vLLM + LoRA 微调的 FFmpeg 转码日志智能分析服务。

# 项目演示

### 1. vLLM和FastAPI启动

```bash
cd log-analyzer-vllm-service/Dual-Process\_architecture

# 一键启动
./3-start-all.sh

```

**输出内容：**

```Shell
========================================
  Starting Dual-Process Architecture... 
========================================
[1/5] Cleaning old processes...
[2/5] Starting vLLM Inference Service (port 8001)...
  vLLM PID: 45295
[3/5] Waiting for vLLM to be ready...
  ✓ vLLM service is ready (took 36s)
[4/5] Starting FastAPI Business Service (port 8000)...
  FastAPI PID: 46881
  ✓ FastAPI service is ready

[5/5] Dual Process Architecture Started Successfully!
========================================
  vLLM Inference:  http://localhost:8001 (PID: 45295)
  Business API:    http://localhost:8000 (PID: 46881)
========================================
```

<br />

### 2. 成功和失败的案例验证

```Shell
sh 4-validation-dual-process.sh 
```

**结果（截取部分）：**

```Shell
Testing Dual Process Architecture...

[Test 1] Health Check...
{
  "status": "healthy",
}

[Test 2] Successful Transcoding Log...  # 成功的案例
{
  "status": "ok",
  "result": {
    "successful": true,
  }
}

[Test 3] Failed Transcoding Log...      # 失败的案例
{
  "status": "error_detected",
  "notified": true,                     # 飞书通知
  "result": {
    "successful": false,
    "psnr_value": 0,
    "error_message": "Incorrect ......",     # 错误信息
    "resolution_steps": "Review the ......"  # 修改建议
  }
}
```

**完整日志输出：**

```Shell
autodl-container-9cjes0s087-98c80c91# sh 4-validation-dual-process.sh 
Testing Dual Process Architecture...

[Test 1] Health Check...
{
  "status": "healthy",
  "architecture": "dual-process",
  "service": "business-api"
}

[Test 2] Successful Transcoding Log...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   779  100   103  100   676     16    108  0:00:06  0:00:06 --:--:--    25
{
  "status": "ok",
  "result": {
    "successful": true,
    "psnr_value": 31.9,
    "error_message": "",
    "resolution_steps": ""
  }
}

[Test 3] Failed Transcoding Log...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   803  100   416  100   387     35     32  0:00:12  0:00:11  0:00:01    90
{
  "status": "error_detected",
  "notified": true,
  "result": {
    "successful": false,
    "psnr_value": 0,
    "error_message": "Incorrect parameters for the selected encoder (e.g., codec tags, codec not enabled).",
    "resolution_steps": "Review the selected encoder and its parameters. Ensure the codec is correctly specified and enabled. Check for typos or mismatched parameters. Try using a different encoder or adjusting the parameters."
  }
}

All tests completed!
```

<br />

### 3. 压测服务

```Shell
sh 5-benchmark-dual-process.sh
```

**输出结果总结：**

使用 Apache Bench 对双进程架构的日志分析服务进行了并发压力测试，模拟 10 个并发用户持续发起 100 次 FFmpeg 日志分析请求。测试结果如下：

**测试环境：**

| 项目   | 配置                                 |
| :--- | :--------------------------------- |
| GPU  | NVIDIA RTX 4090D (24GB 显存)         |
| 推理服务 | vLLM 0.11.2 + Qwen2.5-3B (LoRA 微调) |
| 业务服务 | FastAPI + Uvicorn (4 workers)      |
| 并发数  | 10                                 |
| 总请求量 | 100                                |

**核心性能指标：**

| 指标        | 数值         | 说明               |
| :-------- | :--------- | :--------------- |
| 吞吐量 (QPS) | 6.18 req/s | 每秒稳定处理 6 个日志分析请求 |
| 平均响应时间    | 1618 ms    | 单次推理完整链路耗时       |
| P90 响应时间  | 1616 ms    | 90% 请求在 1.6 秒内返回 |
| P99 响应时间  | 1941 ms    | 最慢请求耗时 1.9 秒     |
| 失败请求数     | 0          | 成功率 100%         |
| 单请求平均传输量  | 476 bytes  | 响应体为精简 JSON      |

**响应时间分布：**

| 百分位  | 耗时 (ms) |
| :--- | :------ |
| 50%  | 1439    |
| 66%  | 1506    |
| 75%  | 1536    |
| 80%  | 1554    |
| 90%  | 1616    |
| 95%  | 1678    |
| 98%  | 1931    |
| 99%  | 1941    |
| 100% | 1941    |

**性能分析：**
在当前低并发（10）设置下，单请求平均推理耗时约 1.4\~1.6 秒，QPS 符合理论值“并发数 / 单请求耗时”。瓶颈主要在于模型单次前向传播时间，而非框架开销。全部 100 个请求均成功返回 200 状态码，无超时、无格式校验失败，证明字段映射与状态推断逻辑工作正常。若需提升 QPS，可将 vLLM 的 --max-num-seqs 参数由默认 32 调高至 128，并增加压测并发数至 50 或 100，利用连续批处理充分榨取 GPU 算力，预期吞吐量可提升至 50\~150 req/s。

**压测命令：**
ab -n 100 -c 10 -T 'text/plain' -l -s 120 -p request.data <http://localhost:8000/analyze>

**历史性能参考：**

| 架构版本       | 并发数 | QPS        | 备注                                          |
| :--------- | :-- | :--------- | :------------------------------------------ |
| 单进程异步 (早期) | 50  | 185 req/s  | 存在 Non-2xx responses: 200，系快速失败导致，不代表真实推理能力 |
| 双进程 (当前基线) | 10  | 6.18 req/s | 稳定可靠，100% 成功，可通过参数调优线性扩展                    |

本报告仅采信全部请求成功（Failed requests: 0）的测试结果。

<br />

### 4. 飞书告警

**测试中的压测服务产生的频繁告警内容：**
<img width="1152" height="2376" alt="e643b707b8eab0f13d289d54219047f9" src="https://github.com/user-attachments/assets/f8253214-8f63-43a2-b942-a14b858d882b" />



<br />

<br />

## 项目概述

本服务利用大语言模型对 FFmpeg 转码日志进行智能分析，自动识别转码状态、PSNR 值、错误信息并提供修复建议。支持异步推理、并发请求处理及飞书告警推送。

## 技术栈

- **框架**: FastAPI + vLLM Async Engine
- **模型**: Qwen2.5-3B + LoRA 微调
- **并发**: vLLM Continuous Batching
- **告警**: 飞书 Webhook

## 快速开始

### 环境要求

- Python >= 3.10
- CUDA >= 12.1
- GPU 显存 >= 16GB

### 安装依赖

```bash
pip install vllm fastapi uvicorn httpx transformers
```

### 启动服务

```bash
python -m uvicorn vllm_service_v3_async_send_feishu:app --host 0.0.0.0 --port 8000
```

### 测试服务

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: text/plain" \
  -d "ffmpeg version N-random-g897d21b1b44...[FFmpeg日志内容]"
```

## API 接口

### POST /analyze

分析 FFmpeg 转码日志

**请求体**:

```
FFmpeg 转码日志文本（text/plain）
```

**成功响应**:

```json
{
  "success": true,
  "psnr": 47.56,
  "error": null,
  "resolution": "转码成功，无异常"
}
```

**失败响应（含告警）**:

```json
{
  "success": false,
  "psnr": null,
  "error": "Value 1000000000 for parameter 'video_bit_rate' is out of range",
  "resolution": "建议降低视频比特率参数，确保在有效范围内"
}
```

### GET /health

健康检查

**响应**:

```json
{"message": "Hello, World!"}
```

## 配置说明

### 模型配置

| 参数                       | 默认值                | 说明            |
| ------------------------ | ------------------ | ------------- |
| `BASE_MODEL_PATH`        | `../qwen25-3b`     | 基础模型路径        |
| `LORA_PATH`              | `./finetuned_lora` | LoRA 适配器路径    |
| `max_model_len`          | 2048               | 最大序列长度        |
| `max_num_seqs`           | 32                 | 最大并发序列数       |
| `max_num_batched_tokens` | 65536              | 最大批处理 Token 数 |

### 推理配置

| 参数            | 默认值 | 说明              |
| ------------- | --- | --------------- |
| `max_tokens`  | 512 | 最大输出 Token 数    |
| `temperature` | 0.0 | 温度参数（0.0 为贪心解码） |
| `MAX_RETRIES` | 3   | 推理重试次数          |

### 告警配置

| 参数            | 默认值        | 说明               |
| ------------- | ---------- | ---------------- |
| `WEBHOOK_URL` | 飞书 Webhook | 飞书机器人 Webhook 地址 |

## 项目结构

```
├── vllm_service_v3_async_send_feishu.py  # 异步服务主程序
├── vllm_starter.py                        # 同步测试脚本
├── finetuned_lora/                        # LoRA 微调权重
└── cpu-and-gpu/                           # CPU/GPU 性能测试代码
```

## 核心特性

1. **异步推理**: 基于 vLLM Async Engine，支持请求级调度
2. **连续批处理**: Continuous Batching 技术提升并发吞吐
3. **LoRA 集成**: 动态加载 LoRA 适配器，低显存占用
4. **智能告警**: 自动检测转码异常并推送飞书通知
5. **错误重试**: 内置重试机制确保服务稳定性

## 性能指标

- **单请求延迟**: 500ms \~ 2s（取决于输入长度）
- **最大并发**: 32 个请求
- **批处理容量**: 65536 Token/批次

