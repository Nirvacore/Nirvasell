"""Multi-marketplace order CSV importer.

Each marketplace exports orders in a different shape. We auto-detect the
shape by looking at column names, then map to our canonical order schema.

Canonical fields: order_id, sku, qty, unit_price, total_price, currency,
                  order_date, status, platform"""
from __future__ import annotations
import io
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

import db
from order_dates import order_business_date


# Per-marketplace column aliases (lowercase substring match)
SCHEMAS: dict[str, dict[str, list[str]]] = {
    "shopee": {
        "order_id":    ["order id", "หมายเลขคำสั่งซื้อ", "เลขที่คำสั่งซื้อ"],
        "sku":         ["sku", "รหัส sku", "parent sku"],
        "qty":         ["quantity", "จำนวน", "qty"],
        "unit_price":  ["original price", "ราคาสินค้า"],
        "total_price": ["total amount", "ยอดรวม", "subtotal"],
        "order_date":  ["order creation date", "วันที่สั่งซื้อ", "create time"],
        "status":      ["order status", "สถานะ"],
        "buyer_name":  ["ชื่อผู้ซื้อ", "buyer name", "recipient name", "ชื่อผู้รับ"],
        "buyer_phone": ["เบอร์โทรผู้ซื้อ", "buyer phone", "phone"],
        "buyer_address": ["ที่อยู่ผู้ซื้อ", "buyer address", "recipient address", "ที่อยู่ผู้รับ"],
        "product_name": ["ชื่อสินค้า", "product name", "item name"],
    },
    "lazada": {
        "order_id":    ["orderitemid", "order number", "เลขออเดอร์", "order id"],
        "sku":         ["sellersku", "seller sku", "sku"],
        "qty":         ["quantity"],
        "unit_price":  ["paid price", "unit price"],
        "total_price": ["paid price", "order total", "total"],
        "order_date":  ["created at", "create time", "order date"],
        "status":      ["status", "order status"],
        "buyer_name":  ["customer name", "buyer name", "customer first name"],
        "buyer_phone": ["phone", "customer phone"],
        "buyer_address": ["shipping address", "billing address", "customer address"],
        "product_name": ["item name", "product name"],
    },
    "tiktok": {
        "order_id":    ["order id", "order number"],
        "sku":         ["sku id", "seller sku", "sku"],
        "qty":         ["quantity"],
        "unit_price":  ["sku unit original price", "price"],
        "total_price": ["order amount", "sub total"],
        "order_date":  ["created time", "order created time"],
        "status":      ["order status"],
        "buyer_name":  ["buyer name", "recipient name", "recipient"],
        "buyer_phone": ["buyer phone", "phone number"],
        "buyer_address": ["buyer address", "recipient address", "shipping address"],
        "product_name": ["product name", "sku name"],
    },
    "shopify": {
        "order_id":    ["name", "order id"],
        "sku":         ["lineitem sku", "sku"],
        "qty":         ["lineitem quantity", "quantity"],
        "unit_price":  ["lineitem price"],
        "total_price": ["total", "subtotal"],
        "order_date":  ["created at", "processed at"],
        "status":      ["financial status", "fulfillment status"],
        "buyer_name":  ["shipping name", "billing name", "customer name"],
        "buyer_phone": ["shipping phone", "billing phone", "phone"],
        "buyer_address": ["shipping address", "billing address", "address"],
        "product_name": ["lineitem name"],
    },
    "amazon": {
        "order_id":    ["amazon-order-id", "order-id"],
        "sku":         ["sku"],
        "qty":         ["quantity-purchased", "quantity"],
        "unit_price":  ["item-price"],
        "total_price": ["item-price"],
        "order_date":  ["purchase-date"],
        "status":      ["order-status"],
        "buyer_name":  ["buyer-name", "recipient-name"],
        "buyer_phone": ["buyer-phone-number", "ship-phone-number"],
        "buyer_address": ["ship-address-1", "shipping-address", "buyer-address"],
        "product_name": ["product-name", "item-name"],
    },
}


