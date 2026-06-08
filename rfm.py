"""RFM Customer Segmentation — the gold standard of CRM.

Recency × Frequency × Monetary = 9 actionable segments.
Used by every serious e-commerce business to decide WHO to spend
marketing budget on.

Segments:
  Champions     (5,5,5) — best customers, reward them
  Loyal         (X,4+,4+) — high freq+monetary, keep engaged
  Potential     (4+,2-3,2-3) — recent, growing, nurture them
  New           (5,1,1) — just arrived, welcome sequence
  Promising     (3-4,1,1) — showed up, need second purchase
  Need Attention(2-3,3+,3+) — were good, slipping away
  About to Sleep(2,2,2) — almost gone
  At Risk       (1-2,3+,3+) — were VIP, now gone
  Hibernating   (1,1-2,1-2) — long gone, win-back or let go
"""
from __future__ import annotations

from datetime import datetime, timedelta

import db


SEGMENTS = {
    "champions":      {"label": "Champions",       "icon": "👑", "color": "#4d6c5c", "action": "reward"},
    "loyal":          {"label": "Loyal",            "icon": "💎", "color": "#3a7ca5", "action": "upsell"},
    "potential":      {"label": "Potential Loyalist","icon": "🌱", "color": "#6b8e5a", "action": "nurture"},
    "new":            {"label": "New Customer",     "icon": "👋", "color": "#7ab648", "action": "welcome"},
    "promising":      {"label": "Promising",        "icon": "⭐", "color": "#c5963d", "action": "engage"},
    "need_attention": {"label": "Need Attention",   "icon": "⚠️", "color": "#d4832f", "action": "re-engage"},
    "about_to_sleep": {"label": "About to Sleep",   "icon": "😴", "color": "#b85c38", "action": "activate"},
    "at_risk":        {"label": "At Risk",          "icon": "🔴", "color": "#c54c4c", "action": "win-back"},
    "hibernating":    {"label": "Hibernating",      "icon": "❄️", "color": "#7a7569", "action": "last-chance"},
}


def _score_quintile(values: list[float], value: float, reverse: bool = False) -> int:
    """Score 1-5 based on quintile position."""
    if not values:
        return 3
    sorted_v = sorted(values, reverse=reverse)
    n = len(sorted_v)
    for i, v in enumerate(sorted_v):
        if (not reverse and value <= v) or (reverse and value >= v):
            return min(5, int(i / n * 5) + 1)
    return 5


def calculate_rfm() -> list[dict]:
    """Calculate RFM scores for all customers."""
    now = datetime.now()

    with db.conn() as c:
        customers = c.execute(
            "SELECT id, name, phone, email, platforms, "
            "order_count, total_spent, last_order "
            "FROM customers WHERE order_count > 0"
        ).fetchall()

    if not customers:
        return []

    # Calculate raw R, F, M values
    raw_data = []
    for cust in customers:
        last_order = cust["last_order"]
        if last_order:
            try:
                last_dt = datetime.fromisoformat(last_order.replace("Z", ""))
                recency_days = (now - last_dt).days
            except Exception:
                recency_days = 999
        else:
            recency_days = 999

        raw_data.append({
            "id": cust["id"],
            "name": cust["name"] or "—",
            "phone": cust["phone"] or "",
            "email": cust["email"] or "",
            "platforms": cust["platforms"] or "",
            "recency_days": recency_days,
            "frequency": int(cust["order_count"] or 0),
            "monetary": float(cust["total_spent"] or 0),
            "last_order": last_order or "",
        })

    # Score each dimension 1-5
    all_r = [d["recency_days"] for d in raw_data]
    all_f = [d["frequency"] for d in raw_data]
    all_m = [d["monetary"] for d in raw_data]

    for d in raw_data:
        d["r_score"] = _score_quintile(all_r, d["recency_days"], reverse=True)  # lower recency = higher score
        d["f_score"] = _score_quintile(all_f, d["frequency"])
        d["m_score"] = _score_quintile(all_m, d["monetary"])
        d["rfm_score"] = d["r_score"] * 100 + d["f_score"] * 10 + d["m_score"]
        d["segment"] = _classify(d["r_score"], d["f_score"], d["m_score"])
        seg_info = SEGMENTS.get(d["segment"], SEGMENTS["promising"])
        d["segment_label"] = seg_info["label"]
        d["segment_icon"] = seg_info["icon"]
        d["segment_color"] = seg_info["color"]
        d["action"] = seg_info["action"]

    return sorted(raw_data, key=lambda x: x["rfm_score"], reverse=True)


def _classify(r: int, f: int, m: int) -> str:
    """Classify into segment based on R, F, M scores."""
    if r >= 4 and f >= 4 and m >= 4:
        return "champions"
    if f >= 4 and m >= 4:
        return "loyal"
    if r >= 4 and f >= 2 and m >= 2:
        return "potential"
    if r >= 4 and f <= 1:
        return "new"
    if r >= 3 and f <= 2:
        return "promising"
    if r >= 2 and r <= 3 and f >= 3 and m >= 3:
        return "need_attention"
    if r == 2 and f == 2:
        return "about_to_sleep"
    if r <= 2 and f >= 3:
        return "at_risk"
    return "hibernating"


def segment_summary() -> list[dict]:
    """Count customers per segment."""
    all_rfm = calculate_rfm()
    counts: dict[str, int] = {}
    revenue: dict[str, float] = {}
    for d in all_rfm:
        seg = d["segment"]
        counts[seg] = counts.get(seg, 0) + 1
        revenue[seg] = revenue.get(seg, 0) + d["monetary"]

    results = []
    for seg_key, seg_info in SEGMENTS.items():
        results.append({
            "segment": seg_key,
            "label": seg_info["label"],
            "icon": seg_info["icon"],
            "color": seg_info["color"],
            "action": seg_info["action"],
            "count": counts.get(seg_key, 0),
            "revenue": round(revenue.get(seg_key, 0), 0),
        })
    return results


def customers_in_segment(segment: str) -> list[dict]:
    """Get all customers in a specific segment."""
    all_rfm = calculate_rfm()
    return [d for d in all_rfm if d["segment"] == segment]
