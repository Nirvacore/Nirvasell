"""QR code generation for products. Used in Catalog product detail panel
so resellers can print QR labels linking to marketplace listing or landing
page."""
from __future__ import annotations
import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def make_png(text: str, box_size: int = 10, border: int = 2) -> bytes:
    """Return PNG bytes of a QR code encoding `text`."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1f1f1f", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def shopee_search_url(sku: str) -> str:
    """Convenience: a QR pointing at the Shopee TH search for this SKU."""
    return f"https://shopee.co.th/search?keyword={sku}"


def lazada_search_url(sku: str) -> str:
    return f"https://www.lazada.co.th/catalog/?q={sku}"
