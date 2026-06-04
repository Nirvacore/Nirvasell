"""Alerts — surface what changed: price moves, low stock, new arrivals.

Reads the reseller/ scraper DB (read-only) and shows actionable diffs.
Resellers can react fast: re-list with new price, mark out-of-stock,
or import new SKUs into nirva."""
from __future__ import annotations
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import bridge_reseller as br
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from _components import page_header

db.init()
st.set_page_config(page_title="nirva.sell · Alerts", page_icon="🔔", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="🔔", title=t("alerts.title"), subtitle=t("alerts.caption"))


# ---- v50: Unified Events Feed (Amazon Seller pattern) ------------------
# Everything that happens — orders, AI errors, policy diffs, donations —
# flows into one chronological feed with category filters + mark-as-read.
import events as _events

_unread_total = _events.unread_count()
_cat_counts = _events.category_counts()

# Heading with badge
st.markdown(
    f"### 📥 {t('alerts.feed_title')}  "
    f"<span style='color:#9a9485;font-weight:400;font-size:13px'>"
    f"· {_unread_total} {t('alerts.unread')}</span>",
    unsafe_allow_html=True,
)
st.caption(t("alerts.feed_caption"))

# Category filter chips
_cat_options = ["all"] + list(_events.CATEGORIES)
_chosen_cat = st.session_state.get("_events_cat", "all")
_cat_cols = st.columns(len(_cat_options))
for _i, _cat in enumerate(_cat_options):
    _icon = _events.CATEGORY_ICONS.get(_cat, "🌐") if _cat != "all" else "🌐"
    _n = _unread_total if _cat == "all" else _cat_counts.get(_cat, 0)
    _suffix = f" · {_n}" if _n else ""
    with _cat_cols[_i]:
        if st.button(
            f"{_icon} {t(f'alerts.cat_{_cat}')}{_suffix}",
            key=f"_evt_cat_{_cat}",
            type="primary" if _chosen_cat == _cat else "tertiary",
            width="stretch",
        ):
            st.session_state["_events_cat"] = _cat
            st.rerun()

# Render feed
_feed = _events.recent(limit=30,
                       category=None if _chosen_cat == "all" else _chosen_cat)

# "Mark all read" action button
if _feed and any(not e["read_at"] for e in _feed):
    _ca, _cb = st.columns([5, 1])
    with _cb:
        if st.button(t("alerts.mark_all_read"), type="tertiary",
                     width="stretch", key="_evt_mark_all"):
            n = _events.mark_all_read(
                None if _chosen_cat == "all" else _chosen_cat
            )
            st.toast(t("alerts.marked_n_read", n=n), icon="✓")
            st.rerun()

if not _feed:
    st.info(t("alerts.feed_empty"))
else:
    for _evt in _feed:
        _is_unread = not _evt.get("read_at")
        _sev_icon = _events.SEVERITY_ICONS.get(_evt["severity"], "•")
        _cat_icon = _events.CATEGORY_ICONS.get(_evt["category"], "🌐")
        _border = "1px solid rgba(77,108,92,0.25)" if _is_unread else "1px solid rgba(40,30,20,0.05)"
        _bg = "rgba(77,108,92,0.03)" if _is_unread else "white"
        _bold = "600" if _is_unread else "400"
        _ts = _evt.get("created_at", "")[:16]
        _body_html = ""
        if _evt.get("body"):
            _body_html = (
                f"<div style='color:#6b6b6b;font-size:13px;margin-top:3px;"
                f"line-height:1.5'>{_evt['body']}</div>"
            )
        st.markdown(
            f"<div style='background:{_bg};border:{_border};border-radius:10px;"
            f"padding:12px 14px;margin-bottom:8px'>"
            f"<div style='display:flex;align-items:center;gap:8px;font-size:11px;"
            f"color:#9a9485'>"
            f"{_cat_icon} <span>{_evt['category'].upper()}</span> · {_ts}</div>"
            f"<div style='font-weight:{_bold};color:#1f1f1f;font-size:14px;"
            f"margin-top:4px'>{_sev_icon} {_evt['title']}</div>"
            f"{_body_html}"
            f"</div>",
            unsafe_allow_html=True,
        )
        # Action row — page link + mark read
        _ra, _rb, _rc = st.columns([1, 1, 4])
        with _ra:
            if _evt.get("target_page"):
                try:
                    st.page_link(_evt["target_page"], label=f"▶ {t('alerts.open')}")
                except Exception:
                    pass
        with _rb:
            if _is_unread and st.button(
                t("alerts.mark_read"),
                key=f"_evt_read_{_evt['id']}",
                type="tertiary",
            ):
                _events.mark_read(_evt["id"])
                st.rerun()

