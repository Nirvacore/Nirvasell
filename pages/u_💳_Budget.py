"""Budget Tracker — set limits, track overspend per category.

Know where money goes. Set budgets. Get warned before overspending."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import budget_tracker as bt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import budget_category

st.set_page_config(page_title="nirva.sell · Budget",
                   page_icon="💳", layout="wide")
apply_theme()
require_auth()
db.init()
bt.init()
render_sidebar()

page_header(icon="💳", title=t("bgt.title"), subtitle=t("bgt.caption"))

s = bt.summary()


# ---- KPIs -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("bgt.kpi_budget"), "{:,.0f}".format(s["total_budget"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("bgt.kpi_spent"), "{:,.0f}".format(s["total_spent"]),
        hint=str(s["used_pct"]) + "% used",
        hint_tone="ok" if s["used_pct"] < 80 else ("warn" if s["used_pct"] < 100 else "danger"),
    )
with k3:
    metric_with_hint(
        t("bgt.kpi_remaining"), "{:,.0f}".format(s["total_remaining"]),
        hint="", hint_tone="ok" if s["total_remaining"] > 0 else "danger",
    )
with k4:
    metric_with_hint(
        "🔴 " + t("bgt.kpi_over"), str(s["over"]),
        hint=t("bgt.over_hint") if s["over"] > 0 else "",
        hint_tone="danger" if s["over"] > 0 else "ok",
    )


# ---- Set budgets -------------------------------------------------------------

st.divider()
with st.expander(t("bgt.set_title"), expanded=s["total_budget"] == 0):
    with st.form("set_budgets"):
        st.caption(t("bgt.set_help"))

        budget_inputs = {}
        cat_keys = list(bt.CATEGORIES.keys())
        for i in range(0, len(cat_keys), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(cat_keys):
                    cat = cat_keys[idx]
                    info = bt.CATEGORIES[cat]
                    with col:
                        # Get existing budget
                        existing = [b for b in bt.all_budgets() if b["category"] == cat]
                        default_val = existing[0]["monthly_limit"] if existing else 0.0

                        budget_inputs[cat] = st.number_input(
                            info["icon"] + " " + budget_category(cat),
                            min_value=0.0,
                            value=float(default_val),
                            step=500.0,
                            key="_bgt_" + cat,
                        )

        if st.form_submit_button(t("bgt.save_btn"), type="primary"):
            for cat, limit in budget_inputs.items():
                if limit > 0:
                    bt.set_budget(cat, limit)
            toast(t("bgt.saved"), icon="✓")
            st.rerun()


# ---- Budget vs Actual -------------------------------------------------------

items = bt.budget_vs_actual()
if items:
    st.divider()
    st.markdown("### " + t("bgt.vs_actual"))

    for item in items:
        status = item["status"]
        bar_color = {
            "over": "#c54c4c",
            "warning": "#c5963d",
            "ok": "#4d6c5c",
            "no_budget": "#9a9485",
        }.get(status, "#9a9485")

        status_icon = {
            "over": "🔴",
            "warning": "🟡",
            "ok": "🟢",
            "no_budget": "⚪",
        }.get(status, "?")

        spent_str = "{:,.0f}".format(item["spent"])
        budget_str = "{:,.0f}".format(item["budget"]) if item["budget"] > 0 else "—"
        pct_str = str(item["used_pct"]) + "%" if item["budget"] > 0 else ""

        bar_width = min(item["used_pct"], 100) if item["budget"] > 0 else 0

        st.markdown(
            "<div style='padding:10px 14px;margin-bottom:6px'>"
            "<div style='display:flex;justify-content:space-between;align-items:baseline;"
            "margin-bottom:4px'>"
            "<span>" + status_icon + " " + item["icon"] + " <strong>" + budget_category(item["category"]) + "</strong></span>"
            "<span style='font-size:13px'>"
            "<span style='color:#7a7569'>฿" + spent_str + "</span>"
            " / <span style='color:#9a9485'>฿" + budget_str + "</span>"
            " <span style='font-weight:600;color:" + bar_color + "'>" + pct_str + "</span>"
            "</span></div>"
            "<div style='background:rgba(40,30,20,0.06);border-radius:4px;height:8px;"
            "overflow:hidden'>"
            "<div style='width:" + str(bar_width) + "%;height:100%;background:" + bar_color + ";"
            "border-radius:4px;transition:width 0.3s'></div>"
            "</div></div>",
            unsafe_allow_html=True,
        )
