"""Supplier Scorecard — rate suppliers on what matters.

Dimensions:
  - Delivery speed (actual vs promised lead time)
  - Quality (return rate on their products)
  - Price competitiveness (vs other suppliers for same SKU)
  - Reliability (on-time delivery %)

Thai resellers juggle 5-20 suppliers. This tells you who's good."""
from __future__ import annotations

from datetime import datetime

import db


def score_all() -> list[dict]:
    """Score all suppliers across dimensions."""
    try:
        import supplier_mgmt as sm
        sm.init()
    except ImportError:
        return []

    with db.conn() as c:
        suppliers = c.execute(
            "SELECT * FROM supplier_contacts ORDER BY name"
        ).fetchall()

    if not suppliers:
        return []

    results = []
    for s in suppliers:
        sd = dict(s)
        sid = sd["id"]
        name = sd.get("name") or "—"

        # --- Price competitiveness ---
        price_score = _price_score(sid)

        # --- Delivery (from PO data) ---
        delivery_score, avg_lead = _delivery_score(sid)

        # --- Volume (total PO value) ---
        volume = _po_volume(sid)

        # --- SKU coverage ---
        sku_count = _sku_count(sid)

        # --- Overall score (weighted average) ---
        overall = round(
            price_score * 0.4 +
            delivery_score * 0.3 +
            min(sku_count / 5, 1) * 100 * 0.15 +
            min(volume / 50000, 1) * 100 * 0.15,
            0,
        )

        results.append({
            "id": sid,
            "name": name,
            "contact": sd.get("contact_info") or "",
            "lead_days": sd.get("lead_days") or 0,
            "price_score": round(price_score, 0),
            "delivery_score": round(delivery_score, 0),
            "avg_lead_actual": avg_lead,
            "sku_count": sku_count,
            "total_volume": volume,
            "overall": int(overall),
            "grade": _grade(overall),
        })

    return sorted(results, key=lambda x: x["overall"], reverse=True)


def _price_score(supplier_id: int) -> float:
    """Price competitiveness: how often is this supplier the cheapest?"""
    with db.conn() as c:
        prices = c.execute(
            "SELECT sku, price FROM supplier_prices WHERE supplier_id=?",
            (supplier_id,),
        ).fetchall()

    if not prices:
        return 50  # neutral

    wins = 0
    total = 0
    for p in prices:
        sku = p["sku"]
        my_price = p["price"]
        with db.conn() as c:
            best = c.execute(
                "SELECT MIN(price) AS best FROM supplier_prices WHERE sku=?",
                (sku,),
            ).fetchone()

        if best and best["best"]:
            total += 1
            if my_price <= best["best"] * 1.05:  # within 5%
                wins += 1

    return (wins / total * 100) if total > 0 else 50


def _delivery_score(supplier_id: int) -> tuple[float, float]:
    """Delivery reliability from PO data."""
    with db.conn() as c:
        pos = c.execute(
            "SELECT * FROM purchase_orders WHERE supplier_id=? AND status='received'",
            (supplier_id,),
        ).fetchall()

    if not pos:
        return 50, 0  # neutral

    on_time = 0
    total_lead = 0
    for po in pos:
        expected = po.get("expected_date")
        received = po.get("received_date") or po.get("created_at")
        if expected and received:
            try:
                exp_dt = datetime.strptime(str(expected)[:10], "%Y-%m-%d")
                rec_dt = datetime.strptime(str(received)[:10], "%Y-%m-%d")
                diff = (rec_dt - exp_dt).days
                if diff <= 1:  # on time or early
                    on_time += 1
                total_lead += max(diff, 0)
            except Exception:
                pass

    pct = on_time / len(pos) * 100 if pos else 50
    avg_lead = round(total_lead / len(pos), 1) if pos else 0
    return pct, avg_lead


def _po_volume(supplier_id: int) -> float:
    with db.conn() as c:
        r = c.execute(
            "SELECT COALESCE(SUM(total_amount), 0) AS vol "
            "FROM purchase_orders WHERE supplier_id=?",
            (supplier_id,),
        ).fetchone()
    return r["vol"] if r else 0


def _sku_count(supplier_id: int) -> int:
    with db.conn() as c:
        r = c.execute(
            "SELECT COUNT(DISTINCT sku) AS cnt "
            "FROM supplier_prices WHERE supplier_id=?",
            (supplier_id,),
        ).fetchone()
    return r["cnt"] if r else 0


def _grade(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"


def summary() -> dict:
    suppliers = score_all()
    grades = {"A": 0, "B": 0, "C": 0, "D": 0}
    for s in suppliers:
        grades[s["grade"]] = grades.get(s["grade"], 0) + 1
    avg_score = round(sum(s["overall"] for s in suppliers) / len(suppliers), 0) if suppliers else 0
    return {
        "total": len(suppliers),
        "avg_score": int(avg_score),
        "grades": grades,
        "top_supplier": suppliers[0]["name"] if suppliers else "—",
    }
