# Dual-Process_architecture/business_service_fastapi.py
# FastAPI 业务服务 - 双进程架构的业务逻辑层
# 职责：接收用户请求 → 调用 vLLM 推理 → 处理结果 → 发送飞书通知
from fastapi import FastAPI, Request, HTTPException
import httpx
import json
import asyncio 


VLLM_SERVICE_URL = "http://localhost:8001"  # vLLM 推理服务的地址
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/d5c30596-7942-4932-8728-d83716aaaa27"
SYSTEM_PROMPT = "Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json."
MAX_RETRIES = 3                             # 最大重试次数（网络请求失败时自动重试）

# ========== 初始化 FastAPI 应用 ==========
app = FastAPI(
    title = "Log Analyzer = Dual Process Architecture",
    description = "FastAPI 业务服务 + vLLM 推理服务（双进程架构）",
    version = "2.0.0",
)

# ========== 核心功能函数 ==========
async def call_vllm_inference(log_str: str) -> str:
    """
    调用独立的 vLLM 推理服务
    
    参数:
        log_str: FFmpeg 日志字符串
    
    返回:
        AI 生成的分析结果（JSON 格式的字符串）
    
    异常:
        如果 vLLM 服务返回错误，抛出 Exception
    """
    # 使用 httpx 异步客户端发起 HTTP 请求
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 调用 vLLM 的 OpenAI 兼容 API
        response = await client.post(
            f"{VLLM_SERVICE_URL}/v1/chat/completions",      # vLLM 聊天补全接口
            json={
                "model": "my-lora",         # 使用名为"my-lora"的微调模型
                "messages": [
                    {"role": "user", "content": SYSTEM_PROMPT + " " + log_str}
                ],
                "max_tokens": 512,
                "temperature": 0.0
            }
        )
    # 检查响应状态码
    if response.status_code != 200:
        raise Exception(f"vLLM service error: {response.text}")

    # 解析并返回 AI 生成的文本内容
    return response.json()["choices"][0]["messages"]["content"]



async def send_feishu_notification(title: str, text_content: str):
    """
    发送飞书通知
    
    参数:
        title: 消息标题
        text_content: 消息正文内容
    
    返回:
        无返回值，直接发送 HTTP 请求
    """
    data = {
        "msg_type": "post",     # 消息类型：Post（富文本）
        "content":{
            "post": {
                # 中文版本
                "zh_cn": {
                    "title": title,
                    "content":[[
                        {
                            "tag": "text",
                            "text": f"{text_contetn}\n"
                        },
                        {
                            "tag": "a",
                            "text": "点击查看详情",
                            "href": "http://example.com"
                        },
                        {
                            "tag": "at",
                            "user_id": "all"
                        }
                    ]]
                }
            }
        }
    }
    # 异步发送 HTTP POST 请求到飞书
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(WEBHOOK_URL, json=data)


# ========== FastAPI 路由接口 ==========
@app.get("/health")
def health():
    """
    健康检查接口
    
    用途:
        1. 服务存活检测
        2. Kubernetes 探针
        3. 负载均衡器心跳检测
    
    返回:
        JSON 格式的服务状态信息
    """
    return {
        "status": "healthy",
        "architecture": "dual-process",
        "service": "business-api"
    }


@app.post("/analyze")
async def analyze_log(request: Request):
    """
    分析 FFmpeg 日志的主接口
    
    参数:
        request: FastAPI 的请求对象
    
    流程:
        1. 读取请求体（FFmpeg 日志）
        2. 调用 vLLM 推理服务分析日志
        3. 解析 AI 返回的 JSON 结果
        4. 如果有错误，发送飞书通知
        5. 返回分析结果给用户
    
    返回:
        成功：{"status": "ok", "result": {...}}
        失败：HTTP 500 错误
    """
    # 步骤 1: 读取请求体并解码
    ffmpeg_log = await request.body()           # 异步读取原始字节
    ffmpeg_log_str = ffmpeg_log.decode("utf-8") # 解码为字符串

    # 步骤 2: 带重试机制的分析循环
    for attempt in range(1, MAX_RETRIES + 1):  # 最多尝试 3 次
        try:
            # 调用 vLLM 推理服务
            raw_output = await call_vllm_inference(ffmpeg_log_str)
            # 解析 AI 返回的 JSON 字符串
            parsed = json.loads(raw_output)

            # 验证必需字段是否存在
            if "success" not in parsed or "psnr" not in parsed:
                raise ValueError("Missing required fields: 'success' or 'psnr'")
            
            success = parsed["success"]
            error_msg = parsed.get("error", "")
            resolution = parsed.get("resolution", "")

            # 步骤 3: 如果转码失败且有错误信息，发送飞书告警
            if not success and error_msg:
                await send_feishu_notification(
                    title = "转码系统告警",
                    text_content = f"异常：{error_msg}\n解决方案：{resolution}"
                )
                return {
                    "status": "error_detected",  # 状态：检测到错误
                    "notified": True,            # 已发送通知
                    "result": parsed             # 完整分析结果
                }
            
             # 步骤 4: 转码成功，直接返回结果
            return {
                "status": "ok",
                "result": parsed
            }

        except Exception as e:
            if attempt == MAX_RETRIES:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": f"Analysis failed after {MAX_RETRIES} retries",
                        "reason": str(e),
                        # 这里添加注释
                        "raw_output": raw_output if 'raw_output' in locals() else None
                    }
                )
            # 指数退避策略：第 1 次失败等 1 秒，第 2 次等 2 秒...
            await asyncio.sleep(1 * attempt)






