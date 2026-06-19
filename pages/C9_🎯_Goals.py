"""Goal Tracker — set and track daily/monthly revenue and order targets."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import goal_tracker as gt
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
gt.init()
render_sidebar()

page_header(icon="🎯", title=t("goal.title"), subtitle=t("goal.caption"))

s = gt.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("🎯 " + t("goal.kpi_active"), str(s["total_active"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("✅ " + t("goal.kpi_on_track"), str(s["on_track"]),
                     hint="", hint_tone="ok" if s["on_track"] > 0 else "info")
with k3:
    metric_with_hint("⚠️ " + t("goal.kpi_off_track"), str(s["off_track"]),
                     hint="", hint_tone="warn" if s["off_track"] > 0 else "ok")

# ---- Set new goal -----------------------------------------------------------
st.divider()
with st.expander(t("goal.set_title"), expanded=s["total_active"] == 0):
    with st.form("set_goal"):
        gc1, gc2, gc3 = st.columns(3)
        with gc1:
            goal_type = st.selectbox(
                t("goal.f_type"),
                list(gt.GOAL_TYPES.keys()),
                format_func=lambda k: gt.GOAL_TYPES[k]["icon"] + " " +
                gt.GOAL_TYPES[k]["label"],
            )
        with gc2:
            period = st.selectbox(
                t("goal.f_period"),
                list(gt.PERIODS.keys()),
                format_func=lambda k: gt.PERIODS[k],
            )
        with gc3:
            target = st.number_input(
                t("goal.f_target") + " (" + gt.GOAL_TYPES.get(goal_type, {}).get("unit", "") + ")",
                min_value=0.0, value=10000.0, step=500.0,
            )
        goal_notes = st.text_input(t("goal.f_notes"), placeholder="")
        if st.form_submit_button(t("goal.set_btn"), type="primary"):
            if target > 0:
                gt.set_goal(goal_type, period, target, notes=goal_notes.strip())
                toast(t("goal.set_ok"), icon="🎯")
                st.rerun()

# ---- Active goals -----------------------------------------------------------
st.divider()
st.markdown("### " + t("goal.active_title"))

goals = gt.current_goals()
if not goals:
    st.info(t("goal.empty"))
    st.stop()

for g in goals:
    pct = g["pct"]
    bar_color = "#4d6c5c" if pct >= 80 else ("#c5963d" if pct >= 50 else "#c54c4c")
    period_label = g["period_label"]

    st.markdown(
        "<div style='padding:12px 16px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-radius:10px;background:white;margin-bottom:8px'>"
        "<div style='display:flex;justify-content:space-between;"
        "align-items:baseline;margin-bottom:6px'>"
        "<span>" + g["goal_icon"] + " <strong>" + g["goal_label"] +
        "</strong> <span style='font-size:11px;color:#9a9485'>[" +
        period_label + "]</span></span>"
        "<span style='font-size:13px'>"
        + t("goal.progress_line",
            actual="{:,.0f}".format(g["actual"]),
            target="{:,.0f}".format(g["target"]))
        + " <span style='font-weight:700;color:" + bar_color + "'>" +
        str(pct) + "%</span></span></div>"
        "<div style='background:rgba(40,30,20,0.06);border-radius:4px;height:10px'>"
        "<div style='width:" + str(pct) + "%;height:100%;background:" + bar_color + ";"
        "border-radius:4px'></div></div></div>",
        unsafe_allow_html=True,
    )
