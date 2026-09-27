"""Channel Performance — which platform actually makes money?

Side-by-side comparison: Shopee vs Lazada vs TikTok vs LINE.
Revenue, margin, return rate, customer count per channel."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import channel_perf as cp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t
from i18n_inline import platform_name

st.set_page_config(page_title="nirva.sell · Channels",
                   page_icon="🌐", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🌐", title=t("chan.title"), subtitle=t("chan.caption"))

period = st.selectbox(
    t("chan.period"),
    [7, 14, 30, 60, 90],
    index=2,
    format_func=lambda d: str(d) + " " + t("dashboard.days"),
    label_visibility="collapsed",
)

platforms = cp.platform_comparison(period)

if not platforms:
    st.info(t("chan.empty"))
    st.stop()

s = cp.summary(period)


# ---- KPIs -------------------------------------------------------------------

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("chan.kpi_channels"), str(s["total_platforms"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("chan.kpi_top"), s["top_platform"],
        hint=t("chan.top_hint"), hint_tone="ok",
    )
with k3:
    best_margin_pct = s.get("best_margin_pct")
    best_margin = (
        s.get("best_margin", "—") + " (" + str(best_margin_pct) + "%)"
        if best_margin_pct is not None else "—"
    )
    metric_with_hint(
        t("chan.kpi_best_margin"),
        best_margin,
        hint=t("chan.margin_hint"), hint_tone="ok",
    )

if not s.get("evidence_complete", False):
    st.warning(
        "⚠️ ข้อมูลยอดขาย/ต้นทุนไม่ครบ · Revenue and profit metrics unavailable"
    )


# ---- Platform cards ----------------------------------------------------------

st.divider()
st.markdown("### " + t("chan.comparison_title"))

plat_icons = {
    "shopee": "🛒", "lazada": "🟧", "tiktok": "🎵",
    "facebook": "📘", "line": "💚", "instagram": "📸",
    "website": "🌐",
}

total_rev = sum(p["revenue"] or 0 for p in platforms)

for p in platforms:
    icon = plat_icons.get(p["platform"], "📦")
    rev_str = "{:,.0f}".format(p["revenue"]) if p["revenue"] is not None else "—"
    profit_str = (
        "{:,.0f}".format(p["gross_profit"])
        if p["gross_profit"] is not None else "—"
    )
    margin_str = str(p["margin"]) + "%" if p["margin"] is not None else "—"
    aov_str = "{:,.0f}".format(p["aov"]) if p["aov"] is not None else "—"
    orders_str = str(p["orders"])
    cust_str = str(p["customers"])
    ret_str = str(p["return_rate"]) + "%"
    share_str = (
        str(p["revenue_pct"]) + "%" if p["revenue_pct"] is not None else "—"
    )

    margin_color = (
        "#4d6c5c" if p["margin"] is not None and p["margin"] >= 20
        else ("#c5963d" if p["margin"] is not None and p["margin"] >= 10
              else ("#c54c4c" if p["margin"] is not None else "#9a9485"))
    )
    bar_width = p["revenue_pct"] if p["revenue_pct"] is not None else 0

    st.markdown(
        "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
        "border-radius:12px;padding:16px;margin-bottom:10px'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline;"
        "margin-bottom:8px'>"
        "<span style='font-size:1.2rem;font-weight:600'>"
        + icon + " " + platform_name(p["platform"]) + "</span>"
        "<span style='font-size:1.3rem;font-weight:600;color:#4d6c5c'>"
        "฿" + rev_str + " <span style='font-size:12px;color:#9a9485'>"
        "(" + share_str + ")</span></span></div>"
        "<div style='background:rgba(40,30,20,0.06);border-radius:4px;height:6px;"
        "overflow:hidden;margin-bottom:10px'>"
        "<div style='width:" + str(int(bar_width)) + "%;height:100%;"
        "background:#4d6c5c;border-radius:4px'></div></div>"
        "<div style='display:flex;gap:18px;font-size:12px;color:#7a7569'>"
        "<span>📦 " + t("common.n_orders", n=orders_str) + "</span>"
        "<span>👥 " + t("common.n_customers", n=cust_str) + "</span>"
        "<span>💰 " + t("chan.line_aov", amount=aov_str) + "</span>"
        "<span style='color:" + margin_color + ";font-weight:600'>"
        + t("common.margin") + " " + margin_str + "</span>"
        "<span>💵 " + t("common.profit") + " ฿" + profit_str + "</span>"
        "<span>↩️ " + t("common.return_label") + " " + ret_str + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )


# ---- Growth trends -----------------------------------------------------------

growth = cp.growth_by_platform(3)
if growth:
    st.divider()
    st.markdown("### " + t("chan.growth_title"))

    for g in growth:
        icon = plat_icons.get(g["platform"], "📦")
        chg = g["growth_pct"]
        chg_color = (
            "#4d6c5c" if chg is not None and chg >= 0
            else ("#c54c4c" if chg is not None else "#9a9485")
        )
        chg_icon = (
            "📈" if chg is not None and chg >= 0
            else ("📉" if chg is not None else "⚠️")
        )
        chg_str = (
            ("+" if chg >= 0 else "") + str(chg) + "%"
            if chg is not None else "—"
        )

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span>" + icon + " <strong>" + platform_name(g["platform"]) +
            "</strong></span>"
            "<span style='font-weight:600;color:" + chg_color + "'>"
            + chg_icon + " " + chg_str + t("common.mom") + "</span></div>",
            unsafe_allow_html=True,
        )
