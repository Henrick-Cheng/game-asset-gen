"""
精灵图打包功能测试脚本。

测试要点：
1. 多张不同尺寸的透明 PNG 拼入大图后不重叠
2. 透明通道保留
3. atlas.json 坐标与大图中的实际像素位置对得上
4. atlas Godot 格式结构合法
"""

import io
import json
import os
import sys
import uuid
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
os.chdir(Path(__file__).parent)  # make relative imports work

from bg_remover import STATIC_DIR
from packer import _make_godot_atlas, _make_json_atlas, _shelf_pack, pack

STATIC_DIR.mkdir(exist_ok=True)

# ── 测试用例：4 张不同尺寸、不同颜色、带透明区域的精灵图 ─────────────────────

SPRITES = [
    # (label, w, h, fill_color_rgba)
    ("warrior",   64,  80, (220,  50,  50, 200)),   # 红色高个子角色
    ("coin",      32,  32, (255, 200,   0, 230)),   # 金色小图标
    ("platform", 128,  24, ( 80, 180,  80, 210)),   # 宽矮地块
    ("potion",    40,  56, ( 80,  80, 220, 200)),   # 蓝色药水
]


def make_sprite(w: int, h: int, color: tuple) -> Image.Image:
    """生成中心带实色圆、四角透明的测试精灵图。"""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 内切椭圆，留出四角作为透明区域
    margin = max(2, min(w, h) // 6)
    draw.ellipse([margin, margin, w - margin, h - margin], fill=color)
    return img


def save_sprite(img: Image.Image, name: str) -> str:
    filename = f"test_{name}_{uuid.uuid4().hex[:6]}.png"
    path = STATIC_DIR / filename
    img.save(path, format="PNG")
    return f"/static/{filename}"


def cleanup(urls: list[str]):
    for url in urls:
        p = STATIC_DIR / Path(url).name
        if p.exists():
            p.unlink()


# ─────────────────────────────────────────────────────────────────────────────

def test_pack():
    print("=== 精灵图打包测试 ===\n")

    # 1. 准备测试素材
    urls = []
    images = {}
    for label, w, h, color in SPRITES:
        img = make_sprite(w, h, color)
        url = save_sprite(img, label)
        urls.append(url)
        images[url] = (label, img)
        print(f"  创建素材: {label:12s}  {w:3d}×{h:3d}  -> {url}")
    print()

    failures = []

    # ── 测试 JSON 格式 ────────────────────────────────────────────────────────

    print("── 测试 JSON atlas 格式 ──")
    zip_bytes = pack(urls, atlas_format="json")
    assert len(zip_bytes) > 0, "ZIP 为空"

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "spritesheet.png" in names, f"ZIP 中缺少 spritesheet.png，实际：{names}"
        assert "atlas.json" in names, f"ZIP 中缺少 atlas.json，实际：{names}"

        sheet_bytes = zf.read("spritesheet.png")
        atlas_raw = zf.read("atlas.json").decode("utf-8")

    sheet = Image.open(io.BytesIO(sheet_bytes)).convert("RGBA")
    atlas = json.loads(atlas_raw)
    sheet_arr = np.array(sheet)

    print(f"  大图尺寸: {sheet.width}×{sheet.height}")
    print(f"  atlas 帧数: {len(atlas['frames'])}")

    # 检查帧数等于素材数
    if len(atlas["frames"]) != len(SPRITES):
        failures.append(f"帧数 {len(atlas['frames'])} != 素材数 {len(SPRITES)}")

    # 检查 meta.size 与实际大图一致
    meta_w = atlas["meta"]["size"]["w"]
    meta_h = atlas["meta"]["size"]["h"]
    if meta_w != sheet.width or meta_h != sheet.height:
        failures.append(f"meta.size ({meta_w}×{meta_h}) 与大图 ({sheet.width}×{sheet.height}) 不一致")

    # ── 核心验证：每帧坐标和大图像素对得上 ──────────────────────────────────
    print("\n── 坐标验证（逐帧）──")
    for frame in atlas["frames"]:
        name, x, y, fw, fh = frame["name"], frame["x"], frame["y"], frame["w"], frame["h"]
        label = name.replace(".png", "")

        # 坐标不超出大图边界
        if x + fw > sheet.width or y + fh > sheet.height:
            failures.append(f"{name}: 超出大图边界 (x={x} y={y} w={fw} h={fh}, sheet={sheet.width}×{sheet.height})")
            continue

        # 从大图中抠出该区域
        region = sheet_arr[y:y+fh, x:x+fw]  # [H, W, 4]

        # 透明通道保留检查：至少有一个像素 alpha > 0（精灵内容存在）
        has_opaque = (region[:, :, 3] > 0).any()
        if not has_opaque:
            failures.append(f"{name}: 大图对应区域全透明，内容丢失")

        # 透明角落保留检查：左上角 2×2 应该是透明的（因为我们画的是内切椭圆）
        corner_alpha = region[:2, :2, 3]
        corner_transparent = (corner_alpha == 0).all()

        print(f"  {label:12s}  x={x:4d} y={y:4d} w={fw:4d} h={fh:4d}"
              f"  有内容={'✓' if has_opaque else '✗'}"
              f"  透明角={'✓' if corner_transparent else '✗'}")

    # ── 不重叠检查：所有帧的矩形范围两两不相交 ──────────────────────────────
    print("\n── 不重叠检查 ──")
    frames = atlas["frames"]
    overlaps_found = False
    for i in range(len(frames)):
        for j in range(i + 1, len(frames)):
            a, b = frames[i], frames[j]
            # AABB 相交检测
            no_overlap = (
                a["x"] + a["w"] <= b["x"] or  # a 在 b 左
                b["x"] + b["w"] <= a["x"] or  # b 在 a 左
                a["y"] + a["h"] <= b["y"] or  # a 在 b 上
                b["y"] + b["h"] <= a["y"]     # b 在 a 上
            )
            if not no_overlap:
                failures.append(f"重叠：{frames[i]['name']} 与 {frames[j]['name']}")
                overlaps_found = True
    if not overlaps_found:
        print("  所有帧不重叠 ✓")

    # ── 测试 Godot 格式 ───────────────────────────────────────────────────────
    print("\n── 测试 Godot atlas 格式 ──")
    zip_bytes_g = pack(urls, atlas_format="godot")
    with zipfile.ZipFile(io.BytesIO(zip_bytes_g)) as zf:
        names_g = zf.namelist()
        assert "spritesheet.png" in names_g
        assert "atlas.tres" in names_g, f"ZIP 中缺少 atlas.tres，实际：{names_g}"
        tres = zf.read("atlas.tres").decode("utf-8")

    # 基本结构检查
    assert "[gd_resource" in tres, ".tres 缺少 gd_resource 头"
    assert "AtlasTexture" in tres, ".tres 缺少 AtlasTexture"
    assert "res://spritesheet.png" in tres, ".tres 缺少 spritesheet.png 引用"
    tres_frame_count = tres.count("sub_resource type=\"AtlasTexture\"")
    if tres_frame_count != len(SPRITES):
        failures.append(f"Godot .tres 中 AtlasTexture 数量 {tres_frame_count} != {len(SPRITES)}")
    else:
        print(f"  AtlasTexture 数量正确：{tres_frame_count} ✓")

    # 提取一帧坐标并验证出现在 .tres 中
    first_frame = atlas["frames"][0]
    expected_rect = f"Rect2({first_frame['x']}, {first_frame['y']}, {first_frame['w']}, {first_frame['h']})"
    if expected_rect in tres:
        print(f"  抽样坐标核对：{expected_rect} ✓")
    else:
        failures.append(f"Godot .tres 中未找到预期坐标 {expected_rect}")

    # 保存大图供人工抽查
    out_path = Path(__file__).parent / "test_spritesheet_output.png"
    sheet.save(out_path)
    out_atlas = Path(__file__).parent / "test_atlas_output.json"
    out_atlas.write_text(atlas_raw, encoding="utf-8")
    print(f"\n大图已保存至：{out_path}")
    print(f"JSON atlas 已保存至：{out_atlas}")

    # ── 汇总 ─────────────────────────────────────────────────────────────────
    print()
    if failures:
        print(f"❌ 失败 {len(failures)} 项：")
        for f in failures:
            print(f"   • {f}")
        sys.exit(1)
    else:
        print("✅ 全部测试通过")

    cleanup(urls)


if __name__ == "__main__":
    test_pack()
