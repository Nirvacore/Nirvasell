"""Bridge: import products + images from a reseller/ SQLite DB into nirva.

This lets a power-user pipe their scraped Synnex / VSTECS / Solar Shop data
straight into nirva without manual CSV export. Reseller's DB stays untouched —
we only read.

Usage in app: see pages/5_🔌_Import.py
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd

import db
import parser as nirva_parser


def default_reseller_db() -> Path:
    """Probe for a reseller/ SQLite DB next to this project."""
    here = Path(__file__).resolve().parent
    # Try common locations relative to where nirva/ might live.
    candidates = [
        here.parent / "reseller" / "data" / "products.db",
        here.parent.parent / "reseller" / "data" / "products.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]  # return non-existent default for UI display


def inspect(reseller_db: Path) -> dict:
    """Quick stats on what's in the reseller DB. Returns empty if not found."""
    if not reseller_db.exists():
        return {"exists": False, "path": str(reseller_db)}
    c = sqlite3.connect(str(reseller_db))
    c.row_factory = sqlite3.Row
    try:
        n_products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        n_with_images = c.execute(
            "SELECT COUNT(DISTINCT product_id) FROM images"
        ).fetchone()[0]
        n_uploaded = c.execute(
            "SELECT COUNT(*) FROM images WHERE remote_url IS NOT NULL"
        ).fetchone()[0]
        last = c.execute("SELECT MAX(scraped_at) FROM products").fetchone()[0]
        sources = {
            r["source"]: r["n"]
            for r in c.execute(
                "SELECT source, COUNT(*) AS n FROM products GROUP BY source"
            ).fetchall()
        }
        return {
            "exists": True,
            "path": str(reseller_db),
            "products": n_products,
            "products_with_images": n_with_images,
            "images_uploaded": n_uploaded,
            "last_scrape": last,
            "sources": sources,
        }
    finally:
        c.close()


def fetch_products_df(reseller_db: Path, markup: float, round_to: int) -> pd.DataFrame:
    """Read all products + concatenated image URLs from the reseller DB.

    Image URL priority: Cloudinary remote_url > local file path. Multiple images
    are concatenated with '|' (matches nirva's existing schema).
    """
    c = sqlite3.connect(str(reseller_db))
    c.row_factory = sqlite3.Row
    try:
        rows = c.execute(
            """
            SELECT
              p.source, p.sku, p.name, p.brand, p.category,
              p.cost_price, p.stock, p.specs,
              (SELECT GROUP_CONCAT(COALESCE(remote_url, local_path), '|')
               FROM images i WHERE i.product_id = p.id ORDER BY i.position) AS image_url
            FROM products p
            """
        ).fetchall()
    finally:
        c.close()

    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        return df

    # Prefix SKU with source so multi-supplier sets don't collide.
    df["sku"] = df["source"].str.upper() + "-" + df["sku"].astype(str)
    df = df.drop(columns=["source"])

    # Apply markup. cost_price may be None for a few rows — drop them.
    df = df[df["cost_price"].notna() & (df["cost_price"] > 0)].reset_index(drop=True)
    df["sell_price"] = df["cost_price"].apply(
        lambda c: nirva_parser.markup_price(float(c), markup, round_to)
    )
    return df


def import_into_nirva(reseller_db: Path, markup: float, round_to: int) -> int:
    """Pull from reseller DB and upsert into nirva's DB. Returns row count."""
    df = fetch_products_df(reseller_db, markup, round_to)
    if df.empty:
        return 0
    batch_id = db.create_batch(f"reseller://{reseller_db.name}", len(df))
    return db.upsert_products(df, batch_id)
