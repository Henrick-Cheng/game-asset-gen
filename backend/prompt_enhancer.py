"""
Qwen 提示词增强模块。

调用 qwen-plus 把用户的简短中文描述扩写成详细的英文文生图提示词。
Qwen 不可用时降级返回原始 prompt，不影响主流程。
"""

import logging
import os

import httpx

_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_MODEL = "qwen-plus"
_TIMEOUT = 15  # 秒

_SYSTEM = (
    "You are an expert prompt writer for text-to-image AI models. "
    "Given a short description of a 2D game asset (possibly in Chinese), "
    "rewrite it as a detailed English prompt for image generation. "
    "Enrich it with visual details about appearance, composition, and lighting "
    "that suit a game asset, but strictly preserve the user's core intent. "
    "Output only the enhanced prompt — no explanations, no quotes."
)

logger = logging.getLogger(__name__)


async def enhance_prompt(user_prompt: str) -> str:
    """
    用 Qwen 扩写用户描述，失败时返回原始 prompt。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        logger.warning("DASHSCOPE_API_KEY 未设置，跳过 Qwen 增强")
        return user_prompt

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 256,
                    "temperature": 0.7,
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            enhanced = data["choices"][0]["message"]["content"].strip()
            return enhanced if enhanced else user_prompt
    except Exception as exc:
        logger.warning("Qwen 增强失败，降级使用原始 prompt：%s", exc)
        return user_prompt
