from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# log_str1 = "ffmpeg version N-random-g897d21b1b44 shared. Build: gcc-latest.\nInput #0, mov,mp4, from 'input_video_5.mp4':\n  Duration: 00:00:13.00, start: 0.000000, bitrate: 622 kb/s\n    Stream #0:0: Video: h264 (Main), yuv420p, 1920x1080, 52 fps\n    Stream #0:1: Audio: aac, 48000 Hz, stereo\n[libx264 @ 0x81b53c73796d10f5] PSNR Y:46.39 U:48.91 V:47.38 Avg:47.56 Global:47.74\nOutput #0, mp4, to 'output_video_54.mp4':\n  Stream #0:0: Video: h264 (H.264 Main)\n  Stream #0:1: Audio: aac\nframe=  676 fps= 37 q=29.0 size=     48003kB time=00:00:13.00 bitrate=2870kbits/s speed=2.1x\nvideo:43202kB audio:4800kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000%"
# log_str2 = "ffmpeg -i input.mp4 -c:v copy -b:v 1G -c:a copy output_large_bitrate.mp4\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\n[mp4 @ 0x...] Value 1000000000 for parameter 'video_bit_rate' is out of range [-2147483648 - 2147483647]\nCould not write header for output file 'output_large_bitrate.mp4': Invalid argument\nConversion failed!"
# log_str3 = "ffmpeg -i input.mp4 -c:v libx264 -crf 23 -f null -\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\nInput #0, mov,mp4,m4a,3gp,3g2,mj2, from 'input.mp4':\n  Duration: 00:00:10.00, start: 0.000000, bitrate: 1000 kb/s\n    Stream #0:0: Video: h264 (High), yuv420p, 1280x720, 25 fps\nOutput #0, null, to 'pipe:1':\n  Metadata:\n    encoder         : Lavf58.76.100\n    Stream #0:0: Video: h264 (libx264), yuv420p, 1280x720, q=-1--1, 25 fps\nStream mapping:\n  Stream #0:0 -> #0:0 (h264 (native) -> libx264 (libx264))\nPress [q] to stop, [?] for help.\nframe=  250 fps= 25 q=28.0 size=N/A time=00:00:10.00 bitrate=N/A speed=1.00x\nvideo:0kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%"

BASE_MODEL_PATH = "../qwen25-3b"
LORA_PATH = "./finetuned_lora"
LORA_NAME = "my_lora"
LORA_ID = 1
SYSTEM_PROMPT = "Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json."
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行（startup）
    global llm
    global sampling_params
    global lora_request

    # ========== 出生阶段（startup）==========
    print("service start, LLM initing ...")
    # 加载超重的模型到内存（只做一次！）
    llm = LLM(                          # 同步调用
        model=BASE_MODEL_PATH,
        max_model_len=2048,
        max_num_batched_tokens=4096,    # 较小批次
        tensor_parallel_size=1,
        gpu_memory_utilization=0.80,
        enable_lora=True,
        max_lora_rank=64,
        max_loras=4,
    )
    sampling_params = SamplingParams(
        max_tokens=512,
        temperature=0.0,
        top_p=1.0,
        top_k=-1,
    )
    lora_request = LoRARequest(LORA_NAME, LORA_ID, LORA_PATH)
    
    yield  # ⭐ 关键：这里分隔了"出生"和"死亡"
           # yield 之前 = startup
           # yield 之后 = shutdown
    
    # ========== 退休阶段（shutdown）==========
    print("sevice is shuting down, cleaning...")
    if llm:
        del llm     # 释放 GPU 显存

app = FastAPI(
        title="Log Analyzer VLLM Service", 
        description="Log Analyzer VLLM Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
        )

# 同步调用
def vllm_analyze(log_str: str):
    conversation = [
        {"role": "user", "content": SYSTEM_PROMPT + " " + log_str}
    ]
    outputs = llm.chat(                     # 阻塞
        conversation,
        sampling_params=sampling_params,
        lora_request=lora_request,
    )                                       # ❌ 同步阻塞 1 秒钟
    return outputs[0].outputs[0].text

@app.get("/health")
def health():
    return {"message": "Hello, World!"}

@app.post("/analyze")
async def analyze_log(request: Request):  # ⭐ 声明为 async
    body = await request.body()  # ✅ 异步接收数据
    ffmpeg_log_str = body.decode("utf-8")
    return vllm_analyze(ffmpeg_log_str)  # ❌ 同步调用，阻塞！
