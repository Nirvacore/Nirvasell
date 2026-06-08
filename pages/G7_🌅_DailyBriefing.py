"""G7 Daily Briefing — morning ops digest: yesterday recap + today tasks."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import daily_briefing as db
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("brief.title"))
st.caption(t("brief.caption"))

if st.button("🔄 " + t("brief.refresh")):
    if "briefing" in st.session_state:
        del st.session_state["briefing"]

if "briefing" not in st.session_state:
    with st.spinner(t("brief.loading")):
        st.session_state["briefing"] = db.generate()

b = st.session_state["briefing"]

st.subheader("📅 " + (b.get("date") or "—"))
st.divider()

# Yesterday
yest = b.get("yesterday") or {}
st.subheader("📊 " + t("brief.yesterday"))
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("brief.y_orders"), yest.get("orders", 0))
c2.metric(t("brief.y_revenue"), "฿{:,.0f}".format(yest.get("revenue", 0)))
c3.metric(t("brief.y_top"), yest.get("top_sku") or "—")
c4.metric(t("brief.y_returns"), yest.get("returns", 0),
          delta_color="inverse" if yest.get("returns", 0) > 0 else "off")

# Quick stats
qs = b.get("quick_stats") or {}
if qs:
    st.divider()
    st.subheader("⚡ " + t("brief.quick_stats"))
    qs_cols = st.columns(4)
    ks_list = list(qs.items())[:8]
    for i, (k, v) in enumerate(ks_list):
        val_str = "฿{:,.0f}".format(v) if isinstance(v, (int,float)) and v > 99 else str(v)
        qs_cols[i % 4].metric(k, val_str)

# Alerts
alerts = b.get("alerts") or []
if alerts:
    st.divider()
    st.subheader("🚨 " + t("brief.alerts"))
    for a in alerts:
        icon  = a.get("icon","⚠️")
        label = a.get("label") or a.get("type","alert")
        msg   = a.get("message","")
        color = a.get("color","#c5963d")
        a_html = (
            "<div style='display:flex;gap:8px;align-items:flex-start;"
            "background:#1a1a1a;padding:8px;margin:4px 0'>"
            "<span style='font-size:1.2rem'>" + icon + "</span>"
            "<div><div style='color:" + color + ";font-size:0.85rem;font-weight:600'>" +
            label + "</div>"
            "<div style='color:#9a9485;font-size:0.82rem'>" + msg + "</div></div></div>"
        )
        st.html(a_html)

# Today tasks
tasks = b.get("today_tasks") or []
if tasks:
    st.divider()
    st.subheader("✅ " + t("brief.today_tasks"))
    for task in tasks:
        task_str = task if isinstance(task, str) else (task.get("label") or str(task))
        t_html = (
            "<div style='display:flex;align-items:center;gap:8px;margin:4px 0;"
            "font-size:0.85rem'>"
            "<div style='width:18px;height:18px;border:2px solid #4d6c5c;flex-shrink:0'></div>"
            "<span style='color:#d4d0c8'>" + task_str + "</span>"
            "</div>"
        )
        st.html(t_html)

if not yest and not tasks and not alerts:
    st.info(t("brief.empty"))
