"""Lazada TH bulk-upload CSV. Headers match Lazada Seller Center →
Products → Add Products in Bulk → generic template."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock


HEADERS = [
    "SellerSku", "Name", "Brand", "Description",
    "Price", "Quantity", "PackageWeight",
    "PackageLength", "PackageWidth", "PackageHeight",
    "Image 1", "Image 2", "Image 3", "Image 4", "Image 5",
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
            row["sku"], row["title"],
            row.get("brand", "") or "No Brand",
            row.get("description", ""),
            int(row.get("sell_price") or 0),
            parse_stock(row.get("stock")),
            0.5, 20, 15, 10,
            _img(row, 0), _img(row, 1), _img(row, 2), _img(row, 3), _img(row, 4),
        ])
    name = f"lazada_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return name, buf.getvalue().encode("utf-8-sig")
