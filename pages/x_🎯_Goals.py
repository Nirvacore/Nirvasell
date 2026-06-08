"""Goals — set targets, track progress, celebrate wins.

Monthly revenue, order count, profit targets with visual progress."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
import db
import goals
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Goals",
                   page_icon="🎯", layout="wide")
apply_theme()
require_auth()
db.init()
goals.init()
render_sidebar()

page_header(icon="🎯", title=t("goal.title"), subtitle=t("goal.caption"))

current_period = date.today().strftime("%Y-%m")

# ---- Set goals ---------------------------------------------------------------

with st.expander(t("goal.set_title"), expanded=False):
    with st.form("set_goals"):
        st.caption(t("goal.set_help"))
        g_inputs = {}
        metric_keys = list(goals.METRICS.keys())
        cols = st.columns(len(metric_keys))
        for i, mk in enumerate(metric_keys):
            info = goals.METRICS[mk]
            with cols[i]:
                g_inputs[mk] = st.number_input(
                    info["icon"] + " " + info["label"],
                    min_value=0.0, value=0.0, step=1000.0,
                    key="_goal_" + mk,
                )

        if st.form_submit_button(t("goal.save_btn"), type="primary"):
            for mk, val in g_inputs.items():
                if val > 0:
                    goals.set_goal(current_period, mk, val)
            toast(t("goal.saved"), icon="✓")
            st.rerun()


# ---- Goal progress -----------------------------------------------------------

goal_list = goals.goals_for_period(current_period)

if not goal_list:
    st.info(t("goal.empty"))
    st.caption(t("goal.empty_hint"))
    st.stop()

s = goals.summary(current_period)

# KPIs
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("🏆 " + t("goal.kpi_achieved"), str(s["achieved"]),
                     hint="", hint_tone="ok")
with k2:
    metric_with_hint("✅ " + t("goal.kpi_on_track"), str(s["on_track"]),
                     hint="", hint_tone="ok")
with k3:
    metric_with_hint("⚠️ " + t("goal.kpi_behind"), str(s["behind"]),
                     hint="", hint_tone="warn")
with k4:
    metric_with_hint("🔴 " + t("goal.kpi_at_risk"), str(s["at_risk"]),
                     hint="", hint_tone="danger" if s["at_risk"] > 0 else "ok")

st.divider()

# Goal cards with progress bars
for g in goal_list:
    status = g["status"]
    s_icon = {"achieved": "🏆", "on_track": "✅", "behind": "⚠️", "at_risk": "🔴"}.get(status, "?")
    s_color = {"achieved": "#4d6c5c", "on_track": "#4a7ab5",
               "behind": "#c5963d", "at_risk": "#c54c4c"}.get(status, "#7a7569")

    unit = g["unit"]
    actual_str = unit + "{:,.0f}".format(g["actual"]) if unit else "{:,.0f}".format(g["actual"])
    target_str = unit + "{:,.0f}".format(g["target"]) if unit else "{:,.0f}".format(g["target"])
    pct_str = str(min(g["pct"], 100)) + "%"
    bar_width = min(g["pct"], 100)

    # Pace indicator
    pace_bar = g["pace_pct"]

    st.markdown(
        "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + s_color + ";border-radius:10px;"
        "padding:14px 16px;margin-bottom:8px'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline;"
        "margin-bottom:6px'>"
        "<span>" + s_icon + " " + g["icon"] + " <strong>" + g["label"] + "</strong></span>"
        "<span style='font-size:1.2rem;font-weight:600;color:" + s_color + "'>"
        + actual_str + " / " + target_str + "</span></div>"
        "<div style='position:relative;background:rgba(40,30,20,0.06);"
        "border-radius:4px;height:12px;overflow:hidden'>"
        "<div style='position:absolute;left:" + str(int(pace_bar)) + "%;"
        "top:0;bottom:0;width:2px;background:rgba(40,30,20,0.2);z-index:1'></div>"
        "<div style='width:" + str(int(bar_width)) + "%;height:100%;background:" + s_color + ";"
        "border-radius:4px;transition:width 0.3s'></div></div>"
        "<div style='display:flex;justify-content:space-between;font-size:11px;"
        "color:#9a9485;margin-top:4px'>"
        "<span>" + pct_str + " · " + str(g["days_elapsed"]) + "d elapsed</span>"
        "<span>" + str(g["days_remaining"]) + "d remaining</span></div></div>",
        unsafe_allow_html=True,
    )
