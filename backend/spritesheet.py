"""
精灵表合成模块。

将多张本地 PNG 图片拼合为一张精灵表（网格布局）。
"""

import math
import uuid
from pathlib import Path

from PIL import Image

from bg_remover import STATIC_DIR


def _url_to_path(image_url: str) -> Path:
    """把 /static/<filename> 形式的 URL 转换为本地文件路径。"""
    filename = Path(image_url).name
    return STATIC_DIR / filename


def build_spritesheet(image_urls: list[str], cell_size: int = 0) -> tuple[str, int, int, int]:
    """
    将给定的本地图片 URL 列表合并为一张精灵表。

    - cell_size=0 表示自动取所有图片中最大的宽/高。
    - 返回 (url, cols, rows, cell_size)。
    """
    images: list[Image.Image] = []
    for url in image_urls:
        path = _url_to_path(url)
        img = Image.open(path).convert("RGBA")
        images.append(img)

    if cell_size <= 0:
        max_w = max(img.width for img in images)
        max_h = max(img.height for img in images)
        cell_size = max(max_w, max_h)

    cols = math.ceil(math.sqrt(len(images)))
    rows = math.ceil(len(images) / cols)

    sheet = Image.new("RGBA", (cols * cell_size, rows * cell_size), (0, 0, 0, 0))

    for idx, img in enumerate(images):
        col = idx % cols
        row = idx // cols
        # 等比缩放到 cell_size 内
        img.thumbnail((cell_size, cell_size), Image.LANCZOS)
        # 居中放置
        x = col * cell_size + (cell_size - img.width) // 2
        y = row * cell_size + (cell_size - img.height) // 2
        sheet.paste(img, (x, y), img)

    filename = f"spritesheet_{uuid.uuid4().hex}.png"
    STATIC_DIR.mkdir(exist_ok=True)
    sheet.save(STATIC_DIR / filename, format="PNG")

    return f"/static/{filename}", cols, rows, cell_size
