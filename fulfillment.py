"""Order fulfillment — close the loop from "order imported" to "shipped":
  1. List pending orders (status='paid', no tracking yet)
  2. Bulk assign carrier + tracking numbers
  3. Export per-marketplace tracking-update CSVs (user uploads to platform)
  4. Generate printable shipping labels (HTML, user prints from browser)
  5. Inventory decrement — auto-reduce product stock on import

Most TH marketplaces (Shopee/Lazada/TikTok) accept a bulk-shipment CSV upload
to mark orders shipped + attach tracking. Each has a different shape but the
fields we need are the same: order_id, tracking_no, carrier_code. We generate
one CSV per platform; user uploads each in the platform's seller backoffice."""
from __future__ import annotations
import csv
import io
import re
from datetime import datetime

import db


# ---- Migrations ---------------------------------------------------------
# Add fulfillment columns to existing orders table. SQLite ALTER TABLE is
# limited but ADD COLUMN works fine. We probe `PRAGMA table_info` to make it
# idempotent across upgrades.

_FULFILLMENT_COLUMNS = {
    "tracking_number": "TEXT",
    "carrier":         "TEXT",
    "shipped_at":      "TEXT",
    "buyer_name":      "TEXT",
    "buyer_address":   "TEXT",
    "buyer_phone":     "TEXT",
}


def init():
    db.init()
    with db.conn() as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(orders)").fetchall()}
        for name, sql_type in _FULFILLMENT_COLUMNS.items():
            if name not in cols:
                c.execute(f"ALTER TABLE orders ADD COLUMN {name} {sql_type}")


# ---- Carrier codes per platform ----------------------------------------
# Each marketplace recognizes a specific set of carrier codes in their bulk
# upload. These are the common ones in Thailand.

CARRIERS = {
    "kerry":     {"shopee": "KERRY",     "lazada": "KE",   "tiktok": "KEX"},
    "flash":     {"shopee": "FLASH",     "lazada": "FLE",  "tiktok": "FLE"},
    "thaipost":  {"shopee": "TH_POST",   "lazada": "THP",  "tiktok": "THP"},
    "j&t":       {"shopee": "JT",        "lazada": "JT",   "tiktok": "JT"},
    "ninjavan":  {"shopee": "NINJA_VAN", "lazada": "NJV",  "tiktok": "NJV"},
    "best":      {"shopee": "BEST",      "lazada": "BEST", "tiktok": "BEST"},
    "scg":       {"shopee": "SCG",       "lazada": "SCG",  "tiktok": "SCG"},
    "dhl":       {"shopee": "DHL",       "lazada": "DHL",  "tiktok": "DHL"},
}


def carrier_options() -> list[tuple[str, str]]:
    from i18n_inline import carrier_name
    return [(k, carrier_name(k)) for k in CARRIERS]


def platform_code(carrier_key: str, platform: str) -> str:
    """Translate a carrier key to the platform's expected code."""
    entry = CARRIERS.get(carrier_key.lower())
    if not entry:
        return carrier_key.upper()
    from i18n_inline import carrier_name
    return entry.get(platform.lower(), carrier_name(carrier_key))


# ---- Pending orders -----------------------------------------------------

