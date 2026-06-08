"""Daily Briefing — open this first every morning.

Yesterday's results + today's tasks + alerts. Everything at a glance."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import daily_briefing as brief
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Daily Briefing",
                   page_icon="☀", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="☀", title=t("brief.title"), subtitle=t("brief.caption"))

b = brief.generate()


# ---- Quick stats (MTD) -------------------------------------------------------

qs = b["quick_stats"]
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("brief.mtd_orders"), str(qs["mtd_orders"]),
        hint=t("brief.mtd_hint"), hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("brief.mtd_revenue"), "{:,.0f}".format(qs["mtd_revenue"]),
        hint="", hint_tone="ok",
    )
with k3:
    metric_with_hint(
        t("brief.total_products"), str(qs["total_products"]),
        hint="", hint_tone="info",
    )


# ---- Yesterday ---------------------------------------------------------------

st.divider()
st.markdown("### 📊 " + t("brief.yesterday_title"))

y = b["yesterday"]
yc1, yc2, yc3 = st.columns(3)
with yc1:
    st.markdown(
        "<div style='text-align:center;padding:14px;background:white;"
        "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px'>"
        "<div style='font-size:12px;color:#7a7569'>📦 " + t("brief.y_orders") + "</div>"
        "<div style='font-size:1.6rem;font-weight:600'>" + str(y["orders"]) + "</div></div>",
        unsafe_allow_html=True,
    )
with yc2:
    st.markdown(
        "<div style='text-align:center;padding:14px;background:white;"
        "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px'>"
        "<div style='font-size:12px;color:#7a7569'>💰 " + t("brief.y_revenue") + "</div>"
        "<div style='font-size:1.6rem;font-weight:600;color:#4d6c5c'>"
        "฿" + "{:,.0f}".format(y["revenue"]) + "</div></div>",
        unsafe_allow_html=True,
    )
with yc3:
    st.markdown(
        "<div style='text-align:center;padding:14px;background:white;"
        "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px'>"
        "<div style='font-size:12px;color:#7a7569'>👥 " + t("brief.y_customers") + "</div>"
        "<div style='font-size:1.6rem;font-weight:600'>" + str(y["new_customers"]) + "</div></div>",
        unsafe_allow_html=True,
    )


# ---- Alerts ------------------------------------------------------------------

alerts = b["alerts"]
if alerts:
    st.divider()
    st.markdown("### 🚨 " + t("brief.alerts_title"))

    for a in alerts:
        a_color = "#c54c4c" if a["level"] == "danger" else "#c5963d"
        msg = a.get("msg_th", a.get("msg", ""))
        st.markdown(
            "<div style='padding:10px 14px;border-left:4px solid " + a_color + ";"
            "background:rgba(197,76,76,0.04);border-radius:0 8px 8px 0;margin-bottom:6px'>"
            + a["icon"] + " <strong>" + msg + "</strong></div>",
            unsafe_allow_html=True,
        )


# ---- Today's tasks -----------------------------------------------------------

st.divider()
st.markdown("### ✅ " + t("brief.tasks_title"))

tasks = b["today_tasks"]
if tasks:
    for task in tasks:
        p_color = {"high": "#c54c4c", "medium": "#c5963d", "low": "#9a9485"}.get(task["priority"], "#7a7569")
        p_badge = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(task["priority"], "?")
        task_text = task.get("task_th", task.get("task", ""))

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid " + p_color + "'>"
            "<span>" + p_badge + " " + task["icon"] + " " + task_text + "</span>"
            "<span style='font-size:11px;color:#9a9485'>→ " +
            task.get("page", "") + "</span></div>",
            unsafe_allow_html=True,
        )
else:
    st.success(t("brief.no_tasks"))


# ---- Motivational close ------------------------------------------------------

st.divider()
import random
quotes_th = [
    "💪 วันนี้ก็สู้ต่อนะคะ!",
    "🌟 ทุกออเดอร์คือความไว้วางใจ",
    "🚀 ขายดีเริ่มจากวันนี้",
    "💕 ลูกค้าทุกคนมีค่า",
    "🎯 ตั้งเป้า ทำจริง วัดผล",
]
st.markdown(
    "<div style='text-align:center;padding:16px;color:#9a9485;"
    "font-style:italic;font-size:14px'>"
    + quotes_th[hash(b["date"]) % len(quotes_th)] + "</div>",
    unsafe_allow_html=True,
)
