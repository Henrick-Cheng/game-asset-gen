"""
去背景模块。

使用 rembg 本地去背景，处理结果保存为透明 PNG 到 static/ 目录。
任何异常均降级返回原图 URL，不影响主流程。

注意：首次调用会自动下载 u2net 模型（约 170 MB）到 ~/.u2net/。
"""

import logging
import uuid
from pathlib import Path

import httpx
from rembg import remove

STATIC_DIR = Path(__file__).parent / "static"

logger = logging.getLogger(__name__)


async def remove_background(image_url: str) -> str:
    """
    下载 image_url 的图片，去除背景后保存为透明 PNG。
    返回 /static/<uuid>.png，失败时返回原始 image_url。
    """
    try:
        STATIC_DIR.mkdir(exist_ok=True)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            image_bytes = resp.content

        result_bytes = remove(image_bytes)

        filename = f"{uuid.uuid4().hex}.png"
        (STATIC_DIR / filename).write_bytes(result_bytes)

        return f"/static/{filename}"
    except Exception as exc:
        logger.warning("去背景失败，降级返回原图：%s", exc)
        return image_url
