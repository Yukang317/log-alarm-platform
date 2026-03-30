from fastapi import FastAPI

app = FastAPI()

@app.get("/health")     # 仅一个路由（对应4-sh） - 后续在终端执行：“curl http://127.0.0.1:8000/health”，会有回复。
def health():
    return "alive"