st.divider()


# ---- Source path ---------------------------------------------------------

default_path = br.default_reseller_db()
path_str = st.text_input(t("import.db_path"), str(default_path))
reseller_db = Path(path_str)

# ---- Policy alerts (written by scripts/policy_check.py) -----------------

POLICY_ALERTS = Path(__file__).parent.parent / "data" / "policy_alerts.jsonl"
if POLICY_ALERTS.exists():
    import json as _json
    recent = []
    for line in POLICY_ALERTS.read_text().splitlines()[-20:]:
        try:
            recent.append(_json.loads(line))
        except Exception:
            continue
    if recent:
        st.markdown(f"### {t('alerts.policy_section')}")
        for r in recent[::-1][:10]:
            kind = r.get("kind", "")
            platform = r.get("platform", "?")
            at = r.get("at", "")[:16]
            if kind == "content_changed":
                badge = "📋"
                diffs = r.get("diffs", [])
                detail = f" — {len(diffs)} fee changes" if diffs else " — content updated"
            elif kind == "fetch_failed":
                badge = "⚠"
                detail = f" — fetch failed (HTTP {r.get('status','?')})"
            else:
                badge = "•"
                detail = ""
            st.markdown(f"{badge} **{platform}** · `{at}`{detail}")
            if r.get("effective_date"):
                st.caption(f"  Effective: {r['effective_date']}")
            if r.get("notes"):
                st.caption(f"  {r['notes'][:200]}")
        st.divider()


info = br.inspect(reseller_db)
if not info["exists"]:
    st.warning(t("import.not_found", path=info["path"]))
    st.markdown(t("import.howto"))
    st.stop()


# ---- Filters --------------------------------------------------------------

c1, c2, c3 = st.columns(3)
with c1:
    window_hours = st.selectbox(t("alerts.window"), [24, 72, 168, 720], index=1,
                                 format_func=lambda h: t("alerts.window_label", h=h))
with c2:
    low_stock_threshold = st.number_input(
        t("alerts.low_stock_threshold"), min_value=0, value=5, step=1
    )
with c3:
    show_kind = st.multiselect(
        t("alerts.show_kind"),
        ["price_change", "low_stock", "new"],
        default=["price_change", "low_stock"],
        format_func=lambda k: {
            "price_change": "💸 " + t("alerts.kind_price"),
            "low_stock": "📦 " + t("alerts.kind_low_stock"),
            "new": "✨ " + t("alerts.kind_new"),
        }.get(k, k),
    )


# ---- Query reseller DB ---------------------------------------------------

conn = sqlite3.connect(str(reseller_db))
conn.row_factory = sqlite3.Row

cutoff = (datetime.now() - timedelta(hours=window_hours)).strftime("%Y-%m-%d %H:%M:%S")

alerts: list[dict] = []

if "price_change" in show_kind:
    # Find products whose price has changed at least once in window.
    # We look at price_history grouped by product_id; if >1 distinct prices
    # exist after the cutoff, OR a price exists newer than the prior one.
    rows = conn.execute(
        """
        WITH recent AS (
          SELECT product_id, cost_price, seen_at,
                 ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY seen_at DESC) AS rn
          FROM price_history
        )
        SELECT p.sku, p.name, p.brand, p.source,
               last.cost_price AS new_price,
               prev.cost_price AS old_price,
               last.seen_at
        FROM products p
        JOIN recent last ON last.product_id = p.id AND last.rn = 1
        LEFT JOIN recent prev ON prev.product_id = p.id AND prev.rn = 2
        WHERE last.seen_at >= ?
          AND prev.cost_price IS NOT NULL
          AND prev.cost_price != last.cost_price
        ORDER BY last.seen_at DESC
        """,
        (cutoff,),
    ).fetchall()
    for r in rows:
        delta = float(r["new_price"]) - float(r["old_price"])
        pct = (delta / float(r["old_price"]) * 100) if r["old_price"] else 0
        alerts.append({
            "kind": "price_change",
            "sku": f"{r['source'].upper()}-{r['sku']}",
            "name": r["name"],
            "brand": r["brand"],
            "old_price": float(r["old_price"]),
            "new_price": float(r["new_price"]),
            "delta": delta,
            "pct": pct,
            "seen_at": r["seen_at"],
        })

