"""Today — the seller's "what needs attention right now" inbox.

BigSeller / Page365 / Ginee give you a KPI dashboard (revenue, profit graphs).
Useful, but it tells you the past. This page tells you the FUTURE — the things
you need to fix BEFORE the next order, the next review, the next pay-cut.

Six buckets, each with a one-click action to resolve:
  🔴 Out of stock (will fail next sale)
  📸 Missing images (Shopee/Lazada will reject)
  ⭐ Recent reviews awaiting reply
  📦 Orders paid but not shipped (clock is ticking)
  🤖 AI generations that errored (worth retrying)
  💤 Slow movers (no orders in 30 days — markdown or pull)"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
import inventory as inv
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Today", page_icon="📥", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📥", title=t("today.title"), subtitle=t("today.caption"))


# ---- Pull every bucket -------------------------------------------------

def _q(sql, params=()):
    with db.conn() as c:
        rows = c.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# 1. Out of stock — products whose stock parses to 0
all_products = _q("SELECT id, sku, name, stock, sell_price FROM products")
oos = [p for p in all_products if inv.parse_stock(p.get("stock")) == 0]

# 2. Missing images
no_img = _q(
    "SELECT id, sku, name FROM products "
    "WHERE image_url IS NULL OR image_url = '' "
    "LIMIT 50"
)

# 3. Pending shipments — orders paid but not yet shipped
try:
    pending_orders = _q(
        "SELECT order_id, sku, platform, qty, unit_price, order_date "
        "FROM orders "
        "WHERE (tracking_number IS NULL OR tracking_number = '') "
        "  AND status = 'paid' "
        "ORDER BY order_date DESC LIMIT 50"
    )
except Exception:
    pending_orders = []

# 4. Slow movers — products with no order in last 30 days
try:
    recent_sku_rows = _q(
        "SELECT DISTINCT sku FROM orders WHERE order_date >= date('now', '-30 days')"
    )
    recent_skus = {r["sku"] for r in recent_sku_rows}
    has_orders_table_with_data = bool(recent_skus) or _q("SELECT 1 FROM orders LIMIT 1")
    slow = [p for p in all_products if p["sku"] not in recent_skus] \
        if has_orders_table_with_data else []
    slow = slow[:30]  # cap for the UI
except Exception:
    slow = []

# 5. Reviews awaiting reply (only counts if 'reviews' table exists)
try:
    pending_reviews = _q(
        "SELECT id, sku, rating, text FROM reviews WHERE replied_at IS NULL LIMIT 20"
    )
except Exception:
    pending_reviews = []

# 6. AI errors — content rows with an `error` field set (if your schema tracks this)
try:
    failed_gen = _q(
        "SELECT product_id, task, payload FROM content "
        "WHERE payload LIKE '%\"error\"%' LIMIT 20"
    )
except Exception:
    failed_gen = []


# ---- Hero counters -----------------------------------------------------

counts = {
    "oos":     len(oos),
    "no_img":  len(no_img),
    "ship":    len(pending_orders),
    "reviews": len(pending_reviews),
    "errors":  len(failed_gen),
    "slow":    len(slow),
}
total_attention = sum(counts.values())

if total_attention == 0:
    # Inbox zero — celebratory empty state
    st.markdown(
        "<div style='max-width:520px;margin:8vh auto;padding:40px 32px;"
        "background:white;border-radius:14px;text-align:center;"
        "border:1px solid rgba(40,30,20,0.06);"
        "box-shadow:0 6px 18px rgba(31,31,31,0.04)'>"
        "<div style='font-size:52px'>🎉</div>"
        "<div style='font-family:Cormorant Garamond,serif;font-size:1.8rem;"
        "font-weight:500;margin-top:8px'>"
        f"{t('today.inbox_zero_title')}</div>"
        f"<div style='color:#6b6b6b;font-size:14px;margin-top:10px;"
        f"line-height:1.6'>{t('today.inbox_zero_body')}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# v49: 6-up metric chips, each with a tone + clickable hint to fix
m1, m2, m3, m4, m5, m6 = st.columns(6)
def _tone(n):
    """0 → ok, 1-5 → warn, 6+ → danger."""
    return "ok" if n == 0 else ("warn" if n <= 5 else "danger")

with m1:
    metric_with_hint("🔴 " + t("today.m_oos"), counts["oos"],
        hint=t("today.b_oos_cta") if counts["oos"] else "",
        hint_target="pages/2_📦_Catalog.py" if counts["oos"] else None,
        hint_tone=_tone(counts["oos"]))
with m2:
    metric_with_hint("📸 " + t("today.m_no_img"), counts["no_img"],
        hint=t("today.b_no_img_cta") if counts["no_img"] else "",
        hint_target="pages/8_📸_Vision.py" if counts["no_img"] else None,
        hint_tone=_tone(counts["no_img"]))
with m3:
    metric_with_hint("📦 " + t("today.m_ship"), counts["ship"],
        hint=t("today.b_ship_cta") if counts["ship"] else "",
        hint_target="pages/K_📦_Fulfillment.py" if counts["ship"] else None,
        hint_tone=_tone(counts["ship"]))
with m4:
    metric_with_hint("⭐ " + t("today.m_reviews"), counts["reviews"],
        hint=t("today.b_reviews_cta") if counts["reviews"] else "",
        hint_target="pages/3_🤖_Generate.py" if counts["reviews"] else None,
        hint_tone=_tone(counts["reviews"]))
with m5:
    metric_with_hint("🤖 " + t("today.m_errors"), counts["errors"],
        hint=t("today.b_errors_cta") if counts["errors"] else "",
        hint_target="pages/3_🤖_Generate.py" if counts["errors"] else None,
        hint_tone="warn" if counts["errors"] else "ok")
with m6:
    metric_with_hint("💤 " + t("today.m_slow"), counts["slow"],
        hint=t("today.b_slow_cta") if counts["slow"] else "",
        hint_target="pages/D_🔀_Sourcing.py" if counts["slow"] else None,
        hint_tone="warn" if counts["slow"] else "ok")

st.divider()


# ---- Bucket renderer ---------------------------------------------------

def _bucket(*, icon: str, title_key: str, hint_key: str,
            rows: list, columns: list, page_target: str | None = None,
            cta_key: str | None = None):
    if not rows:
        return
    st.markdown(f"### {icon} {t(title_key)}  "
                f"<span style='color:#6b6b6b;font-weight:400'>· {len(rows)}</span>",
                unsafe_allow_html=True)
    st.caption(t(hint_key))

    # Render compact dataframe
    df = pd.DataFrame(rows)
    show_cols = [c for c in columns if c in df.columns]
    if show_cols:
        st.dataframe(df[show_cols].head(15), width='stretch', hide_index=True)
        if len(rows) > 15:
            st.caption(f"+ {len(rows) - 15} more")

    if page_target and cta_key:
        st.page_link(page_target, label=f"▶ {t(cta_key)}")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)


# ---- Render every non-empty bucket -------------------------------------

_bucket(
    icon="🔴", title_key="today.b_oos_title", hint_key="today.b_oos_hint",
    rows=oos,
    columns=["sku", "name", "stock", "sell_price"],
    page_target="pages/2_📦_Catalog.py", cta_key="today.b_oos_cta",
)
_bucket(
    icon="📸", title_key="today.b_no_img_title", hint_key="today.b_no_img_hint",
    rows=no_img,
    columns=["sku", "name"],
    page_target="pages/8_📸_Vision.py", cta_key="today.b_no_img_cta",
)
_bucket(
    icon="📦", title_key="today.b_ship_title", hint_key="today.b_ship_hint",
    rows=pending_orders,
    columns=["order_id", "platform", "sku", "qty", "order_date"],
    page_target="pages/K_📦_Fulfillment.py", cta_key="today.b_ship_cta",
)
_bucket(
    icon="⭐", title_key="today.b_reviews_title", hint_key="today.b_reviews_hint",
    rows=pending_reviews,
    columns=["sku", "rating", "text"],
    page_target="pages/3_🤖_Generate.py", cta_key="today.b_reviews_cta",
)
_bucket(
    icon="🤖", title_key="today.b_errors_title", hint_key="today.b_errors_hint",
    rows=failed_gen,
    columns=["product_id", "task"],
    page_target="pages/3_🤖_Generate.py", cta_key="today.b_errors_cta",
)
_bucket(
    icon="💤", title_key="today.b_slow_title", hint_key="today.b_slow_hint",
    rows=slow,
    columns=["sku", "name", "sell_price"],
    page_target="pages/D_🔀_Sourcing.py", cta_key="today.b_slow_cta",
)
