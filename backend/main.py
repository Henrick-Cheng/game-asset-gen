from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from asset_types import ASSET_TYPES, DEFAULT_ASSET_TYPE_ID
from bg_remover import STATIC_DIR, remove_background
from prompt_enhancer import enhance_prompt
from style_presets import DEFAULT_STYLE_ID, STYLE_PRESETS
from wanx_client import WanxError, generate_image

load_dotenv()  # 读取同目录 .env（开发环境）


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATIC_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="Game Asset Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GenerateRequest(BaseModel):
    prompt: str
    style: str = DEFAULT_STYLE_ID
    asset_type: str = DEFAULT_ASSET_TYPE_ID
    remove_bg: bool = True

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

    @field_validator("asset_type")
    @classmethod
    def asset_type_must_be_valid(cls, v: str) -> str:
        if v not in ASSET_TYPES:
            valid = ", ".join(ASSET_TYPES.keys())
            raise ValueError(f"asset_type 无效，可选值：{valid}")
        return v


class GenerateResponse(BaseModel):
    image_url: str


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """提示词增强 → 拼接风格后缀 → 拼接类型提示词 → 通义万相文生图 → 可选去背景。"""
    enhanced = await enhance_prompt(req.prompt)
    style_suffix = STYLE_PRESETS[req.style].suffix
    type_suffix = ASSET_TYPES[req.asset_type].suffix
    final_prompt = f"{enhanced}, {style_suffix}, {type_suffix}"

    try:
        url = await generate_image(final_prompt)
    except WanxError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if req.remove_bg:
        url = await remove_background(url)

    return GenerateResponse(image_url=url)


@app.get("/api/styles")
async def list_styles():
    """返回所有可用风格预设。"""
    return [{"id": p.id, "name": p.name} for p in STYLE_PRESETS.values()]


@app.get("/api/asset-types")
async def list_asset_types():
    """返回所有可用素材类型。"""
    return [{"id": t.id, "name": t.name} for t in ASSET_TYPES.values()]


@app.get("/health")
async def health():
    return {"status": "ok"}