if "low_stock" in show_kind:
    rows = conn.execute(
        """
        SELECT sku, name, brand, source, stock, cost_price, scraped_at
        FROM products
        WHERE stock IS NOT NULL
          AND CAST(stock AS INTEGER) <= ?
          AND CAST(stock AS INTEGER) > 0
        ORDER BY CAST(stock AS INTEGER) ASC
        LIMIT 100
        """,
        (low_stock_threshold,),
    ).fetchall()
    for r in rows:
        try:
            stock = int(r["stock"])
        except (TypeError, ValueError):
            continue
        alerts.append({
            "kind": "low_stock",
            "sku": f"{r['source'].upper()}-{r['sku']}",
            "name": r["name"],
            "brand": r["brand"],
            "stock": stock,
            "cost_price": float(r["cost_price"] or 0),
            "seen_at": r["scraped_at"],
        })

if "new" in show_kind:
    rows = conn.execute(
        """
        SELECT sku, name, brand, source, cost_price, scraped_at
        FROM products
        WHERE scraped_at >= ?
        ORDER BY scraped_at DESC
        LIMIT 100
        """,
        (cutoff,),
    ).fetchall()
    for r in rows:
        alerts.append({
            "kind": "new",
            "sku": f"{r['source'].upper()}-{r['sku']}",
            "name": r["name"],
            "brand": r["brand"],
            "cost_price": float(r["cost_price"] or 0),
            "seen_at": r["scraped_at"],
        })

conn.close()


# ---- Summary metrics ------------------------------------------------------

n_price = sum(1 for a in alerts if a["kind"] == "price_change")
n_stock = sum(1 for a in alerts if a["kind"] == "low_stock")
n_new = sum(1 for a in alerts if a["kind"] == "new")

m1, m2, m3 = st.columns(3)
m1.metric("💸 " + t("alerts.kind_price"), n_price)
m2.metric("📦 " + t("alerts.kind_low_stock"), n_stock)
m3.metric("✨ " + t("alerts.kind_new"), n_new)

if not alerts:
    st.info(t("alerts.no_alerts"))
    st.stop()


# ---- Alert feed ----------------------------------------------------------

st.divider()

# Price changes (most actionable — show first)
price_alerts = [a for a in alerts if a["kind"] == "price_change"]
if price_alerts:
    st.markdown(f"### 💸 {t('alerts.kind_price')}")
    rows = []
    for a in price_alerts:
        arrow = "📈" if a["delta"] > 0 else "📉"
        rows.append({
            "SKU": a["sku"],
            t("upload.field.name").rstrip(" *"): (a["name"] or "")[:60],
            t("alerts.old_price"): a["old_price"],
            t("alerts.new_price"): a["new_price"],
            "Δ %": f"{arrow} {a['pct']:+.1f}%",
            t("alerts.seen"): a["seen_at"][:16],
        })
    st.dataframe(
        pd.DataFrame(rows),
        width='stretch',
        hide_index=True,
        column_config={
            t("alerts.old_price"): st.column_config.NumberColumn(format="฿%.0f"),
            t("alerts.new_price"): st.column_config.NumberColumn(format="฿%.0f"),
        },
    )
    st.caption(t("alerts.price_hint"))

# Low stock
low_alerts = [a for a in alerts if a["kind"] == "low_stock"]
if low_alerts:
    st.markdown(f"### 📦 {t('alerts.kind_low_stock')}")
    rows = []
    for a in low_alerts:
        rows.append({
            "SKU": a["sku"],
            t("upload.field.name").rstrip(" *"): (a["name"] or "")[:60],
            t("upload.field.stock"): a["stock"],
            t("common.cost"): a["cost_price"],
            t("alerts.seen"): a["seen_at"][:16],
        })
    st.dataframe(
        pd.DataFrame(rows),
        width='stretch',
        hide_index=True,
        column_config={
            t("common.cost"): st.column_config.NumberColumn(format="฿%.0f"),
        },
    )

# New
new_alerts = [a for a in alerts if a["kind"] == "new"]
if new_alerts:
    st.markdown(f"### ✨ {t('alerts.kind_new')}")
    rows = []
    for a in new_alerts:
        rows.append({
            "SKU": a["sku"],
            t("upload.field.name").rstrip(" *"): (a["name"] or "")[:60],
            t("common.cost"): a["cost_price"],
            t("alerts.seen"): a["seen_at"][:16],
        })
    st.dataframe(
        pd.DataFrame(rows),
        width='stretch',
        hide_index=True,
        column_config={
            t("common.cost"): st.column_config.NumberColumn(format="฿%.0f"),
        },
    )
    st.caption(t("alerts.new_hint"))
