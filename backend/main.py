from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from wanx_client import WanxError, generate_image

load_dotenv()  # 读取同目录 .env（开发环境）


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Game Asset Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("prompt 不能为空")
        return v


class GenerateResponse(BaseModel):
    image_url: str


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """接收文本描述，调用通义万相生成图片，返回图片 URL。"""
    try:
        url = await generate_image(req.prompt)
    except WanxError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return GenerateResponse(image_url=url)


@app.get("/health")
async def health():
    return {"status": "ok"}
