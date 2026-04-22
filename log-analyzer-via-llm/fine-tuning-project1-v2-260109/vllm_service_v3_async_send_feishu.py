from vllm import LLM, SamplingParams
from vllm.utils import random_uuid
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.lora.request import LoRARequest
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from transformers import AutoTokenizer
import asyncio
import json
import httpx

# log_str1 = "ffmpeg version N-random-g897d21b1b44 shared. Build: gcc-latest.\nInput #0, mov,mp4, from 'input_video_5.mp4':\n  Duration: 00:00:13.00, start: 0.000000, bitrate: 622 kb/s\n    Stream #0:0: Video: h264 (Main), yuv420p, 1920x1080, 52 fps\n    Stream #0:1: Audio: aac, 48000 Hz, stereo\n[libx264 @ 0x81b53c73796d10f5] PSNR Y:46.39 U:48.91 V:47.38 Avg:47.56 Global:47.74\nOutput #0, mp4, to 'output_video_54.mp4':\n  Stream #0:0: Video: h264 (H.264 Main)\n  Stream #0:1: Audio: aac\nframe=  676 fps= 37 q=29.0 size=     48003kB time=00:00:13.00 bitrate=2870kbits/s speed=2.1x\nvideo:43202kB audio:4800kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000%"
# log_str2 = "ffmpeg -i input.mp4 -c:v copy -b:v 1G -c:a copy output_large_bitrate.mp4\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\n[mp4 @ 0x...] Value 1000000000 for parameter 'video_bit_rate' is out of range [-2147483648 - 2147483647]\nCould not write header for output file 'output_large_bitrate.mp4': Invalid argument\nConversion failed!"
# log_str3 = "ffmpeg -i input.mp4 -c:v libx264 -crf 23 -f null -\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\nInput #0, mov,mp4,m4a,3gp,3g2,mj2, from 'input.mp4':\n  Duration: 00:00:10.00, start: 0.000000, bitrate: 1000 kb/s\n    Stream #0:0: Video: h264 (High), yuv420p, 1280x720, 25 fps\nOutput #0, null, to 'pipe:1':\n  Metadata:\n    encoder         : Lavf58.76.100\n    Stream #0:0: Video: h264 (libx264), yuv420p, 1280x720, q=-1--1, 25 fps\nStream mapping:\n  Stream #0:0 -> #0:0 (h264 (native) -> libx264 (libx264))\nPress [q] to stop, [?] for help.\nframe=  250 fps= 25 q=28.0 size=N/A time=00:00:10.00 bitrate=N/A speed=1.00x\nvideo:0kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%"

BASE_MODEL_PATH = "../qwen25-3b"
LORA_PATH = "./finetuned_lora"
LORA_NAME = "my_lora"
LORA_ID = 1
SYSTEM_PROMPT = "Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json."
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/750efd0b-6216-437c-a3ca-ee3c8b4cf5ca"
MAX_RETRIES = 3

# 🔑 FastAPI异步生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    global tokenizer
    global llm
    global sampling_params
    global lora_request

    print("service start, LLM initing ...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)
    # 初始化异步引擎
    engine_args = AsyncEngineArgs(
        model=BASE_MODEL_PATH,
        max_model_len=2048,
        max_num_seqs=32,              # 🔑 最大并发序列数：允许同时处理32个请求
        max_num_batched_tokens=65536,  # 🔑 单个batch的最大token数
        tensor_parallel_size=1,
        gpu_memory_utilization=0.85,
        enable_lora=True,
        max_lora_rank=16,
        max_loras=1,
        kv_cache_dtype="auto",
        dtype="auto",
        block_size=16,   # 数启用了PagedAttention机制，将KV Cache分成固定大小的block=16进行分页管理，避免显存碎片问题，实现接近100%的显存利用率
        enforce_eager=False,
    )
    # 🔑 创建异步LLM引擎
    llm = AsyncLLMEngine.from_engine_args(engine_args)
    sampling_params = SamplingParams(
        max_tokens=512,
        temperature=0.0,
        top_p=1.0,
        top_k=-1,
    )
    lora_request = LoRARequest(LORA_NAME, LORA_ID, LORA_PATH)
    
    # 服务运行中
    yield

    print("sevice is shuting down, cleaning...")
    if llm:
        del llm


# 🔑 创建FastAPI应用，集成异步生命周期
app = FastAPI(
        title="Log Analyzer VLLM Service", 
        description="Log Analyzer VLLM Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan  # 🔑 使用异步生命周期管理
        )

# 异步推理调用
async def vllm_analyze(log_str: str):
    conversation = [
        {"role": "user", "content": SYSTEM_PROMPT + " " + log_str}
    ]
    prompt_str = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
    async for output in llm.generate(   # 🔑 异步生成：支持请求级别的调度
        prompt_str,
        sampling_params,
        random_uuid(),
        lora_request=lora_request  # 🔑 动态加载LoRA适配器
    ):
        final_output = output
    return final_output.outputs[0].text

async def send_feishu_notification(
    webhook_url: str,
    title: str,
    text_content: str,
    href: str = "http://www.baidu.com/",
    at_user_id: str = "all"
) -> dict:
    # 构造请求数据
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [
                        [
                            {"tag": "text", "text": f"{text_content}\n"},
                            {"tag": "a", "text": "点击进行更多操作", "href": href},
                            {"tag": "text", "text": "\n"},
                            {"tag": "at", "user_id": at_user_id}
                        ]
                    ]
                }
            }
        }
    }

    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url=webhook_url,
                json=data,  # httpx 的 json 参数自动处理 dumps 和 Content-Type
                headers=headers
            )
            return {
                "success": True,
                "status_code": response.status_code,
                "response_text": response.text
            }

    except httpx.RequestError as e:
        return {
            "success": False,
            "error": str(e),
            "request_data": data
        }

@app.get("/health")
def health():
    return {"message": "Hello, World!"}

# 🔑 异步API端点
@app.post("/analyze")
async def analyze_log(request: Request):
    body = await request.body()   # 异步读取请求体
    ffmpeg_log_str = body.decode("utf-8")
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 异步调用推理
            llm_output = await vllm_analyze(ffmpeg_log_str)
            llm_output_parsed = json.loads(llm_output)
            if "success" not in llm_output_parsed:
                raise ValueError("Missing required field: 'success'")
            if "psnr" not in llm_output_parsed:
                raise ValueError("Missing required field: 'psnr'")
            if not isinstance(llm_output_parsed["success"], bool):
                raise ValueError("Required field: 'success' boolean")

            success = llm_output_parsed['success']
            psnr = llm_output_parsed['psnr']
            error_message = llm_output_parsed['error']
            resolution_steps = llm_output_parsed['resolution']

            if error_message is None or error_message == "" or success == True:
                print("This log is OK.")
                return "OK"
            else:
                notify_result = await send_feishu_notification(
                    webhook_url=WEBHOOK_URL,
                    title="转码系统告警",
                    text_content="转码异常:" + error_message + "\n AI 分析方案:" + resolution_steps +"\n",
                    href="http://www.baidu.com",
                    at_user_id="all"
                )
            return llm_output
        except (json.JSONDecodeError, ValueError, KeyError, Exception) as e:
            if attempt == MAX_RETRIES:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Failed to generate valid JSON response after retries",
                        "last_raw_output": llm_output if 'llm_output' in locals() else None,
                        "reason": str(e)
                    }
                )