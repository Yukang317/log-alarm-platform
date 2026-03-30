# 把fastapi-101.py，feishu-101.py，vllm-101.py（分析）整合到一起
from fastapi import FastAPI, Request

from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
from contextlib import asynccontextmanager
from vllm.utils import random_uuid
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
import json
import asyncio
import httpx


BASE_MODEL_PATH = "../qwen25-3b"
LORA_PATH = "./finetuned_lora"
LORA_NAME = "my_lora"
LORA_ID = 1
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/d5c30596-7942-4932-8728-d83716aaaa27"
MAX_RETRIES= 3



# llm = LLM(
#     model=BASE_MODEL_PATH,
#     max_model_len=2048,
#     # 最长并发的token
#     max_num_batched_tokens=4096,
#     tensor_parallel_size=1,
#     gpu_memory_utilization=0.80,
#     enable_lora=True,
#     max_lora_rank=64,
#     max_loras=1,
# )

# lora_request = LoRARequest(LORA_NAME, LORA_ID, LORA_PATH)

# sampling_params = SamplingParams(
#     max_tokens=512,     # 不能默认值，一般拉长一点
#     temperature=0.0,
#     top_p=1.0,
#     top_k=-1,   # 如下束搜索，只拿最高的几个，-1的意思是都可以选
# )

# 束搜索
# 中 0.7
# 左 0.2 
# 右 0.1

system_prompt = "Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json."
# log_str1 = "ffmpeg version N-random-g897d21b1b44 shared. Build: gcc-latest.\nInput #0, mov,mp4, from 'input_video_5.mp4':\n  Duration: 00:00:13.00, start: 0.000000, bitrate: 622 kb/s\n    Stream #0:0: Video: h264 (Main), yuv420p, 1920x1080, 52 fps\n    Stream #0:1: Audio: aac, 48000 Hz, stereo\n[libx264 @ 0x81b53c73796d10f5] PSNR Y:46.39 U:48.91 V:47.38 Avg:47.56 Global:47.74\nOutput #0, mp4, to 'output_video_54.mp4':\n  Stream #0:0: Video: h264 (H.264 Main)\n  Stream #0:1: Audio: aac\nframe=  676 fps= 37 q=29.0 size=     48003kB time=00:00:13.00 bitrate=2870kbits/s speed=2.1x\nvideo:43202kB audio:4800kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000%"
# log_str2 = "ffmpeg -i input.mp4 -c:v copy -b:v 1G -c:a copy output_large_bitrate.mp4\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\n[mp4 @ 0x...] Value 1000000000 for parameter 'video_bit_rate' is out of range [-2147483648 - 2147483647]\nCould not write header for output file 'output_large_bitrate.mp4': Invalid argument\nConversion failed!"
# log_str3 = "ffmpeg -i input.mp4 -c:v libx264 -crf 23 -f null -\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\nInput #0, mov,mp4,m4a,3gp,3g2,mj2, from 'input.mp4':\n  Duration: 00:00:10.00, start: 0.000000, bitrate: 1000 kb/s\n    Stream #0:0: Video: h264 (High), yuv420p, 1280x720, 25 fps\nOutput #0, null, to 'pipe:1':\n  Metadata:\n    encoder         : Lavf58.76.100\n    Stream #0:0: Video: h264 (libx264), yuv420p, 1280x720, q=-1--1, 25 fps\nStream mapping:\n  Stream #0:0 -> #0:0 (h264 (native) -> libx264 (libx264))\nPress [q] to stop, [?] for help.\nframe=  250 fps= 25 q=28.0 size=N/A time=00:00:10.00 bitrate=N/A speed=1.00x\nvideo:0kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%"


 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行（startup）
    global tokenizer
    global llm
    global sampling_params
    global lora_request

    print("service start, LLM initing ...")

    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)
    engine_args = AsyncEngineArgs(
        model=BASE_MODEL_PATH,
        max_model_len=2048,
        # 以下两个参数来控制一批一批的做多少
        # 以时间优化Continuous Batchinbg为例，粗糙理解第一个参数是行，第二个参数是面积
        max_num_seqs=32,                # 最大并发量
        max_num_batched_tokens=65536,   # 序列并发
        tensor_parallel_size=1,
        gpu_memory_utilization=0.85,    # 与上两个
        enable_lora=True,
        max_lora_rank=16,
        max_loras=1,            # 最多支持一个lora
        kv_cache_dtype="auto",
        dtype="auto",
        block_size=16,
        enforce_eager=False,
    )
    llm = AsyncLLMEngine.from_engine_args(engine_args)

    sampling_params = SamplingParams(
        max_tokens=512,
        temperature=0.0,
        top_p=1.0,
        top_k=-1,
    )
    lora_request = LoRARequest(LORA_NAME, LORA_ID, LORA_PATH)
    
    yield   # 进程让出去

    print("sevice is shuting down, cleaning...")
    if llm:
        del llm

app = FastAPI(

)

# 待优化：fastapi异步框架中有了一个同步函数
async def vllm_analyze(log_str: str):
    conversation = [
        {"role": "user", "content": system_prompt + " " + log_str}
    ]
    # 手动应用聊天模板
    prompt_str = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
    async for output in llm.generate(
        prompt_str,
        sampling_params,
        random_uuid(),      # 异步返回，用ID区分
        lora_request=lora_request
    ):
        final_output = output
    return final_output.outputs[0].text
    # llm. 已经变成异步
    # outputs = llm.chat(
    #     conversation,
    #     sampling_params=sampling_params,
    #     lora_request=lora_request,
    # )
    # return outputs[0].outputs[0].text


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
    return "alive"


@app.post("/analyze")
async def analyze_log(request: Request):
    body = await request.body()
    ffmpeg_log_str = body.decode("utf-8")

    # json重试
    for attempt in range(1, 3):
        try:
            raw_output = await vllm_analyze(ffmpeg_log_str)
            parsed = json.loads(raw_output)
            if "success" not in parsed:
                raise ValueError("Missing required field: 'success'")
            if "psnr" not in parsed:
                raise ValueError("Missing required field: 'psnr'")
            if not isinstance(parsed["success"], bool):
                raise ValueError("Required field: 'success' boolean")
            
            succ = parsed["success"]
            psnr = parsed["psnr"]
            err = parsed["error"]
            resolution = parsed["resolution"]

            return "here I am"

            if succ == False:
                notify_result = await send_feishu_notification(
                    webhook_url = webhook_url,
                    title = "大哥大姐新年好"
                    text_content = "出错了，错误是：" + err + "解决方案是：" + resolution,
                    href = "http://www.baidu.dom"
                    at_user_id = "all"
                )
                return raw_output
            else:
                print("Everything is OK.")
                return "OK"

            return raw_output
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if attempt == MAX_RETRIES:
                # send_feishu_notification
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Failed to generate valid JSON response after retries"
                    }
                )


    return await vllm_analyze(ffmpeg_log_str)

