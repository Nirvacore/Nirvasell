"""E2 KPI Scorecard — one-page business health overview."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import kpi_scorecard as ks
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("kpi.title"))
st.caption(t("kpi.caption"))

days = st.segmented_control(t("kpi.period"), [7, 30, 90, 365], default=30,
                              format_func=lambda d: str(d) + t("kpi.days"))

try:
    data = ks.all_kpis(int(days))
    trend = ks.trend_comparison(int(days))

    # Health score
    score = data["health_score"]
    score_color = "#4d6c5c" if score >= 70 else ("#c5963d" if score >= 40 else "#c54c4c")
    score_html = (
        "<div style='text-align:center;padding:20px 0'>"
        "<div style='font-size:3rem;font-weight:bold;color:" + score_color + "'>"
        + str(score) + "</div>"
        "<div style='color:#9a9485;font-size:0.9rem'>" + t("kpi.health_score") + " / 100</div>"
        "</div>"
    )
    st.html(score_html)
    st.divider()

    # Revenue section
    st.subheader(t("kpi.revenue_title"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("kpi.revenue"), "฿{:,.0f}".format(data["revenue"]),
                delta=str(trend["revenue_change_pct"]) + "% vs prev",
                delta_color="normal" if trend["revenue_change_pct"] >= 0 else "inverse")
    col2.metric(t("kpi.orders"), data["orders"],
                delta=str(trend["orders_change_pct"]) + "% vs prev",
                delta_color="normal" if trend["orders_change_pct"] >= 0 else "inverse")
    col3.metric(t("kpi.aov"), "฿{:,.0f}".format(data["aov"]))
    col4.metric(t("kpi.customers"), data["customers"])

    # Profit section
    st.subheader(t("kpi.profit_title"))
    p1, p2, p3, p4 = st.columns(4)
    p1.metric(t("kpi.gross_profit"), "฿{:,.0f}".format(data["gross_profit"]))
    margin_color = "normal" if data["margin_pct"] > 20 else "inverse"
    p2.metric(t("kpi.margin"), str(data["margin_pct"]) + "%",
              delta_color=margin_color)
    p3.metric(t("kpi.expenses"), "฿{:,.0f}".format(data["expenses"]))
    net_color = "normal" if data["net_profit"] > 0 else "inverse"
    p4.metric(t("kpi.net_profit"), "฿{:,.0f}".format(data["net_profit"]),
              delta_color=net_color)

    # Operations section
    st.subheader(t("kpi.ops_title"))
    o1, o2, o3, o4 = st.columns(4)
    o1.metric(t("kpi.low_stock"), data["low_stock_count"],
              delta_color="inverse" if data["low_stock_count"] > 0 else "off")
    o2.metric(t("kpi.out_of_stock"), data["out_of_stock"],
              delta_color="inverse" if data["out_of_stock"] > 0 else "off")
    o3.metric(t("kpi.avg_rating"), "⭐ " + str(data["avg_rating"]) if data["avg_rating"] else "—")
    o4.metric(t("kpi.unanswered_reviews"), data["unanswered_reviews"],
              delta_color="inverse" if data["unanswered_reviews"] > 0 else "off")

    # COD & customers
    st.subheader(t("kpi.cod_title"))
    d1, d2 = st.columns(2)
    d1.metric(t("kpi.cod_pending"), "฿{:,.0f}".format(data["cod_pending"]))
    d2.metric(t("kpi.cod_return_rate"), str(data["cod_return_rate"]) + "%",
              delta_color="inverse" if data["cod_return_rate"] > 10 else "off")

    # Insights
    st.divider()
    st.subheader(t("kpi.insights_title"))
    insights = []
    if data["margin_pct"] < 10:
        insights.append(t("kpi.insight_low_margin"))
    if data["low_stock_count"] > 3:
        insights.append(t("kpi.insight_low_stock"))
    if data["unanswered_reviews"] > 0:
        insights.append(t("kpi.insight_reviews"))
    if data["cod_return_rate"] > 15:
        insights.append(t("kpi.insight_cod_return"))
    if data["net_profit"] < 0:
        insights.append(t("kpi.insight_loss"))
    if not insights:
        insights.append(t("kpi.insight_good"))
    for ins in insights:
        st.write("• " + ins)

except Exception as e:
    st.error(t("kpi.error") + ": " + str(e))
