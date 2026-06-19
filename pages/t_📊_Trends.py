"""SKU Trends — rising stars and declining products.

Week-over-week comparison. Spot opportunities early, catch problems before they hurt."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import sku_trends as skt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · SKU Trends",
                   page_icon="📊", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📊", title=t("trend.title"), subtitle=t("trend.caption"))

s = skt.summary()

if s["total_skus"] == 0:
    st.info(t("trend.empty"))
    st.stop()


# ---- KPIs -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        "📈 " + t("trend.kpi_rising"), str(s["rising"]),
        hint="", hint_tone="ok",
    )
with k2:
    metric_with_hint(
        "📉 " + t("trend.kpi_declining"), str(s["declining"]),
        hint="", hint_tone="danger" if s["declining"] > 0 else "ok",
    )
with k3:
    metric_with_hint(
        "➡️ " + t("trend.kpi_stable"), str(s["stable"]),
        hint="", hint_tone="info",
    )
with k4:
    gainer_str = s["top_gainer"] + " (+" + str(s["top_gainer_pct"]) + "%)"
    metric_with_hint(
        "🏆 " + t("trend.kpi_top_gainer"), gainer_str if s["top_gainer"] != "—" else "—",
        hint="", hint_tone="ok",
    )


# ---- Trend tabs --------------------------------------------------------------

st.divider()

trends = skt.weekly_trend()

tab_all, tab_rising, tab_declining = st.tabs([
    "📋 " + t("trend.tab_all") + " (" + str(len(trends)) + ")",
    "📈 " + t("trend.tab_rising") + " (" + str(s["rising"]) + ")",
    "📉 " + t("trend.tab_declining") + " (" + str(s["declining"]) + ")",
])


def _render_trends(items):
    for item in items:
        trend = item["trend"]
        t_icon = {"rising": "📈", "declining": "📉", "stable": "➡️"}.get(trend, "?")
        t_color = {"rising": "#4d6c5c", "declining": "#c54c4c", "stable": "#9a9485"}.get(trend, "#7a7569")

        qty_now = str(item["qty_this_week"])
        qty_prev = str(item["qty_last_week"])
        chg_str = ("+" if item["qty_change_pct"] > 0 else "") + str(item["qty_change_pct"]) + "%"
        rev_chg = ("+" if item["rev_change_pct"] > 0 else "") + str(item["rev_change_pct"]) + "%"
        rev_str = "{:,.0f}".format(item["rev_this_week"])

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid " + t_color + "'>"
            "<div>"
            "<span style='font-weight:600'>" + t_icon + " " + item["sku"] + "</span>"
            " <span style='color:#7a7569;font-size:12px'>" + (item["name"] or "")[:25] + "</span>"
            "</div>"
            "<div style='display:flex;gap:14px;align-items:center;font-size:13px'>"
            "<span>📦 " + qty_prev + " → " + qty_now + "</span>"
            "<span style='font-weight:600;color:" + t_color + "'>" + chg_str + "</span>"
            "<span>💵 ฿" + rev_str + " (" + rev_chg + ")</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


with tab_all:
    _render_trends(trends)

with tab_rising:
    rising = [t for t in trends if t["trend"] == "rising"]
    if rising:
        st.success(t("trend.rising_help"))
        _render_trends(rising)
    else:
        st.info(t("trend.no_rising"))

with tab_declining:
    declining = [t for t in trends if t["trend"] == "declining"]
    if declining:
        st.error(t("trend.declining_help"))
        _render_trends(declining)
    else:
        st.success(t("trend.no_declining"))


# ---- New products performance -----------------------------------------------

new = skt.new_products(14)
if new:
    st.divider()
    st.markdown("### 🆕 " + t("trend.new_title"))
    st.caption(t("trend.new_help"))

    for p in new[:10]:
        sold = p.get("total_sold") or 0
        rev = "{:,.0f}".format(p.get("total_revenue") or 0)
        st.markdown(
            "<div style='padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "🆕 <strong>" + p["sku"] + "</strong>"
            " — " + (p["name"] or "")[:25] +
            t("trend.sold_count", n=str(sold)) +
            " · 💵 ฿" + rev + "</div>",
            unsafe_allow_html=True,
        )