def pending_orders(platform: str | None = None) -> list[dict]:
    """Orders that haven't been shipped yet."""
    init()
    where = "WHERE tracking_number IS NULL OR tracking_number = ''"
    params: tuple = ()
    if platform:
        where += " AND platform = ?"
        params = (platform,)
    with db.conn() as c:
        rows = c.execute(
            f"""SELECT o.*, p.name AS product_name, p.image_url
                FROM orders o
                LEFT JOIN products p ON p.id = o.product_id
                {where}
                ORDER BY o.order_date DESC, o.id DESC""",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def shipped_orders(limit: int = 200) -> list[dict]:
    init()
    with db.conn() as c:
        rows = c.execute(
            """SELECT o.*, p.name AS product_name
               FROM orders o
               LEFT JOIN products p ON p.id = o.product_id
               WHERE tracking_number IS NOT NULL AND tracking_number != ''
               ORDER BY shipped_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def platforms_with_pending() -> list[str]:
    init()
    with db.conn() as c:
        rows = c.execute(
            """SELECT DISTINCT platform FROM orders
               WHERE (tracking_number IS NULL OR tracking_number = '')
               ORDER BY platform"""
        ).fetchall()
    return [r["platform"] for r in rows if r["platform"]]


# ---- Mark as shipped ----------------------------------------------------

def mark_shipped(order_id_db: int, *, tracking_number: str,
                 carrier: str, decrement_stock: bool = True) -> bool:
    """Set tracking + shipped_at + status='shipped'. Optionally decrement stock."""
    init()
    if not tracking_number.strip():
        return False
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.conn() as c:
        # Read the order to know qty + product_id for stock decrement
        row = c.execute(
            "SELECT product_id, qty FROM orders WHERE id = ?", (order_id_db,)
        ).fetchone()
        c.execute(
            """UPDATE orders SET tracking_number = ?, carrier = ?,
                                 shipped_at = ?, status = 'shipped'
               WHERE id = ?""",
            (tracking_number.strip(), carrier.strip().lower(), now, order_id_db),
        )
        if decrement_stock and row and row["product_id"]:
            # Stock is stored as a free-text string in products.stock — try to
            # parse a number out and decrement. Leave non-numeric stock as-is.
            stock_row = c.execute(
                "SELECT stock FROM products WHERE id = ?", (row["product_id"],)
            ).fetchone()
            if stock_row and stock_row["stock"]:
                m = re.search(r"\d+", str(stock_row["stock"]))
                if m:
                    new_n = max(0, int(m.group(0)) - int(row["qty"] or 1))
                    new_stock = re.sub(r"\d+", str(new_n), str(stock_row["stock"]), count=1)
                    c.execute(
                        "UPDATE products SET stock = ? WHERE id = ?",
                        (new_stock, row["product_id"]),
                    )
    return True


def mark_shipped_bulk(items: list[dict]) -> int:
    """items = [{'id': db_order_id, 'tracking_number': ..., 'carrier': ...}, ...]
    Returns count of orders updated."""
    ok = 0
    for it in items:
        if mark_shipped(
            it["id"],
            tracking_number=it.get("tracking_number", "").strip(),
            carrier=it.get("carrier", "").strip(),
        ):
            ok += 1
    return ok


# ---- Per-platform shipment CSV exports ---------------------------------
# Each platform's "bulk shipping" CSV has a different column shape. The
# operator downloads the CSV here and uploads it in the seller backoffice.

def shipment_csv_shopee(rows: list[dict]) -> bytes:
    """Shopee bulk shipment CSV (TH backoffice)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Order ID", "Tracking Number", "Shipping Channel"])
    for r in rows:
        w.writerow([
            r["order_id"],
            r.get("tracking_number", ""),
            platform_code(r.get("carrier", ""), "shopee"),
        ])
    return buf.getvalue().encode("utf-8-sig")


def shipment_csv_lazada(rows: list[dict]) -> bytes:
    """Lazada bulk shipment CSV."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["OrderItemId", "TrackingNumber", "ShipmentProvider"])
    for r in rows:
        w.writerow([
            r["order_id"],
            r.get("tracking_number", ""),
            platform_code(r.get("carrier", ""), "lazada"),
        ])
    return buf.getvalue().encode("utf-8-sig")


def shipment_csv_tiktok(rows: list[dict]) -> bytes:
    """TikTok Shop bulk shipment CSV."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Order ID", "Tracking ID", "Shipping Provider"])
    for r in rows:
        w.writerow([
            r["order_id"],
            r.get("tracking_number", ""),
            platform_code(r.get("carrier", ""), "tiktok"),
        ])
    return buf.getvalue().encode("utf-8-sig")


