"""Dead Stock — find cash trapped on shelves.

Products that haven't sold in 30-60+ days are bleeding cash.
Better to sell at a loss than hold forever."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import dead_stock as ds
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Dead Stock",
                   page_icon="💀", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="💀", title=t("dead.title"), subtitle=t("dead.caption"))


# ---- Period selector ---------------------------------------------------------

period = st.selectbox(
    t("dead.period"),
    [30, 60, 90],
    format_func=lambda d: str(d) + " " + t("dashboard.days"),
    label_visibility="collapsed",
)

s = ds.summary(period)

# ---- KPIs -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("dead.kpi_total"), str(s["total_items"]),
        hint=t("dead.kpi_total_hint"), hint_tone="warn" if s["total_items"] > 0 else "ok",
    )
with k2:
    metric_with_hint(
        t("dead.kpi_trapped"), "{:,.0f}".format(s["trapped_cash"]),
        hint=t("dead.kpi_trapped_hint"), hint_tone="danger" if s["trapped_cash"] > 5000 else "info",
    )
with k3:
    metric_with_hint(
        "💀 " + t("dead.label_dead"), str(s["dead"]),
        hint="60+ " + t("dashboard.days"), hint_tone="danger" if s["dead"] > 0 else "ok",
    )
with k4:
    metric_with_hint(
        "🐌 " + t("dead.label_slow"), str(s["slow"]),
        hint=t("dead.slow_hint"), hint_tone="warn" if s["slow"] > 0 else "ok",
    )


# ---- Trapped cash breakdown -------------------------------------------------

if s["total_items"] > 0:
    st.divider()
    st.markdown("### " + t("dead.breakdown_title"))

    breakdown = [
        ("💀", t("dead.label_dead"), s["dead_trapped"], "#c54c4c"),
        ("🧊", t("dead.label_stale"), s["stale_trapped"], "#c5963d"),
        ("🐌", t("dead.label_slow"), s["slow_trapped"], "#9a9485"),
    ]
    bcols = st.columns(3)
    for i, (icon, label, amount, color) in enumerate(breakdown):
        with bcols[i]:
            st.markdown(
                "<div style='text-align:center;padding:16px;background:white;"
                "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px'>"
                "<div style='font-size:1.5rem'>" + icon + "</div>"
                "<div style='font-size:12px;color:#7a7569'>" + label + "</div>"
                "<div style='font-size:1.4rem;font-weight:600;color:" + color + "'>"
                "฿" + "{:,.0f}".format(amount) + "</div></div>",
                unsafe_allow_html=True,
            )


# ---- Item list ---------------------------------------------------------------

items = ds.detect(period)
if items:
    st.divider()
    st.markdown("### " + t("dead.list_title"))

    sev_filter = st.selectbox(
        t("dead.filter_sev"),
        ["all", "dead", "stale", "slow"],
        format_func=lambda k: {
            "all": "📋 " + t("dead.filter_all"),
            "dead": "💀 " + t("dead.label_dead"),
            "stale": "🧊 " + t("dead.label_stale"),
            "slow": "🐌 " + t("dead.label_slow"),
        }.get(k, k),
        label_visibility="collapsed",
    )

    filtered = items if sev_filter == "all" else [i for i in items if i["severity"] == sev_filter]

    for item in filtered:
        sev = item["severity"]
        sev_icon = {"dead": "💀", "stale": "🧊", "slow": "🐌"}.get(sev, "?")
        sev_color = {"dead": "#c54c4c", "stale": "#c5963d", "slow": "#9a9485"}.get(sev, "#7a7569")

        trapped_str = "{:,.0f}".format(item["trapped_cash"])
        days_str = str(item["days_since_sale"]) + "d"
        stock_str = str(item.get("stock") or 0)

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid " + sev_color + "'>"
            "<div>"
            "<span style='font-weight:600'>" + sev_icon + " " + item["sku"] + "</span>"
            " <span style='color:#7a7569;font-size:12px'>" + (item["name"] or "")[:25] + "</span>"
            "</div>"
            "<div style='display:flex;gap:14px;align-items:center;font-size:13px'>"
            "<span>📦 " + stock_str + "</span>"
            "<span>📅 " + t("common.days_ago", n=str(item["days_since_sale"])) + "</span>"
            "<span style='font-weight:600;color:" + sev_color + "'>" +
            t("dead.trapped_cash", amount=trapped_str) + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Action suggestions -----------------------------------------------------

suggestions = ds.suggest_actions(items if items else None)
if suggestions:
    st.divider()
    st.markdown("### " + t("dead.suggest_title"))

    for sg in suggestions[:10]:
        sev_icon = {"dead": "💀", "stale": "🧊", "slow": "🐌"}.get(sg["severity"], "?")
        st.markdown(
            "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            + sev_icon + " **" + sg["sku"] + "** — "
            + sg.get("suggestion", "") + "</div>",
            unsafe_allow_html=True,
        )
