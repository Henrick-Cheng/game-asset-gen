from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from prompt_enhancer import enhance_prompt
from style_presets import DEFAULT_STYLE_ID, STYLE_PRESETS
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
    style: str = DEFAULT_STYLE_ID

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("prompt 不能为空")
        return v

    @field_validator("style")
    @classmethod
    def style_must_be_valid(cls, v: str) -> str:
        if v not in STYLE_PRESETS:
            valid = ", ".join(STYLE_PRESETS.keys())
            raise ValueError(f"style 无效，可选值：{valid}")
        return v


class GenerateResponse(BaseModel):
    image_url: str


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """提示词增强 → 拼接风格后缀 → 通义万相文生图。"""
    enhanced = await enhance_prompt(req.prompt)
    style_suffix = STYLE_PRESETS[req.style].suffix
    final_prompt = f"{enhanced}, {style_suffix}"

    try:
        url = await generate_image(final_prompt)
    except WanxError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return GenerateResponse(image_url=url)


@app.get("/api/styles")
async def list_styles():
    """返回所有可用风格预设。"""
    return [{"id": p.id, "name": p.name} for p in STYLE_PRESETS.values()]


@app.get("/health")
async def health():
    return {"status": "ok"}