def shipment_csv_generic(rows: list[dict]) -> bytes:
    """Fallback: generic columns that any platform can probably consume."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["order_id", "platform", "sku", "qty", "tracking_number",
                "carrier", "shipped_at"])
    for r in rows:
        w.writerow([
            r["order_id"], r.get("platform", ""), r.get("sku", ""),
            r.get("qty", 1), r.get("tracking_number", ""),
            platform_code(r.get("carrier", ""), r.get("platform", "")),
            r.get("shipped_at", ""),
        ])
    return buf.getvalue().encode("utf-8-sig")


PLATFORM_CSV = {
    "shopee": shipment_csv_shopee,
    "lazada": shipment_csv_lazada,
    "tiktok": shipment_csv_tiktok,
}


def shipment_csv_for(platform: str, rows: list[dict]) -> bytes:
    fn = PLATFORM_CSV.get((platform or "").lower(), shipment_csv_generic)
    return fn(rows)


# ---- Printable shipping label (HTML) -----------------------------------

def label_html(orders: list[dict], *, seller_name: str = "",
               seller_address: str = "") -> str:
    """Generate a print-friendly HTML page — one label per order, A6-ish."""
    cards = []
    for o in orders:
        cards.append(f"""
        <div class='label'>
          <div class='from'>
            <div class='small'>FROM</div>
            <div class='strong'>{_html(seller_name) or 'Seller'}</div>
            <div class='small'>{_html(seller_address)}</div>
          </div>
          <div class='to'>
            <div class='small'>TO</div>
            <div class='strong'>{_html(o.get('buyer_name') or '—')}</div>
            <div>{_html(o.get('buyer_address') or '—')}</div>
            <div class='small'>{_html(o.get('buyer_phone') or '')}</div>
          </div>
          <div class='order'>
            <div class='row'><span>Order</span><span class='mono'>{_html(o.get('order_id',''))}</span></div>
            <div class='row'><span>SKU</span><span class='mono'>{_html(o.get('sku',''))}</span></div>
            <div class='row'><span>Qty</span><span>{_html(o.get('qty',1))}</span></div>
            <div class='row'><span>Carrier</span><span>{_html((o.get('carrier','') or '').upper())}</span></div>
            <div class='row'><span>Track</span><span class='mono large'>{_html(o.get('tracking_number',''))}</span></div>
            <div class='row'><span>Platform</span><span>{_html(o.get('platform',''))}</span></div>
          </div>
        </div>
        """)

    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Shipping labels</title>
<style>
  @media print {{ .no-print {{ display:none }} body {{ background:white }} }}
  body {{ font-family:-apple-system,Helvetica,Arial,sans-serif;
         background:#f7f4ec; color:#1f1f1f; margin:0; padding:20px; }}
  .label {{ background:white; border:2px dashed #888; border-radius:6px;
            padding:16px; margin:0 0 14px; page-break-inside:avoid;
            display:grid; grid-template-columns:1fr 1fr; gap:14px;
            grid-template-areas: 'from to' 'order order'; }}
  .from {{ grid-area:from }} .to {{ grid-area:to }} .order {{ grid-area:order;
           border-top:1px solid #ddd; padding-top:10px }}
  .small {{ font-size:11px; color:#666; text-transform:uppercase; letter-spacing:.5px }}
  .strong {{ font-weight:600; font-size:15px; margin:2px 0 }}
  .row {{ display:flex; justify-content:space-between; font-size:13px; padding:2px 0 }}
  .mono {{ font-family:Menlo,monospace }}
  .large {{ font-size:16px; font-weight:600 }}
  .controls {{ margin-bottom:18px; text-align:right }}
  .controls button {{ background:#4d6c5c; color:white; border:none;
                      padding:8px 18px; border-radius:6px; cursor:pointer;
                      font-size:14px }}
</style>
</head><body>
<div class='controls no-print'>
  <button onclick='window.print()'>🖨 Print</button>
</div>
{''.join(cards)}
</body></html>"""


def _html(s) -> str:
    """Escape user content for HTML output."""
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;").replace('"', "&quot;"))


# ---- Stats --------------------------------------------------------------

def stats() -> dict:
    init()
    with db.conn() as c:
        pend = c.execute(
            """SELECT COUNT(*) FROM orders
               WHERE tracking_number IS NULL OR tracking_number = ''"""
        ).fetchone()[0]
        ship = c.execute(
            """SELECT COUNT(*) FROM orders
               WHERE tracking_number IS NOT NULL AND tracking_number != ''"""
        ).fetchone()[0]
        platforms = c.execute(
            """SELECT platform, COUNT(*) AS n FROM orders
               WHERE tracking_number IS NULL OR tracking_number = ''
               GROUP BY platform"""
        ).fetchall()
    return {
        "pending": pend,
        "shipped": ship,
        "pending_by_platform": {r["platform"]: r["n"] for r in platforms},
    }
