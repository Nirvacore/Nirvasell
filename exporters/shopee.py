"""Shopee TH mass-upload CSV. Confirm headers against the latest template from
Seller Centre → Products → Mass Upload before each campaign."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock


HEADERS = [
    "Product Name", "Product Description", "Variation Name 1", "Variation Name 2",
    "Category", "Brand", "SKU", "Stock", "Price",
    "Weight", "Length", "Width", "Height",
    "Cover image", "Image 1", "Image 2", "Image 3", "Image 4",
]


def _img(row, i: int) -> str:
    val = row.get("image_url") or ""
    parts = [p for p in str(val).split("|") if p.strip()]
    return parts[i] if i < len(parts) else ""


def build(df: pd.DataFrame, currency: str = "THB") -> tuple[str, bytes]:
    """Shopee TH always uses THB regardless of currency parameter."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)
    for _, row in df.iterrows():
        if not row.get("title"):
            continue
        w.writerow([
            row["title"], row.get("description", ""),
            "", "",
            row.get("category", "") or "",
            row.get("brand", "") or "",
            row["sku"],
            parse_stock(row.get("stock")),
            int(row.get("sell_price") or 0),
            500, 20, 15, 10,
            _img(row, 0), _img(row, 0), _img(row, 1), _img(row, 2), _img(row, 3),
        ])
    name = f"shopee_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return name, buf.getvalue().encode("utf-8-sig")
