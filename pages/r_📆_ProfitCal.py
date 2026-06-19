"""Profit Calendar — daily profit heatmap.

Which days made money? Which lost? Spot weekly patterns instantly."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import profit_calendar as pc
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Profit Calendar",
                   page_icon="📆", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📆", title=t("pcal.title"), subtitle=t("pcal.caption"))

# ---- Monthly summary bars ---------------------------------------------------

months = pc.monthly_summary(6)
if not months:
    st.info(t("pcal.empty"))
    st.stop()

st.markdown("### " + t("pcal.monthly_title"))
mcols = st.columns(len(months))
for i, m in enumerate(months):
    with mcols[i]:
        p_color = "#4d6c5c" if m["profit"] >= 0 else "#c54c4c"
        p_icon = "📈" if m["profit"] >= 0 else "📉"
        st.markdown(
            "<div style='text-align:center;padding:12px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px;"
            "border-top:3px solid " + p_color + "'>"
            "<div style='font-weight:600;color:#7a7569;font-size:12px'>"
            + m["month"] + "</div>"
            "<div style='font-size:1.3rem;font-weight:600;color:" + p_color + "'>"
            + p_icon + " ฿" + "{:,.0f}".format(m["profit"]) + "</div>"
            "<div style='font-size:11px;color:#9a9485'>"
            + str(m["days_with_sales"]) + " " + t("pcal.active_days") + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Weekly breakdown -------------------------------------------------------

st.divider()
st.markdown("### " + t("pcal.weekly_title"))

weeks = pc.weekly_summary(90)
for w in weeks[-8:]:  # last 8 weeks
    profit = w["profit"]
    p_color = "#4d6c5c" if profit >= 0 else "#c54c4c"
    rev_str = "{:,.0f}".format(w["revenue"])
    prof_str = "{:,.0f}".format(profit)
    days_str = str(w["days_with_sales"]) + "/7"

    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<div>"
        "<span style='font-weight:600;font-size:13px;color:#7a7569'>"
        + w["start"][:10] + " → " + w["end"][:10] + "</span>"
        " <span style='font-size:11px;color:#9a9485'>" + days_str + t("pcal.week_days_suffix") + "</span>"
        "</div>"
        "<div style='display:flex;gap:14px;align-items:center'>"
        "<span style='font-size:12px;color:#9a9485'>💵 ฿" + rev_str + "</span>"
        "<span style='font-weight:600;color:" + p_color + "'>"
        "฿" + prof_str + "</span></div></div>",
        unsafe_allow_html=True,
    )


# ---- Best / Worst days ------------------------------------------------------

st.divider()
bw = pc.best_worst_days(90, 5)

bcol, wcol = st.columns(2)
with bcol:
    st.markdown("### 🏆 " + t("pcal.best_days"))
    for d in bw["best"]:
        st.markdown(
            "<div style='padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "🟢 <strong>" + d["date"] + "</strong>"
            " (" + d["weekday"] + ")"
            " — <span style='color:#4d6c5c;font-weight:600'>฿" +
            "{:,.0f}".format(d["profit"]) + "</span></div>",
            unsafe_allow_html=True,
        )

with wcol:
    st.markdown("### 💔 " + t("pcal.worst_days"))
    for d in bw["worst"]:
        p_color = "#c54c4c" if d["profit"] < 0 else "#9a9485"
        st.markdown(
            "<div style='padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "🔴 <strong>" + d["date"] + "</strong>"
            " (" + d["weekday"] + ")"
            " — <span style='color:" + p_color + ";font-weight:600'>฿" +
            "{:,.0f}".format(d["profit"]) + "</span></div>",
            unsafe_allow_html=True,
        )
