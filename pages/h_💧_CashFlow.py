"""Cash Flow Forecast — don't run out of cash to buy stock.

Thai platforms hold money 7-14 days. Suppliers want payment upfront.
This gap kills resellers. This page shows when cash actually arrives."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import cashflow as cf
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Cash Flow",
                   page_icon="💧", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="💧", title=t("cf.title"), subtitle=t("cf.caption"))


# ---- 30-day forecast ---------------------------------------------------------

f = cf.forecast(30)

st.markdown("### " + t("cf.forecast_30"))

# Net flow hero
net_color = "#4d6c5c" if f["net_flow"] >= 0 else "#c54c4c"
health_icon = {"positive": "✅", "tight": "⚠️", "danger": "🔴"}.get(f["health"], "?")
net_str = "{:,.0f}".format(f["net_flow"])

st.markdown(
    "<div style='text-align:center;padding:24px;background:rgba(77,108,92,0.04);"
    "border-radius:14px;margin-bottom:16px'>"
    "<div style='font-size:2.5rem;font-weight:600;color:" + net_color + "'>"
    + health_icon + " ฿" + net_str + "</div>"
    "<div style='color:#7a7569;font-size:14px'>" + t("cf.net_flow_label") + "</div>"
    "</div>",
    unsafe_allow_html=True,
)


# ---- Incoming vs Outgoing breakdown ------------------------------------------

in_col, out_col = st.columns(2)

with in_col:
    st.markdown("### 📥 " + t("cf.incoming"))

    items_in = [
        (t("cf.pending_cod"), f["pending_cod"], "📮"),
        (t("cf.pending_orders"), f["pending_orders"], "🛒"),
    ]
    for label, amount, icon in items_in:
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span>" + icon + " " + label + "</span>"
            "<span style='color:#4d6c5c;font-weight:600;font-variant-numeric:tabular-nums'>"
            "+฿" + "{:,.0f}".format(amount) + "</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div style='display:flex;justify-content:space-between;"
        "padding:10px 14px;border-top:1px solid rgba(40,30,20,0.1);font-weight:600'>"
        "<span>" + t("cf.total_incoming") + "</span>"
        "<span style='color:#4d6c5c;font-variant-numeric:tabular-nums'>"
        "+฿" + "{:,.0f}".format(f["total_incoming"]) + "</span></div>",
        unsafe_allow_html=True,
    )

with out_col:
    st.markdown("### 📤 " + t("cf.outgoing"))

    items_out = [
        (t("cf.proj_expenses"), f["projected_expenses"], "💸"),
        (t("cf.pending_po"), f["pending_po"], "🏭"),
        (t("cf.return_reserve"), f["return_reserve"], "↩️"),
    ]
    for label, amount, icon in items_out:
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span>" + icon + " " + label + "</span>"
            "<span style='color:#c54c4c;font-weight:600;font-variant-numeric:tabular-nums'>"
            "-฿" + "{:,.0f}".format(amount) + "</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div style='display:flex;justify-content:space-between;"
        "padding:10px 14px;border-top:1px solid rgba(40,30,20,0.1);font-weight:600'>"
        "<span>" + t("cf.total_outgoing") + "</span>"
        "<span style='color:#c54c4c;font-variant-numeric:tabular-nums'>"
        "-฿" + "{:,.0f}".format(f["total_outgoing"]) + "</span></div>",
        unsafe_allow_html=True,
    )


# ---- Weekly projection -------------------------------------------------------

st.divider()
st.markdown("### " + t("cf.weekly_title"))

weeks = cf.weekly_projection(4)
wcols = st.columns(4)
for i, w in enumerate(weeks):
    with wcols[i]:
        w_color = "#4d6c5c" if w["net"] >= 0 else "#c54c4c"
        w_icon = {"positive": "✅", "tight": "⚠️", "danger": "🔴"}.get(w["health"], "?")
        st.markdown(
            "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-radius:10px;padding:14px;text-align:center'>"
            "<div style='font-weight:600;color:#7a7569;font-size:12px;margin-bottom:6px'>"
            + w["label"] + "</div>"
            "<div style='font-size:1.4rem;font-weight:600;color:" + w_color + "'>"
            + w_icon + " ฿" + "{:,.0f}".format(w["net"]) + "</div>"
            "<div style='font-size:11px;color:#9a9485;margin-top:4px'>"
            "📥 " + "{:,.0f}".format(w["incoming"]) +
            " · 📤 " + "{:,.0f}".format(w["outgoing"]) +
            "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Cash runway -------------------------------------------------------------

st.divider()
runway = cf.runway_days()
runway_color = "#4d6c5c" if runway > 30 else ("#c5963d" if runway > 14 else "#c54c4c")
runway_icon = "✅" if runway > 30 else ("⚠️" if runway > 14 else "🔴")

st.markdown(
    "<div style='text-align:center;padding:20px;background:rgba(77,108,92,0.03);"
    "border-radius:12px'>"
    "<div style='color:#7a7569;font-size:13px;margin-bottom:6px'>"
    + t("cf.runway_label") + "</div>"
    "<div style='font-size:2rem;font-weight:600;color:" + runway_color + "'>"
    + runway_icon + " " + str(runway) + " " + t("dashboard.days") + "</div>"
    "<div style='color:#9a9485;font-size:12px;margin-top:4px'>"
    + t("cf.runway_hint") + "</div></div>",
    unsafe_allow_html=True,
)