def _norm(s: str) -> str:
    return str(s).strip().lower()


def detect_platform(columns: list[str]) -> str | None:
    """Guess which marketplace this CSV is from based on column names."""
    cols_l = [_norm(c) for c in columns]
    best, best_score = None, 0
    for platform, alias_map in SCHEMAS.items():
        score = 0
        for canonical, aliases in alias_map.items():
            for alias in aliases:
                if any(alias in c for c in cols_l):
                    score += 1
                    break
        if score > best_score:
            best, best_score = platform, score
    return best if best_score >= 3 else None


def map_columns(columns: list[str], platform: str) -> dict[str, str | None]:
    """Return {canonical: actual_column_name | None}."""
    cols_l = [(c, _norm(c)) for c in columns]
    alias_map = SCHEMAS.get(platform, {})
    out: dict[str, str | None] = {}
    for canonical, aliases in alias_map.items():
        match = None
        for alias in aliases:
            for orig, lc in cols_l:
                if alias in lc:
                    match = orig
                    break
            if match:
                break
        out[canonical] = match
    return out


def read_orders_csv(raw: bytes, filename: str = "") -> pd.DataFrame:
    """Read any marketplace order export. Tries multiple encodings."""
    for enc in ("utf-8-sig", "utf-8", "cp874"):
        try:
            if filename.endswith((".xlsx", ".xls")):
                return pd.read_excel(io.BytesIO(raw), dtype=str)
            return pd.read_csv(io.BytesIO(raw), dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            try:
                return pd.read_csv(io.BytesIO(raw), dtype=str, sep="\t", encoding=enc)
            except Exception:
                continue
    raise ValueError("Could not parse order CSV")


def normalize(df: pd.DataFrame, platform: str,
              mapping: dict[str, str | None] | None = None) -> pd.DataFrame:
    """Project the raw DataFrame onto canonical fields."""
    mapping = mapping or map_columns(list(df.columns), platform)
    out = pd.DataFrame(index=df.index)
    for canonical, src in mapping.items():
        out[canonical] = df[src] if src and src in df.columns else None

    # Parse date — best-effort
    if "order_date" in out.columns:
        out["order_date"] = pd.to_datetime(out["order_date"], errors="coerce")

    out["platform"] = platform
    out["currency"] = "THB" if platform in ("shopee", "lazada", "tiktok") else "USD"

    # Keep invalid rows and their original indexes. save_orders_report() owns
    # validation so every rejected source row receives a structured error.
    return out


@dataclass(frozen=True)
class OrderImportError:
    row_index: Any
    order_id: str
    sku: str
    code: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrderImportResult:
    inserted: int
    skipped: int
    errors: tuple[OrderImportError, ...]

    @property
    def import_errors(self) -> tuple[OrderImportError, ...]:
        return tuple(error for error in self.errors if error.code != "customer_sync_error")

    @property
    def warnings(self) -> tuple[OrderImportError, ...]:
        return tuple(error for error in self.errors if error.code == "customer_sync_error")


class OrderImportRowsError(ValueError):
    def __init__(self, errors: tuple[OrderImportError, ...]):
        self.errors = errors
        super().__init__(f"{len(errors)} order row(s) could not be imported")


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _text(value: Any, default: str = "") -> str:
    if _is_blank(value):
        return default
    normalized = str(value).strip()
    return normalized or default


def _positive_whole_number(value: Any, default: int) -> int:
    if _is_blank(value):
        return default
    try:
        number = float(re.sub(r"[฿$,\s]", "", str(value)))
    except (TypeError, ValueError, OverflowError):
        raise ValueError("qty must be a positive whole number") from None
    if not math.isfinite(number) or number <= 0 or not number.is_integer():
        raise ValueError("qty must be a positive whole number")
    return int(number)


def _finite_non_negative(value: Any, default: float, field: str) -> float:
    if _is_blank(value):
        return default
    try:
        number = float(re.sub(r"[฿$,\s]", "", str(value)))
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{field} must be a finite non-negative number") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return number


def save_orders_report(df: pd.DataFrame) -> OrderImportResult:
    """Insert orders and return deterministic per-row outcomes."""
    if df.empty:
        return OrderImportResult(inserted=0, skipped=0, errors=())

    db.init()

    # Map sku → product_id where it exists
    with db.conn() as c:
        sku_to_id = {
            r["sku"]: r["id"]
            for r in c.execute("SELECT id, sku FROM products").fetchall()
        }

    n_inserted = 0
    n_skipped = 0
    errors: list[OrderImportError] = []
    inserted_rows: list[tuple[Any, dict[str, Any]]] = []
    customer_sync_rows: list[tuple[Any, dict[str, Any]]] = []
    with db.conn() as c:
        for row_index, r in df.iterrows():
            order_id = _text(r.get("order_id"))
            sku = _text(r.get("sku"))
            platform = _text(r.get("platform"))
            missing = next(
                (name for name, value in (("order_id", order_id), ("sku", sku), ("platform", platform)) if not value),
                None,
            )
            if missing:
                errors.append(OrderImportError(
                    row_index=row_index,
                    order_id=order_id,
                    sku=sku,
                    code="missing_required",
                    message=f"{missing} is required",
                ))
                continue

            try:
                qty = _positive_whole_number(r.get("qty"), 1)
                unit = _finite_non_negative(r.get("unit_price"), 0, "unit_price")
                total = _finite_non_negative(
                    r.get("total_price"), unit * qty, "total_price"
                )
            except ValueError as exc:
                errors.append(OrderImportError(
                    row_index=row_index,
                    order_id=order_id,
                    sku=sku,
                    code="invalid_numeric",
                    message=str(exc),
                ))
                continue

            product_id = sku_to_id.get(sku)

            date_val = r.get("order_date")
            parsed_order_date = (
                order_business_date(date_val) if pd.notna(date_val) else None
            )
            order_date = parsed_order_date.isoformat() if parsed_order_date else ""

            canonical = {
                "order_id": order_id,
                "sku": sku,
                "platform": platform,
                "qty": qty,
                "unit_price": unit,
                "total_price": total,
                "currency": _text(r.get("currency"), "THB"),
                "order_date": order_date,
                "status": _text(r.get("status"), "paid"),
                "buyer_name": _text(r.get("buyer_name")),
                "buyer_phone": _text(r.get("buyer_phone")),
                "buyer_address": _text(r.get("buyer_address")),
                "product_name": _text(r.get("product_name"), sku),
            }

            c.execute("SAVEPOINT order_import_row")
            try:
                cursor = c.execute(
                    """
                    INSERT OR IGNORE INTO orders
                    (order_id, sku, product_id, platform, qty, unit_price, total_price,
                     currency, order_date, status, buyer_name, buyer_phone, buyer_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        canonical["order_id"], canonical["sku"], product_id,
                        canonical["platform"], canonical["qty"],
                        canonical["unit_price"], canonical["total_price"],
                        canonical["currency"], canonical["order_date"],
                        canonical["status"], canonical["buyer_name"],
                        canonical["buyer_phone"], canonical["buyer_address"],
                    ),
                )
                if cursor.rowcount:
                    # Decrement stock on the matched product (only on NEW
                    # rows, so re-importing the same CSV doesn't double-deduct).
                    if product_id:
                        _decrement_stock(c, product_id, qty)
                c.execute("RELEASE SAVEPOINT order_import_row")
            except sqlite3.Error as exc:
                c.execute("ROLLBACK TO SAVEPOINT order_import_row")
                c.execute("RELEASE SAVEPOINT order_import_row")
                errors.append(OrderImportError(
                    row_index=row_index,
                    order_id=order_id,
                    sku=sku,
                    code="database_error",
                    message=str(exc),
                ))
                continue

            if cursor.rowcount:
                n_inserted += 1
                inserted_rows.append((row_index, canonical))
                customer_row = canonical
            else:
                n_skipped += 1
                persisted = c.execute(
                    """
                    SELECT o.order_id, o.sku, o.platform, o.qty, o.unit_price,
                           o.total_price, o.currency, o.order_date, o.status,
                           o.buyer_name, o.buyer_phone, o.buyer_address,
                           COALESCE(p.name, o.sku) AS product_name
                    FROM orders o
                    LEFT JOIN products p ON p.id = o.product_id
                    WHERE o.platform = ? AND o.order_id = ? AND o.sku = ?
                    """,
                    (platform, order_id, sku),
                ).fetchone()
                customer_row = dict(persisted) if persisted else canonical
            customer_sync_rows.append((row_index, customer_row))

    # v58: Auto-create/update customer records from order data
    if customer_sync_rows:
        import customers as cust
        for row_index, row in customer_sync_rows:
            if not row["buyer_name"]:
                continue
            try:
                cust.init()
                cid = cust.find_or_create(
                    name=row["buyer_name"],
                    phone=row["buyer_phone"],
                    platform=row["platform"],
                )
                cust.record_order(
                    customer_id=cid,
                    order_id=row["order_id"],
                    platform=row["platform"],
                    amount=row["total_price"],
                    order_date=row["order_date"],
                    product=row["product_name"],
                )
            except Exception as exc:
                errors.append(OrderImportError(
                    row_index=row_index,
                    order_id=row["order_id"],
                    sku=row["sku"],
                    code="customer_sync_error",
                    message=str(exc),
                ))

    # v50: Emit a single event for the batch — not one per order (would spam)
    if n_inserted:
        try:
            import events
            events.log(
                category="order",
                severity="success",
                title=f"📦 {n_inserted} ออเดอร์ใหม่",
                body="Import เรียบร้อย · stock ลดอัตโนมัติแล้ว",
                target_page="pages/F_📈_Dashboard.py",
                meta={"n_inserted": n_inserted},
            )
        except Exception:
            pass

        # v58: LINE Notify — alert seller about new orders
        try:
            import user_settings as _us
            _us.init()
            token = _us.get("line_notify_token", "")
            if token and _us.get("line_alert_orders", True):
                import line_notify
                total_rev = sum(row["total_price"] for _, row in inserted_rows)
                platforms = ", ".join(sorted({row["platform"] for _, row in inserted_rows}))
                line_notify.send(token,
                    "\n🛒 ออเดอร์ใหม่ " + str(n_inserted) + " รายการ!"
                    "\n🏪 " + platforms +
                    "\n💰 รวม ฿{:,.0f}".format(float(total_rev or 0))
                )
        except Exception:
            pass

    return OrderImportResult(
        inserted=n_inserted,
        skipped=n_skipped,
        errors=tuple(errors),
    )


def save_orders(df: pd.DataFrame) -> int:
    """Backward-compatible import that never hides rejected rows."""
    result = save_orders_report(df)
    if result.import_errors:
        raise OrderImportRowsError(result.import_errors)
    return result.inserted


def _decrement_stock(c, product_id: int, qty: int) -> None:
    """Best-effort stock decrement. products.stock is a free-text label like
    '12 ชิ้น' or 'In stock' — we strip out the first integer, subtract qty,
    and write it back. Non-numeric stock is left alone."""
    import re
    row = c.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row or not row["stock"]:
        return
    s = str(row["stock"])
    m = re.search(r"\d+", s)
    if not m:
        return
    new_n = max(0, int(m.group(0)) - int(qty or 1))
    new_stock = re.sub(r"\d+", str(new_n), s, count=1)
    c.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
