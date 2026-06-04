"""Shopify Products CSV — the most portable marketplace format.

Works with the user's own Shopify store in any country. Header names match
Shopify's official import schema (Products → Import)."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock

import fees as fees_mod


HEADERS = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags",
    "Published", "Option1 Name", "Option1 Value", "SKU", "Variant Grams",
    "Variant Inventory Tracker", "Variant Inventory Qty",
    "Variant Inventory Policy", "Variant Fulfillment Service",
    "Variant Price", "Variant Compare At Price",
    "Variant Requires Shipping", "Variant Taxable", "Variant Barcode",
    "Image Src", "Image Position", "Image Alt Text",
    "Gift Card", "SEO Title", "SEO Description",
    "Status",
]


def _img(row, i: int) -> str:
    val = row.get("image_url") or ""
    parts = [p for p in str(val).split("|") if p.strip()]
    return parts[i] if i < len(parts) else ""


def _handle(name: str, sku: str) -> str:
    base = name or sku
    return "".join(c.lower() if c.isalnum() else "-" for c in base)[:100]


def build(df: pd.DataFrame, currency: str = "USD") -> tuple[str, bytes]:
    """One row per image (Shopify quirk — multiple images = multiple CSV rows
    sharing the same Handle). We just emit the cover image to keep it simple;
    additional rows can be added in Shopify Admin."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)

    for _, row in df.iterrows():
        if not row.get("title"):
            continue
        sell_thb = float(row.get("sell_price") or 0)
        price = fees_mod.convert_from_thb(sell_thb, currency)
        cost_thb = float(row.get("cost_price") or 0)
        compare_at = fees_mod.convert_from_thb(cost_thb * 1.5, currency)  # MSRP hint
        handle = _handle(row.get("name", ""), row["sku"])

        body_html = (row.get("description") or "").replace("\n", "<br>")
        tags = row.get("tags", "")

        w.writerow([
            handle,
            row["title"],
            body_html,
            row.get("brand", ""),
            row.get("category", ""),
            tags,
            "TRUE",
            "Title", "Default Title",
            row["sku"],
            500,
            "shopify",
            parse_stock(row.get("stock")),
            "deny",
            "manual",
            f"{price:.2f}",
            f"{compare_at:.2f}",
            "TRUE", "TRUE", "",
            _img(row, 0), 1, row.get("title", "")[:120],
            "FALSE",
            row.get("title", "")[:60],
            (row.get("description") or "")[:160],
            "active",
        ])

    name = f"shopify_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return name, buf.getvalue().encode("utf-8-sig")
