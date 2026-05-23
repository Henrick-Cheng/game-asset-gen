from dataclasses import dataclass


@dataclass(frozen=True)
class AssetType:
    id: str
    name: str
    suffix: str


ASSET_TYPES: dict[str, AssetType] = {
    "character": AssetType(
        id="character",
        name="角色精灵",
        suffix=(
            "full body character, centered composition, neutral idle pose, "
            "clear silhouette, suitable for 2D game sprite animation, white background"
        ),
    ),
    "icon": AssetType(
        id="icon",
        name="道具图标",
        suffix=(
            "single object, simple clean design, centered, "
            "UI item icon style, high contrast, transparent-friendly background"
        ),
    ),
    "tile": AssetType(
        id="tile",
        name="地块贴图",
        suffix=(
            "seamless tileable texture, uniform pattern, "
            "top-down or isometric view, suitable for 2D game map tiling, no focal point"
        ),
    ),
}

DEFAULT_ASSET_TYPE_ID = "character"
