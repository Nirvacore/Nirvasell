"""Stock Turnover — how fast does inventory move?

Turnover Rate = COGS / Avg Inventory
Days of Inventory = how long current stock lasts
Reorder Point = when to buy more"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import stock_turnover as st_mod
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Stock Turnover",
                   page_icon="🔄", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🔄", title=t("turn.title"), subtitle=t("turn.caption"))


# ---- KPIs -------------------------------------------------------------------

s = st_mod.summary()

if s["total_skus"] == 0:
    st.info(t("turn.empty"))
    st.stop()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("turn.kpi_avg_turnover"),
        str(s["avg_turnover"]) + "x",
        hint=t("turn.turnover_hint"),
        hint_tone="ok" if s["avg_turnover"] >= 4 else "warn",
    )
with k2:
    metric_with_hint(
        t("turn.kpi_avg_doi"),
        str(s["avg_doi"]) + " " + t("dashboard.days"),
        hint=t("turn.doi_hint"),
        hint_tone="ok" if s["avg_doi"] <= 30 else "warn",
    )
with k3:
    metric_with_hint(
        t("turn.kpi_stock_value"),
        "{:,.0f}".format(s["total_stock_value"]),
        hint="", hint_tone="info",
    )
with k4:
    metric_with_hint(
        t("turn.kpi_reorder"),
        str(s["need_reorder"]),
        hint=t("turn.reorder_hint") if s["need_reorder"] > 0 else "",
        hint_tone="danger" if s["need_reorder"] > 0 else "ok",
    )


# ---- Health distribution -----------------------------------------------------

st.divider()
st.markdown("### " + t("turn.health_title"))

health_data = [
    ("🚀", t("turn.h_fast"), s["health"]["fast"], "#4d6c5c", "< 14d"),
    ("✅", t("turn.h_good"), s["health"]["good"], "#4a7ab5", "14-30d"),
    ("🐌", t("turn.h_slow"), s["health"]["slow"], "#c5963d", "30-60d"),
    ("🧊", t("turn.h_stuck"), s["health"]["stuck"], "#c54c4c", "60d+"),
]
hcols = st.columns(4)
for i, (icon, label, count, color, doi_range) in enumerate(health_data):
    with hcols[i]:
        st.markdown(
            "<div style='text-align:center;padding:14px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px;"
            "border-top:3px solid " + color + "'>"
            "<div style='font-size:1.3rem'>" + icon + "</div>"
            "<div style='font-weight:600;font-size:13px'>" + label + "</div>"
            "<div style='font-size:1.6rem;font-weight:600;color:" + color + "'>"
            + str(count) + "</div>"
            "<div style='font-size:11px;color:#9a9485'>DOI " + doi_range + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Item table ---------------------------------------------------------------

st.divider()

items = st_mod.calculate()

tab_all, tab_reorder = st.tabs([
    "📋 " + t("turn.tab_all") + " (" + str(len(items)) + ")",
    "🔴 " + t("turn.tab_reorder") + " (" + str(s["need_reorder"]) + ")",
])


def _render_items(item_list):
    for item in item_list:
        health = item["health"]
        h_icon = {"fast": "🚀", "good": "✅", "slow": "🐌", "stuck": "🧊"}.get(health, "?")
        h_color = {"fast": "#4d6c5c", "good": "#4a7ab5", "slow": "#c5963d", "stuck": "#c54c4c"}.get(health, "#7a7569")

        doi_str = str(item["doi"]) + "d"
        tr_str = str(item["turnover_rate"]) + "x"
        daily_str = str(item["daily_sales"])
        stock_str = str(item.get("stock") or 0)
        rp_str = str(item["reorder_point"])
        stk_val_str = "{:,.0f}".format(item["stock_value"])

        reorder_badge = ""
        if item["needs_reorder"]:
            reorder_badge = (
                " <span style='background:#c54c4c;color:white;padding:1px 6px;"
                "border-radius:4px;font-size:10px'>REORDER</span>"
            )

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid " + h_color + "'>"
            "<div>"
            "<span style='font-weight:600'>" + h_icon + " " + item["sku"] + "</span>"
            " <span style='color:#7a7569;font-size:12px'>" + (item["name"] or "")[:25] + "</span>"
            + reorder_badge +
            "</div>"
            "<div style='display:flex;gap:12px;align-items:center;font-size:12px'>"
            "<span>📦 " + stock_str + "</span>"
            "<span>📈 " + daily_str + "/d</span>"
            "<span style='color:" + h_color + ";font-weight:600'>DOI " + doi_str + "</span>"
            "<span>" + tr_str + "/yr</span>"
            "<span>RP " + rp_str + "</span>"
            "<span style='color:#9a9485'>฿" + stk_val_str + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


with tab_all:
    _render_items(sorted(items, key=lambda x: x["doi"]))

with tab_reorder:
    reorder = st_mod.reorder_list()
    if reorder:
        st.error(t("turn.reorder_alert"))
        _render_items(reorder)
    else:
        st.success(t("turn.no_reorder"))
