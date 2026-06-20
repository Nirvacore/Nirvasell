"""Customer Lifetime Value — know what each customer is worth.

CLV = AOV × Frequency × Lifespan. Decides how much to spend
acquiring each type, who deserves VIP treatment."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import clv
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · CLV",
                   page_icon="💎", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="💎", title=t("clv.title"), subtitle=t("clv.caption"))

s = clv.summary()

if s["total_customers"] == 0:
    st.info(t("clv.empty"))
    st.stop()


# ---- KPIs -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("clv.kpi_customers"), str(s["total_customers"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("clv.kpi_avg_clv"), "{:,.0f}".format(s["avg_clv"]),
        hint=t("clv.avg_hint"), hint_tone="info",
    )
with k3:
    metric_with_hint(
        t("clv.kpi_projected"), "{:,.0f}".format(s["total_projected"]),
        hint=t("clv.projected_hint"), hint_tone="ok",
    )
with k4:
    at_risk = s["churn_risk"]["high"]
    metric_with_hint(
        t("clv.kpi_at_risk"), str(at_risk),
        hint=t("clv.at_risk_hint") if at_risk > 0 else "",
        hint_tone="danger" if at_risk > 0 else "ok",
    )


# ---- Tier breakdown ----------------------------------------------------------

st.divider()
st.markdown("### " + t("clv.tiers_title"))

tier_data = [
    ("💎", "Platinum", s["tiers"]["platinum"], "฿50K+/yr", "#8B7355"),
    ("🥇", "Gold", s["tiers"]["gold"], "฿20-50K/yr", "#c5963d"),
    ("🥈", "Silver", s["tiers"]["silver"], "฿5-20K/yr", "#9a9485"),
    ("🥉", "Bronze", s["tiers"]["bronze"], "<฿5K/yr", "#7a7569"),
]
tcols = st.columns(4)
for i, (icon, label, count, threshold, color) in enumerate(tier_data):
    with tcols[i]:
        st.markdown(
            "<div style='text-align:center;padding:16px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px;"
            "border-top:3px solid " + color + "'>"
            "<div style='font-size:1.5rem'>" + icon + "</div>"
            "<div style='font-weight:600'>" + label + "</div>"
            "<div style='font-size:1.5rem;font-weight:600;color:" + color + "'>"
            + str(count) + "</div>"
            "<div style='font-size:11px;color:#9a9485'>" + threshold + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Customer list by tier ---------------------------------------------------

st.divider()

tab_plat, tab_gold, tab_silver, tab_bronze = st.tabs([
    "💎 Platinum (" + str(s["tiers"]["platinum"]) + ")",
    "🥇 Gold (" + str(s["tiers"]["gold"]) + ")",
    "🥈 Silver (" + str(s["tiers"]["silver"]) + ")",
    "🥉 Bronze (" + str(s["tiers"]["bronze"]) + ")",
])


def _render_customers(tier):
    custs = clv.tier_customers(tier)
    if not custs:
        st.info(t("clv.no_customers"))
        return

    for c in custs:
        name = c.get("buyer_name") or "—"
        phone = c.get("buyer_phone") or ""
        clv_str = "{:,.0f}".format(c["projected_annual_clv"])
        spent_str = "{:,.0f}".format(c["total_spent"])
        freq_str = str(c.get("order_count") or 0)
        aov_str = "{:,.0f}".format(c["avg_order_value"])

        churn = c.get("churn_risk", "low")
        churn_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(churn, "?")
        days_str = str(c.get("days_since_last", 0)) + "d"

        tier_color = {"platinum": "#8B7355", "gold": "#c5963d",
                      "silver": "#9a9485", "bronze": "#7a7569"}.get(tier, "#7a7569")

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>"
            "<span style='font-weight:600'>" + name + "</span>"
            " <span style='color:#9a9485;font-size:11px'>" + phone + "</span>"
            "</div>"
            "<div style='display:flex;gap:14px;align-items:center;font-size:13px'>"
            "<span>📦 " + freq_str + "x</span>"
            "<span>" + t("clv.line_aov", amount=aov_str) + "</span>"
            "<span>" + t("clv.line_spent", amount=spent_str) + "</span>"
            "<span>" + churn_icon + " " + days_str + "</span>"
            "<span style='font-weight:600;color:" + tier_color + "'>"
            + t("clv.clv_per_year", amount=clv_str) + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


with tab_plat:
    _render_customers("platinum")
with tab_gold:
    _render_customers("gold")
with tab_silver:
    _render_customers("silver")
with tab_bronze:
    _render_customers("bronze")


# ---- At-risk high-value customers -------------------------------------------

at_risk = clv.at_risk_high_value()
if at_risk:
    st.divider()
    st.markdown("### 🚨 " + t("clv.at_risk_title"))
    st.caption(t("clv.at_risk_help"))

    for c in at_risk:
        name = c.get("buyer_name") or "—"
        clv_str = "{:,.0f}".format(c["projected_annual_clv"])
        days_str = str(c.get("days_since_last", 0))

        st.markdown(
            "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid #c54c4c'>"
            "🚨 <strong>" + name + "</strong>"
            " · " + t("clv.clv_per_year", amount=clv_str) +
            " · " + t("clv.last_order") + " " +
            t("common.days_ago", n=days_str) + "</div>",
            unsafe_allow_html=True,
        )
