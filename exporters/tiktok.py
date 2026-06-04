"""TikTok Shop TH bulk-upload CSV. Confirm against the category-specific
template from Seller Center → Products → Add Multiple Products."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock


HEADERS = [
    "Product Name", "Category", "Brand", "Description",
    "Seller SKU", "Stock", "Price",
    "Package Weight (kg)", "Package Length (cm)", "Package Width (cm)", "Package Height (cm)",
    "Main Image", "Image 2", "Image 3", "Image 4", "Image 5",
]


def _img(row, i: int) -> str:
    val = row.get("image_url") or ""
    parts = [p for p in str(val).split("|") if p.strip()]
    return parts[i] if i < len(parts) else ""


def build(df: pd.DataFrame, currency: str = "THB") -> tuple[str, bytes]:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)
    for _, row in df.iterrows():
        if not row.get("title"):
            continue
        w.writerow([
            row["title"],
            row.get("category", "") or "",
            row.get("brand", "") or "",
            row.get("description", ""),
            row["sku"],
            parse_stock(row.get("stock")),
            int(row.get("sell_price") or 0),
            0.5, 20, 15, 10,
            _img(row, 0), _img(row, 1), _img(row, 2), _img(row, 3), _img(row, 4),
        ])
    name = f"tiktok_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return name, buf.getvalue().encode("utf-8-sig")
