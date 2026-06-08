"""F2 Demand Forecast — predict next 30/60/90-day sales per SKU."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import demand_forecast as df
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("fcast.title"))
st.caption(t("fcast.caption"))

horizon = st.segmented_control(
    t("fcast.horizon"), [30, 60, 90],
    format_func=lambda d: str(d) + t("fcast.days"),
    default=30,
)

with st.spinner(t("fcast.loading")):
    summary = df.summary()
    risks   = df.stockout_risk(horizon_days=int(horizon or 30))
    forecasts = df.forecast_all(horizon_days=int(horizon or 30), limit=50)

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("fcast.kpi_skus"), summary.get("total_skus_with_data", len(forecasts)))
c2.metric(t("fcast.kpi_rising"), summary.get("rising", 0))
c3.metric(t("fcast.kpi_declining"), summary.get("declining", 0),
          delta_color="inverse" if summary.get("declining", 0) > 0 else "off")
c4.metric(t("fcast.kpi_stockout"), len(risks),
          delta_color="inverse" if risks else "off")

if risks:
    high_risks = [r for r in risks if r["risk_level"] == "high"]
    if high_risks:
        st.error("🚨 " + str(len(high_risks)) + t("fcast.high_risk_warning"))

st.divider()

tab_forecast, tab_risks = st.tabs([t("fcast.tab_forecast"), t("fcast.tab_risks")])

TREND_ICONS = {"rising": "📈", "stable": "➡️", "declining": "📉"}
CONF_COLORS = {"high": "#4d6c5c", "medium": "#c5963d", "low": "#7a7569"}

with tab_forecast:
    if not forecasts:
        st.info(t("fcast.empty"))
    else:
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.83rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("fcast.col_sku"), t("fcast.col_trend"), t("fcast.col_qty"),
                    t("fcast.col_revenue"), t("fcast.col_weekly"), t("fcast.col_conf")]:
            table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
        table_html += "</tr>"
        for f in forecasts:
            conf_color = CONF_COLORS.get(f["confidence"], "#9a9485")
            trend_icon = TREND_ICONS.get(f["trend"], "")
            table_html += "<tr style='border-top:1px solid #2a2a2a'>"
            table_html += "<td style='padding:4px 8px'>" + f["sku"] + "</td>"
            table_html += "<td style='padding:4px 8px'>" + trend_icon + " " + f["trend"] + "</td>"
            table_html += "<td style='padding:4px 8px'>" + str(int(f["forecast_qty"])) + t("fcast.units") + "</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(f["forecast_revenue"]) + "</td>"
            table_html += "<td style='padding:4px 8px;color:#9a9485'>" + str(round(f["weekly_avg"],1)) + t("fcast.per_week") + "</td>"
            table_html += "<td style='padding:4px 8px;color:" + conf_color + "'>" + f["confidence"] + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)

with tab_risks:
    st.subheader(t("fcast.stockout_title"))
    if not risks:
        st.success(t("fcast.no_risks"))
    else:
        for r in risks:
            risk_color = "#c54c4c" if r["risk_level"] == "high" else "#c5963d"
            risk_icon  = "🚨" if r["risk_level"] == "high" else "⚠️"
            risk_html = (
                "<div style='margin:4px 0;padding:6px 10px;border-left:3px solid " +
                risk_color + ";font-size:0.84rem'>"
                "<b>" + risk_icon + " " + r["sku"] + "</b>"
                " — สต็อก " + str(r["current_stock"]) + " ชิ้น"
                " · ต้องการ " + str(int(r["forecast_need"])) + " ชิ้น"
                " · ขาด " + str(r["deficit"]) + " ชิ้น"
                " · <span style='color:" + risk_color + "'>เหลือ " +
                str(r["coverage_days"]) + t("fcast.days") + "</span>"
                "</div>"
            )
            st.html(risk_html)
