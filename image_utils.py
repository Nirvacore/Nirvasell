"""Image utilities — platform-specific resize + background removal.

PLATFORM_SIZES: per-marketplace recommended aspect ratios / sizes.
remove_bg() — optional rembg, falls back to identity if not installed.
"""
from __future__ import annotations
import io
from typing import Iterable

from PIL import Image, ImageOps


PLATFORM_SIZES: dict[str, dict] = {
    "shopee_main":   {"label": "Shopee main",          "size": (1024, 1024), "fit": "pad_white"},
    "lazada_main":   {"label": "Lazada main",          "size": (1024, 1024), "fit": "pad_white"},
    "tiktok_main":   {"label": "TikTok Shop main",     "size": (1080, 1080), "fit": "pad_white"},
    "tiktok_video":  {"label": "TikTok video cover",   "size": (1080, 1920), "fit": "smart_crop"},
    "facebook_post": {"label": "Facebook post",        "size": (1200, 630),  "fit": "smart_crop"},
    "line_thumb":    {"label": "LINE thumbnail",       "size": (1040, 1040), "fit": "pad_white"},
    "instagram":     {"label": "Instagram square",     "size": (1080, 1080), "fit": "pad_white"},
}


def _open(raw: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(raw))
    # Apply EXIF orientation so phone photos don't end up sideways.
    img = ImageOps.exif_transpose(img)
    return img.convert("RGBA") if img.mode in ("P", "RGBA") else img.convert("RGB")


def to_bytes(img: Image.Image, fmt: str = "JPEG", quality: int = 90) -> bytes:
    buf = io.BytesIO()
    if fmt.upper() == "JPEG" and img.mode == "RGBA":
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    img.save(buf, format=fmt, quality=quality, optimize=True)
    return buf.getvalue()


def resize_for(raw: bytes, preset: str) -> bytes:
    """Resize an image to fit a marketplace preset."""
    if preset not in PLATFORM_SIZES:
        raise ValueError(f"Unknown preset: {preset}")
    cfg = PLATFORM_SIZES[preset]
    target_w, target_h = cfg["size"]
    img = _open(raw)

    if cfg["fit"] == "pad_white":
        # Letterbox to a white square — preserves the whole product.
        return to_bytes(ImageOps.pad(img, (target_w, target_h), color=(255, 255, 255)))
    if cfg["fit"] == "smart_crop":
        # Crop+fill to fully fill target aspect. Pillow's `fit` centers by default.
        return to_bytes(ImageOps.fit(img, (target_w, target_h)))
    # Plain resize as fallback.
    return to_bytes(img.resize((target_w, target_h)))


def batch_resize(raw: bytes, presets: Iterable[str]) -> dict[str, bytes]:
    """Resize one input into multiple presets at once."""
    return {p: resize_for(raw, p) for p in presets}


def remove_bg(raw: bytes) -> bytes:
    """Remove background using rembg. Falls back to original bytes if rembg
    isn't installed (first-call model download can be slow ~175MB)."""
    try:
        from rembg import remove  # type: ignore
    except ImportError:
        return raw
    return remove(raw)


def remove_bg_then_white(raw: bytes) -> bytes:
    """Background-remove then composite onto pure white — what marketplaces want."""
    transparent = remove_bg(raw)
    img = _open(transparent)
    if img.mode != "RGBA":
        return to_bytes(img)
    bg = Image.new("RGB", img.size, "white")
    bg.paste(img, mask=img.split()[-1])
    return to_bytes(bg)
