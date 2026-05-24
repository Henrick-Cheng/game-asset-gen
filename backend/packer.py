"""
精灵图打包模块。

将多张透明 PNG 排版打包为一张精灵图大图（shelf 行装箱算法），
同时生成对应的图集描述文件（JSON 或 Godot .tres 格式），
最终打包为 ZIP bytes 返回。
"""

import io
import json
import math
import zipfile
from pathlib import Path

from PIL import Image

from bg_remover import STATIC_DIR

PADDING = 1  # 精灵之间的像素间距，防止纹理渗色


def _url_to_path(image_url: str) -> Path:
    return STATIC_DIR / Path(image_url).name


def _shelf_pack(
    items: list[tuple[str, Image.Image]],
) -> tuple[list[tuple[str, Image.Image, int, int]], int, int]:
    """
    行装箱算法（shelf packing）。
    按高度降序排列，逐行从左到右放置，行宽超过目标宽度时换行。
    返回 (frames, sheet_w, sheet_h)，frames 元素为 (name, img, x, y)。
    """
    if not items:
        return [], 0, 0

    sorted_items = sorted(items, key=lambda t: t[1].height, reverse=True)

    # 目标宽度：基于总面积估算近似正方形的边长，最小为最宽图片宽度
    total_area = sum(img.width * img.height for _, img in sorted_items)
    max_img_w = max(img.width for _, img in sorted_items)
    target_w = max(max_img_w, int(math.sqrt(total_area) * 1.2))
    target_w = min(target_w, 4096)

    placed: list[tuple[str, Image.Image, int, int]] = []
    x, y = 0, 0
    row_h = 0
    sheet_w = 0

    for name, img in sorted_items:
        w, h = img.width, img.height
        if x > 0 and x + w > target_w:
            y += row_h + PADDING
            x = 0
            row_h = 0
        placed.append((name, img, x, y))
        row_h = max(row_h, h)
        sheet_w = max(sheet_w, x + w)
        x += w + PADDING

    sheet_h = y + row_h
    return placed, sheet_w, sheet_h


def _make_json_atlas(frames_data: list[dict], sheet_w: int, sheet_h: int) -> str:
    """
    通用 JSON 格式（Phaser 3 / PixiJS / 大多数 Web 引擎兼容）。
    结构：{ frames: [{name, x, y, w, h}], meta: {image, size} }
    """
    atlas = {
        "frames": [
            {"name": f["name"], "x": f["x"], "y": f["y"], "w": f["w"], "h": f["h"]}
            for f in frames_data
        ],
        "meta": {
            "image": "spritesheet.png",
            "size": {"w": sheet_w, "h": sheet_h},
            "scale": "1",
        },
    }
    return json.dumps(atlas, ensure_ascii=False, indent=2)


def _make_godot_atlas(frames_data: list[dict]) -> str:
    """
    Godot 4 文本资源格式（.tres）。
    每张精灵对应一个 AtlasTexture sub_resource，
    放入 Godot 项目后可直接在 Sprite2D / AnimatedSprite2D 等节点中引用。
    使用前请将 spritesheet.png 和本文件一同放入 res:// 目录。
    """
    load_steps = 1 + len(frames_data)
    lines = [
        f'[gd_resource type="Resource" load_steps={load_steps} format=3]',
        "",
        '[ext_resource type="Texture2D" path="res://spritesheet.png" id="1"]',
        "",
    ]
    for f in frames_data:
        rid = f["name"].replace(".", "_").replace("/", "_")
        lines += [
            f'[sub_resource type="AtlasTexture" id="AtlasTexture_{rid}"]',
            'atlas = ExtResource("1")',
            f'region = Rect2({f["x"]}, {f["y"]}, {f["w"]}, {f["h"]})',
            "",
        ]
    return "\n".join(lines)


def pack(image_urls: list[str], atlas_format: str = "json") -> bytes:
    """
    打包多张本地图片为精灵图 + atlas 文件，返回 ZIP bytes。

    参数：
        image_urls   — /static/<filename> 形式的本地 URL 列表
        atlas_format — "json"（默认）或 "godot"

    返回：
        包含 spritesheet.png 和 atlas 文件的 ZIP bytes
    """
    items: list[tuple[str, Image.Image]] = []
    for i, url in enumerate(image_urls):
        path = _url_to_path(url)
        img = Image.open(path).convert("RGBA")
        items.append((f"sprite_{i}.png", img))

    placed, sheet_w, sheet_h = _shelf_pack(items)

    # 合成精灵图
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    frames_data: list[dict] = []
    for name, img, x, y in placed:
        sheet.paste(img, (x, y), img)
        frames_data.append({"name": name, "x": x, "y": y, "w": img.width, "h": img.height})

    sheet_buf = io.BytesIO()
    sheet.save(sheet_buf, format="PNG")
    sheet_bytes = sheet_buf.getvalue()

    # 生成图集描述
    if atlas_format == "godot":
        atlas_text = _make_godot_atlas(frames_data)
        atlas_filename = "atlas.tres"
    else:
        atlas_text = _make_json_atlas(frames_data, sheet_w, sheet_h)
        atlas_filename = "atlas.json"

    # 打包为 ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("spritesheet.png", sheet_bytes)
        zf.writestr(atlas_filename, atlas_text.encode("utf-8"))
    return zip_buf.getvalue()
