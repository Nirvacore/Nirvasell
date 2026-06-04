"""Etsy CSV (uses Etsy's "Multi-listing import" format).

Etsy bulk import is in private beta for some shops; this CSV is also useful
as input for third-party tools like Vela / Marmalead."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock

import fees as fees_mod


HEADERS = [
    "Title", "Description", "Price", "Currency", "Quantity",
    "SKU", "Tags", "Materials", "Production Partner",
    "Section", "Shop Section ID",
    "Image 1", "Image 2", "Image 3", "Image 4", "Image 5",
    "Item Weight", "Item Length", "Item Width", "Item Height",
    "Who Made", "When Made", "Category",
]


def _img(row, i: int) -> str:
    val = row.get("image_url") or ""
    parts = [p for p in str(val).split("|") if p.strip()]
    return parts[i] if i < len(parts) else ""


def build(df: pd.DataFrame, currency: str = "USD") -> tuple[str, bytes]:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)

    for _, row in df.iterrows():
        if not row.get("title"):
            continue
        sell_thb = float(row.get("sell_price") or 0)
        price = fees_mod.convert_from_thb(sell_thb, currency)
        tags = ",".join((row.get("tags") or "").split(",")[:13])  # Etsy max 13

        w.writerow([
            row["title"][:140],
            row.get("description", ""),
            f"{price:.2f}", currency,
            parse_stock(row.get("stock")),
            row["sku"], tags,
            "", "",
            "", "",
            _img(row, 0), _img(row, 1), _img(row, 2), _img(row, 3), _img(row, 4),
            500, 20, 15, 10,
            "i_did", "made_to_order", row.get("category", ""),
        ])

    name = f"etsy_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return name, buf.getvalue().encode("utf-8-sig")
