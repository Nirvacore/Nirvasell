"""H2 Profit Calendar — see daily/weekly profit at a glance."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import profit_calendar as pc
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("pcal.title"))
st.caption(t("pcal.caption"))

tab_daily, tab_weekly, tab_best = st.tabs([
    t("pcal.tab_daily"), t("pcal.tab_weekly"), t("pcal.tab_best")
])

with tab_daily:
    days = st.segmented_control(t("pcal.period"), [30,60,90], default=30,
        format_func=lambda d: str(d) + t("pcal.days"))
    daily = pc.daily_profits(days=int(days or 30))
    if not daily:
        st.info(t("pcal.empty"))
    else:
        profits = [d.get("net_profit",0) for d in daily]
        max_abs = max(abs(p) for p in profits) or 1
        for d in daily:
            profit = d.get("net_profit",0)
            bar_color = "#4d6c5c" if profit >= 0 else "#c54c4c"
            bar_w = int(abs(profit) / max_abs * 180)
            dot = "🟢" if profit > 0 else ("🔴" if profit < 0 else "⚫")
            row_html = (
                "<div style='display:flex;align-items:center;gap:6px;margin:2px 0;"
                "font-size:0.82rem'>"
                "<span style='width:78px;color:#9a9485'>" +
                (d.get("date") or "—") + "</span>"
                "<span>" + dot + "</span>"
                "<div style='background:" + bar_color + ";width:" +
                str(bar_w) + "px;height:8px'></div>"
                "<span style='color:" + bar_color + ";font-variant-numeric:tabular-nums;"
                "min-width:80px'>" +
                ("+" if profit > 0 else "") + "฿{:,.0f}".format(profit) +
                "</span></div>"
            )
            st.html(row_html)

with tab_weekly:
    weekly = pc.weekly_summary(days=90)
    if not weekly:
        st.info(t("pcal.empty"))
    else:
        max_p = max(abs(w.get("net_profit",0)) for w in weekly) or 1
        for w in weekly:
            profit = w.get("net_profit",0)
            rev    = w.get("revenue",0)
            orders = w.get("orders",0)
            color  = "#4d6c5c" if profit >= 0 else "#c54c4c"
            bar_w  = int(abs(profit) / max_p * 160)
            w_html = (
                "<div style='margin:4px 0;font-size:0.83rem'>"
                "<div style='color:#9a9485'>" + (w.get("week") or "—") + "</div>"
                "<div style='display:flex;align-items:center;gap:6px;margin-top:2px'>"
                "<div style='background:" + color + ";width:" + str(bar_w) + "px;height:10px'></div>"
                "<span style='color:" + color + "'>" +
                ("+" if profit >= 0 else "") + "฿{:,.0f}".format(profit) +
                "</span>"
                "<span style='color:#9a9485;margin-left:8px'>" +
                str(orders) + t("pcal.orders") +
                " · rev ฿{:,.0f}".format(rev) +
                "</span></div></div>"
            )
            st.html(w_html)

with tab_best:
    col1, col2 = st.columns(2)
    bw = pc.best_worst_days(days=90, top=5)
    col1.subheader("🌟 " + t("pcal.best_days"))
    for d in bw.get("best",[]):
        col1.metric(d.get("date","—"), "฿{:,.0f}".format(d.get("net_profit",0)))

    col2.subheader("💀 " + t("pcal.worst_days"))
    for d in bw.get("worst",[]):
        col2.metric(d.get("date","—"),
                    "฿{:,.0f}".format(d.get("net_profit",0)),
                    delta_color="inverse")

    st.divider()
    monthly = pc.monthly_summary(months=6)
    if monthly:
        st.subheader(t("pcal.monthly_summary"))
        for m in monthly:
            profit_m = m.get("net_profit",0)
            c_m      = "#4d6c5c" if profit_m >= 0 else "#c54c4c"
            m_html   = (
                "<div style='margin:3px 0;font-size:0.83rem'>"
                "<span style='color:#9a9485;width:70px;display:inline-block'>" +
                (m.get("month","—")) + "</span>"
                "<span style='color:" + c_m + ";font-variant-numeric:tabular-nums'>" +
                ("+" if profit_m >= 0 else "") + "฿{:,.0f}".format(profit_m) +
                "</span></div>"
            )
            st.html(m_html)
