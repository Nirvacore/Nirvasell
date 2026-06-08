"""H0 Cash Flow — daily/monthly inflow vs outflow and forecast."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cash_flow as cf
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("cf.title"))
st.caption(t("cf.caption"))

summary = cf.summary()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("cf.kpi_inflow"), "฿{:,.0f}".format(summary.get("total_inflow",0)))
c2.metric(t("cf.kpi_outflow"), "฿{:,.0f}".format(summary.get("total_outflow",0)))
net = summary.get("net_flow",0)
c3.metric(t("cf.kpi_net"), "฿{:,.0f}".format(net),
          delta_color="normal" if net >= 0 else "inverse")
forecast = cf.current_month_forecast()
c4.metric(t("cf.kpi_forecast"), "฿{:,.0f}".format(forecast.get("projected_net",0)))

st.divider()
tab_daily, tab_monthly = st.tabs([t("cf.tab_daily"), t("cf.tab_monthly")])

with tab_daily:
    days = st.segmented_control(t("cf.period"), [7,14,30], default=14,
        format_func=lambda d: str(d) + t("cf.days"))
    daily = cf.daily(days=int(days or 14))
    if not daily:
        st.info(t("cf.empty"))
    else:
        max_val = max(max(abs(d.get("inflow",0)), abs(d.get("outflow",0))) for d in daily) or 1
        for d in daily:
            inf_w = int(d.get("inflow",0) / max_val * 160)
            out_w = int(d.get("outflow",0) / max_val * 160)
            net_d  = d.get("inflow",0) - d.get("outflow",0)
            net_c  = "#4d6c5c" if net_d >= 0 else "#c54c4c"
            row_html = (
                "<div style='margin:3px 0;font-size:0.82rem'>"
                "<span style='color:#9a9485;width:80px;display:inline-block'>" +
                (d.get("date") or "—") + "</span>"
                "<span style='display:inline-block;background:#4d6c5c;width:" +
                str(inf_w) + "px;height:10px;margin-right:4px'></span>"
                "<span style='display:inline-block;background:#c54c4c;width:" +
                str(out_w) + "px;height:10px;margin-right:8px'></span>"
                "<span style='color:" + net_c + ";font-variant-numeric:tabular-nums'>" +
                ("+" if net_d >= 0 else "") + "฿{:,.0f}".format(net_d) + "</span>"
                "</div>"
            )
            st.html(row_html)
        legend_html = (
            "<div style='font-size:0.78rem;color:#9a9485;margin-top:4px'>"
            "<span style='display:inline-block;background:#4d6c5c;width:12px;height:8px'></span>"
            " " + t("cf.inflow") + "  "
            "<span style='display:inline-block;background:#c54c4c;width:12px;height:8px;margin-left:8px'></span>"
            " " + t("cf.outflow") +
            "</div>"
        )
        st.html(legend_html)

with tab_monthly:
    months = st.slider(t("cf.months_slider"), 2, 12, 6)
    monthly = cf.monthly(months=int(months))
    if not monthly:
        st.info(t("cf.empty"))
    table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.84rem'>"
    table_html += "<tr style='color:#9a9485'>"
    for col in [t("cf.month"), t("cf.inflow"), t("cf.outflow"), t("cf.net")]:
        table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
    table_html += "</tr>"
    for m in monthly:
        net_m  = m.get("inflow",0) - m.get("outflow",0)
        net_c  = "#4d6c5c" if net_m >= 0 else "#c54c4c"
        table_html += "<tr style='border-top:1px solid #2a2a2a'>"
        table_html += "<td style='padding:4px 8px;color:#9a9485'>" + (m.get("month","—")) + "</td>"
        table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(m.get("inflow",0)) + "</td>"
        table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(m.get("outflow",0)) + "</td>"
        table_html += "<td style='padding:4px 8px;color:" + net_c + "'>฿{:,.0f}".format(net_m) + "</td>"
        table_html += "</tr>"
    table_html += "</table>"
    if monthly:
        st.html(table_html)
