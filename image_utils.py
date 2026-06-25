"""Image utilities — platform-specific resize + background removal.

PLATFORM_SIZES: per-marketplace recommended aspect ratios / sizes.
remove_bg() — optional rembg, falls back to identity if not installed.
"""
from __future__ import annotations
import io
from typing import Iterable

from PIL import Image, ImageOps


PLATFORM_SIZES: dict[str, dict] = {
    "shopee_main":   {"size": (1024, 1024), "fit": "pad_white"},
    "lazada_main":   {"size": (1024, 1024), "fit": "pad_white"},
    "tiktok_main":   {"size": (1080, 1080), "fit": "pad_white"},
    "tiktok_video":  {"size": (1080, 1920), "fit": "smart_crop"},
    "facebook_post": {"size": (1200, 630),  "fit": "smart_crop"},
    "line_thumb":    {"size": (1040, 1040), "fit": "pad_white"},
    "instagram":     {"size": (1080, 1080), "fit": "pad_white"},
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


# ---- v59: Studio pipeline (bulk-process product photos) ----------------

def studio_process(raw: bytes, *, size: int = 1080, bg: str = "white",
                   padding: float = 0.06) -> bytes:
    """One-pass marketplace-ready output:
       remove background → square crop with subject centered →
       resize to NxN (default 1080) → composite onto solid bg.

    `padding` (0.06 = 6% margin around the subject) — Shopee/Lazada like a
    little breathing room, not edge-to-edge.

    Returns JPEG bytes ready to upload. Falls back gracefully if rembg
    isn't available (just re-frames the original).
    """
    transparent = remove_bg(raw)
    img = _open(transparent)
    has_alpha = img.mode == "RGBA"

    # Crop to subject bounding box (alpha-aware)
    if has_alpha:
        bbox = img.split()[-1].getbbox()
    else:
        # Without alpha, use full frame
        bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # Pad to square
    w, h = img.size
    side = max(w, h)
    pad_px = int(side * padding * 2)   # padding on both sides
    canvas_side = side + pad_px
    bg_color = (255, 255, 255) if bg == "white" else (
        (251, 249, 243) if bg == "cream" else (0, 0, 0)
    )
    canvas = Image.new("RGB", (canvas_side, canvas_side), bg_color)
    paste_x = (canvas_side - w) // 2
    paste_y = (canvas_side - h) // 2
    if has_alpha:
        canvas.paste(img, (paste_x, paste_y), mask=img.split()[-1])
    else:
        canvas.paste(img, (paste_x, paste_y))

    # Final resize to target size (LANCZOS = high quality)
    canvas = canvas.resize((size, size), Image.LANCZOS)
    return to_bytes(canvas, fmt="JPEG", quality=92)
