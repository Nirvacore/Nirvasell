"""Amazon Seller Central Flat File CSV (simplified Inventory Loader format).

Amazon's full template has 200+ columns and varies per category. This emits
the minimum subset that Seller Central will accept for the "Inventory Loader"
upload. Users typically still need to enrich category-specific fields in
Seller Central before going live."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock

import fees as fees_mod


HEADERS = [
    "sku", "product-id", "product-id-type",
    "price", "minimum-seller-allowed-price", "maximum-seller-allowed-price",
    "item-condition", "quantity", "add-delete",
    "will-ship-internationally", "expedited-shipping",
    "product-tax-code", "leadtime-to-ship",
    "item-name", "item-description", "image-url",
]


def build(df: pd.DataFrame, currency: str = "USD") -> tuple[str, bytes]:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t")  # Amazon flat-files are tab-separated
    w.writerow(HEADERS)

    for _, row in df.iterrows():
        if not row.get("title"):
            continue
        sell_thb = float(row.get("sell_price") or 0)
        price = fees_mod.convert_from_thb(sell_thb, currency)
        min_p = price * 0.9
        max_p = price * 1.5
        img = (row.get("image_url") or "").split("|")[0]

        w.writerow([
            row["sku"], row["sku"], "1",  # 1 = ASIN/SKU, may need product-id-type=4 (EAN/UPC)
            f"{price:.2f}", f"{min_p:.2f}", f"{max_p:.2f}",
            "11",  # New
            parse_stock(row.get("stock")), "a",
            "false", "false",
            "", "2",
            row["title"][:200],
            (row.get("description") or "")[:2000],
            img,
        ])

    name = f"amazon_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    return name, buf.getvalue().encode("utf-8")
