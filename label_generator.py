"""Label Generator — packing slip and shipping address label text."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import math
import re
import sqlite3

import db
from i18n import t
from i18n_inline import carrier_name
from order_dates import order_business_date

LABEL_STYLES = ("full", "compact", "cod")
_PLATFORM = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_MAX_ORDER_ID = 160
_BULK_HEADER = ("order_id", "buyer_name", "phone", "address", "total", "cod")


def init() -> None:
    """Load shop profile from settings for label generation."""
    pass


def _shop_info() -> dict:
    with db.conn() as c:
        try:
            row = c.execute(
                "SELECT * FROM settings WHERE key='shop_profile'"
            ).fetchone()
            if row:
                import json
                return json.loads(row["value"] or "{}")
        except Exception:
            pass
    return {
        "name": t("lbl.shop_default"), "phone": "", "address": "",
        "line": "", "facebook": "",
    }


def generate_label(order_id: str = "", buyer_name: str = "",
                   buyer_phone: str = "", buyer_address: str = "",
                   items: list[dict] = None, total_price: float = 0,
                   cod_amount: float = 0, tracking: str = "",
                   carrier: str = "", notes: str = "",
                   style: str = "full") -> str:
    if items is None:
        items = []

    shop = _shop_info()
    dash = "-" * 40
    eq = "=" * 40
    carrier_label = carrier_name(carrier)

    lines = []
    if style == "full":
        lines += [
            eq,
            t("lbl.body_title"),
            eq,
            t("lbl.body_order", id=order_id or "—"),
            t("lbl.body_recipient", name=buyer_name or "—"),
            t("lbl.body_phone", phone=buyer_phone or "—"),
            t("lbl.body_address", address=buyer_address or "—"),
            dash,
        ]
        unit = t("lbl.unit_pcs")
        for item in items:
            line = t("lbl.body_item",
                     sku=item.get("sku") or "",
                     qty=str(item.get("qty", 1)),
                     unit=unit)
            if item.get("price"):
                line += t("lbl.body_item_price",
                          amount="{:,.0f}".format(item.get("price", 0)))
            lines.append(line)
        lines += [
            dash,
            t("lbl.body_total", amount="{:,.0f}".format(total_price)),
        ]
        if cod_amount > 0:
            lines.append(t("lbl.body_cod", amount="{:,.0f}".format(cod_amount)))
        if tracking:
            lines.append(t("lbl.body_tracking",
                           number=tracking, carrier=carrier_label))
        if notes:
            lines.append(t("lbl.body_notes", notes=notes))
        lines += [
            dash,
            t("lbl.body_sender", name=shop.get("name", "")),
            t("lbl.body_phone", phone=shop.get("phone", "")),
            eq,
        ]
    elif style == "compact":
        lines += [
            buyer_name or "—",
            buyer_phone or "—",
            buyer_address or "—",
        ]
        if cod_amount > 0:
            lines.append(t("lbl.body_cod_compact",
                           amount="{:,.0f}".format(cod_amount)))
        if tracking:
            lines.append(tracking)
    elif style == "cod":
        lines += [
            "=" * 30,
            t("lbl.body_recipient", name=buyer_name or "—"),
            t("lbl.body_phone", phone=buyer_phone or "—"),
            t("lbl.body_address", address=buyer_address or "—"),
        ]
        if cod_amount > 0:
            lines.append(t("lbl.body_cod_collect",
                           amount="{:,.0f}".format(cod_amount)))
        lines += [(tracking or ""), "=" * 30]
    return "\n".join(lines)


def _failure(code: str, *, order_id: str = "") -> dict:
    if code == "not_found":
        message = t("lbl.order_not_found", id=order_id)
    else:
        message = t("lbl.error_prefix", msg=code.replace("_", " "))
    return {"ok": False, "code": code, "message": message}


def _nonblank(value) -> bool:
    return value is not None and bool(str(value).strip())


def _finite_nonnegative(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _normalized_quantity(value: float):
    return int(value) if value.is_integer() else value


def _validated_identity(platform: str, order_id: str) -> tuple[str, str] | None:
    if not isinstance(platform, str) or not isinstance(order_id, str):
        return None
    normalized_platform = platform.strip().lower()
    normalized_order_id = order_id.strip()
    if not _PLATFORM.fullmatch(normalized_platform):
        return None
    if not normalized_order_id or len(normalized_order_id) > _MAX_ORDER_ID:
        return None
    if any(ord(character) < 32 or ord(character) == 127
           for character in normalized_order_id):
        return None
    return normalized_platform, normalized_order_id


def _cod_evidence(connection, platform: str, order_id: str) -> tuple[str, float | None]:
    try:
        rows = connection.execute(
            """SELECT payment_type, amount FROM cod_orders
               WHERE platform = ? AND order_id = ? ORDER BY id""",
            (platform, order_id),
        ).fetchall()
    except sqlite3.Error:
        return "unknown", None
    if len(rows) != 1:
        return "unknown", None
    payment_type = (
        str(rows[0]["payment_type"]).strip().lower()
        if _nonblank(rows[0]["payment_type"]) else ""
    )
    amount = _finite_nonnegative(rows[0]["amount"])
    if payment_type == "prepaid" and amount is not None:
        return "prepaid", 0.0
    if payment_type == "cod" and amount is not None:
        return "cod", amount
    return "unknown", None


def from_order(platform: str, order_id: str, style: str = "full") -> dict:
    """Generate a label from one exact external marketplace order."""
    identity = _validated_identity(platform, order_id)
    if identity is None or style not in LABEL_STYLES:
        return _failure("invalid_input", order_id=str(order_id or ""))
    normalized_platform, normalized_order_id = identity

    with db.conn() as c:
        try:
            rows = [dict(row) for row in c.execute(
                """SELECT order_id, sku, platform, qty, unit_price,
                          total_price, order_date, buyer_name, buyer_phone,
                          buyer_address, tracking_number, carrier
                   FROM orders
                   WHERE platform = ? AND order_id = ?
                   ORDER BY id""",
                (normalized_platform, normalized_order_id),
            ).fetchall()]
        except sqlite3.Error:
            return _failure("database_error", order_id=normalized_order_id)

        if not rows:
            return _failure("not_found", order_id=normalized_order_id)

        required_text = (
            "buyer_name", "buyer_phone", "buyer_address",
            "tracking_number", "carrier",
        )
        if any(not _nonblank(row[field]) for row in rows for field in required_text):
            return _failure("incomplete_evidence", order_id=normalized_order_id)

        consistent_values = {
            field: {str(row[field]).strip() for row in rows}
            for field in required_text
        }
        if any(len(values) != 1 for values in consistent_values.values()):
            return _failure("conflicting_evidence", order_id=normalized_order_id)

        parsed_dates = [order_business_date(row["order_date"]) for row in rows]
        today = order_business_date(datetime.now(timezone.utc))
        if any(value is None or value > today for value in parsed_dates):
            return _failure("incomplete_evidence", order_id=normalized_order_id)
        if len(set(parsed_dates)) != 1:
            return _failure("conflicting_evidence", order_id=normalized_order_id)

        items = []
        seen_skus = set()
        total_price = 0.0
        for row in rows:
            sku = str(row["sku"]).strip() if _nonblank(row["sku"]) else ""
            qty = _finite_nonnegative(row["qty"])
            unit_price = _finite_nonnegative(row["unit_price"])
            row_total = _finite_nonnegative(row["total_price"])
            if not sku or qty is None or unit_price is None or row_total is None:
                return _failure("incomplete_evidence", order_id=normalized_order_id)
            if sku in seen_skus:
                return _failure("ambiguous_order", order_id=normalized_order_id)
            seen_skus.add(sku)
            total_price += row_total
            if not math.isfinite(total_price):
                return _failure("incomplete_evidence", order_id=normalized_order_id)
            items.append({
                "sku": sku,
                "qty": _normalized_quantity(qty),
                "price": unit_price,
            })

        cod_state, cod_amount = _cod_evidence(
            c, normalized_platform, normalized_order_id
        )
        order = {
            "platform": normalized_platform,
            "order_id": normalized_order_id,
            "order_date": parsed_dates[0].isoformat(),
            "buyer_name": next(iter(consistent_values["buyer_name"])),
            "buyer_phone": next(iter(consistent_values["buyer_phone"])),
            "buyer_address": next(iter(consistent_values["buyer_address"])),
            "tracking_number": next(iter(consistent_values["tracking_number"])),
            "carrier": next(iter(consistent_values["carrier"])),
            "items": items,
            "total_price": total_price,
            "cod_state": cod_state,
            "cod_amount": cod_amount,
        }
        label = generate_label(
            order_id=normalized_order_id,
            buyer_name=order["buyer_name"],
            buyer_phone=order["buyer_phone"],
            buyer_address=order["buyer_address"],
            items=items,
            total_price=total_price,
            cod_amount=cod_amount if cod_state == "cod" else 0,
            tracking=order["tracking_number"],
            carrier=order["carrier"],
            style=style,
        )
        return {"ok": True, "code": "ok", "message": "", "label": label,
                "order": order}


def generate_bulk_labels(csv_text: str, *, style: str = "full") -> dict:
    """Generate manual plain-text labels from six-column CSV rows."""
    labels = []
    errors = []
    if not isinstance(csv_text, str) or style not in LABEL_STYLES:
        return {"labels": labels, "errors": [{
            "row": 0, "code": "invalid_input", "message": "row 0: invalid input",
        }]}

    try:
        reader = csv.reader(io.StringIO(csv_text), strict=True)
        for row in reader:
            row_number = reader.line_num
            if not row or all(not str(value).strip() for value in row):
                continue
            if len(row) != 6:
                errors.append({
                    "row": row_number,
                    "code": "invalid_columns",
                    "message": f"row {row_number}: invalid columns",
                })
                continue
            if tuple(str(value).strip().lower() for value in row) == _BULK_HEADER:
                continue
            order_id, buyer_name, phone, address, raw_total, raw_cod = (
                str(value).strip() for value in row
            )
            if (not _validated_identity("manual", order_id)
                    or not all((buyer_name, phone, address))):
                errors.append({
                    "row": row_number,
                    "code": "incomplete_evidence",
                    "message": f"row {row_number}: incomplete evidence",
                })
                continue
            total = _finite_nonnegative(raw_total)
            cod_amount = _finite_nonnegative(raw_cod)
            if total is None or cod_amount is None:
                errors.append({
                    "row": row_number,
                    "code": "invalid_numeric",
                    "message": f"row {row_number}: invalid numeric value",
                })
                continue
            labels.append(generate_label(
                order_id=order_id,
                buyer_name=buyer_name,
                buyer_phone=phone,
                buyer_address=address,
                total_price=total,
                cod_amount=cod_amount,
                style=style,
            ))
    except csv.Error as exc:
        row_number = getattr(reader, "line_num", 0)
        errors.append({
            "row": row_number,
            "code": "invalid_csv",
            "message": f"row {row_number}: {exc}",
        })
    return {"labels": labels, "errors": errors}


def stats() -> dict:
    with db.conn() as c:
        try:
            today_orders = c.execute(
                "SELECT COUNT(*) FROM orders WHERE date(order_date)=date('now','localtime')"
            ).fetchone()[0]
        except Exception:
            today_orders = 0
    return {"today_orders": today_orders}
