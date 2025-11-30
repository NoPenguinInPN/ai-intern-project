from fastapi import FastAPI, HTTPException
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Intern Project")

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],    # 允许所有方法
    allow_headers=["*"],
)

@app.post("/ask")
async def ask(payload: dict):
    q = payload.get("q")
    if not q:
        raise HTTPException(status_code=400, detail="Missing query parameter 'q'")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://170.18.10.21:6001/v1/chat/completions",
                json={
                    "stream": False,
                    "temperature": 0.1,
                    "messages": [{"role": "user", "content": q}],
                    "model": "tclf90/qwen3-32b-gptq-int8",
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=10.0
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))