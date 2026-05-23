from dataclasses import dataclass


@dataclass(frozen=True)
class StylePreset:
    id: str
    name: str
    suffix: str


STYLE_PRESETS: dict[str, StylePreset] = {
    "pixel-art": StylePreset(
        id="pixel-art",
        name="像素风",
        suffix=(
            "pixel art, 16-bit retro game sprite, crisp hard edges, "
            "limited color palette, no anti-aliasing, classic RPG style"
        ),
    ),
    "flat-vector": StylePreset(
        id="flat-vector",
        name="扁平矢量",
        suffix=(
            "flat vector illustration, clean bold outlines, solid colors, "
            "minimalist 2D design, no gradients, game icon style, SVG-like"
        ),
    ),
    "hand-drawn": StylePreset(
        id="hand-drawn",
        name="手绘卡通",
        suffix=(
            "hand-drawn cartoon illustration, expressive ink lines, "
            "soft watercolor fill, whimsical playful style, children's book art"
        ),
    ),
}

DEFAULT_STYLE_ID = "pixel-art"
