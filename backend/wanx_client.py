"""
通义万相文生图客户端。

流程：
  1. 提交异步任务，获取 task_id
  2. 轮询任务状态，直到 SUCCEEDED / FAILED / 超时
"""

import asyncio
import os
import httpx

_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
_SUBMIT_PATH = "/services/aigc/text2image/image-synthesis"
_QUERY_PATH = "/tasks/{task_id}"

_MODEL = "wanx2.1-t2i-turbo"
_POLL_INTERVAL = 2          # 秒
_TIMEOUT_SECONDS = 120      # 最长等待时间


class WanxError(Exception):
    """通义万相调用失败"""


def _api_key() -> str:
    key = os.getenv("DASHSCOPE_API_KEY", "")
    if not key:
        raise WanxError("环境变量 DASHSCOPE_API_KEY 未设置")
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        # 告知服务端这是异步任务
        "X-DashScope-Async": "enable",
    }


async def _submit_task(client: httpx.AsyncClient, prompt: str) -> str:
    """提交文生图任务，返回 task_id。"""
    payload = {
        "model": _MODEL,
        "input": {"prompt": prompt},
        "parameters": {"size": "1024*1024", "n": 1},
    }
    resp = await client.post(
        f"{_BASE_URL}{_SUBMIT_PATH}",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise WanxError(f"提交任务失败 HTTP {e.response.status_code}: {e.response.text}") from e
    data = resp.json()

    task_id = data.get("output", {}).get("task_id")
    if not task_id:
        raise WanxError(f"提交任务失败，响应：{data}")
    return task_id


async def _poll_task(client: httpx.AsyncClient, task_id: str) -> str:
    """轮询任务直到完成，返回图片 URL。"""
    deadline = asyncio.get_event_loop().time() + _TIMEOUT_SECONDS
    headers = {
        "Authorization": f"Bearer {_api_key()}",
    }

    while True:
        if asyncio.get_event_loop().time() > deadline:
            raise WanxError(f"等待任务 {task_id} 超时（>{_TIMEOUT_SECONDS}s）")

        resp = await client.get(
            f"{_BASE_URL}{_QUERY_PATH.format(task_id=task_id)}",
            headers=headers,
            timeout=30,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise WanxError(f"查询任务失败 HTTP {e.response.status_code}: {e.response.text}") from e
        data = resp.json()

        output = data.get("output", {})
        status = output.get("task_status")

        if status == "SUCCEEDED":
            results = output.get("results", [])
            if not results or not results[0].get("url"):
                raise WanxError(f"任务成功但未返回图片 URL，响应：{data}")
            return results[0]["url"]

        if status in ("FAILED", "CANCELED"):
            code = output.get("code", "")
            message = output.get("message", "")
            raise WanxError(f"任务 {task_id} 失败：{code} {message}")

        # PENDING / RUNNING —— 继续等待
        await asyncio.sleep(_POLL_INTERVAL)


async def generate_image(prompt: str) -> str:
    """
    调用通义万相生成图片，返回图片 URL。

    :param prompt: 文本描述
    :returns: 可直接访问的图片 URL
    :raises WanxError: API 调用失败或超时
    """
    async with httpx.AsyncClient() as client:
        task_id = await _submit_task(client, prompt)
        image_url = await _poll_task(client, task_id)
    return image_url
