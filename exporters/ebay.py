"""eBay Bulk Listing CSV (File Exchange format).

eBay's File Exchange requires very specific headers. This generates the
minimum needed for fixed-price US listings. For different sites (UK, AU, DE),
swap the `Site` value."""
from __future__ import annotations
import io
import csv
from datetime import datetime
import pandas as pd
from inventory import parse_stock

import fees as fees_mod


HEADERS = [
    "Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
    "Category", "ConditionID", "Title", "Description",
    "PicURL", "Quantity", "Format", "StartPrice",
    "Duration", "Location", "ShippingType",
    "ShippingService-1:Option", "ShippingService-1:Cost",
    "DispatchTimeMax", "ReturnsAcceptedOption",
    "PayPalAccepted", "Currency",
    "C:Brand",
]


def build(df: pd.DataFrame, currency: str = "USD") -> tuple[str, bytes]:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)

    for _, row in df.iterrows():
        if not row.get("title"):
            continue
        sell_thb = float(row.get("sell_price") or 0)
        price = fees_mod.convert_from_thb(sell_thb, currency)
        img = (row.get("image_url") or "").split("|")[0]
        desc_html = (row.get("description") or "").replace("\n", "<br>")

        w.writerow([
            "Add",
            "0",  # 0 = needs category lookup; user sets in Seller Hub
            "1000",  # 1000 = New
            row["title"][:80],
            desc_html[:50000],
            img,
            parse_stock(row.get("stock")),
            "FixedPriceItem",
            f"{price:.2f}",
            "GTC",
            "TH",
            "Flat",
            "InternationalPriorityShipping", "0.00",
            "3", "ReturnsAccepted",
            "1", currency,
            row.get("brand", ""),
        ])

    name = f"ebay_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return name, buf.getvalue().encode("utf-8-sig")
