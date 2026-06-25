"""F0 P&L Statement — formal income statement by month, quarter, year."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pnl_statement as pnl
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import expense_category
from sidebar import render_sidebar
from datetime import datetime

apply_theme()
require_auth()
render_sidebar()

st.title(t("pnl.title"))
st.caption(t("pnl.caption"))

tab_month, tab_quarter, tab_year, tab_trend = st.tabs([
    t("pnl.tab_month"), t("pnl.tab_quarter"), t("pnl.tab_year"), t("pnl.tab_trend")
])

def _render_pnl(p: dict):
    profitable = p.get("profitable", False)
    if profitable:
        st.success("✅ " + t("pnl.profitable"))
    else:
        st.error("❌ " + t("pnl.loss"))

    r1, r2, r3, r4 = st.columns(4)
    r1.metric(t("pnl.revenue"), "฿{:,.0f}".format(p["revenue"]))
    r2.metric(t("pnl.net_revenue"), "฿{:,.0f}".format(p["net_revenue"]))
    r3.metric(t("pnl.units"), str(p["units_sold"]))
    r4.metric(t("pnl.returns"), "฿{:,.0f}".format(p["returns"]),
              delta_color="inverse" if p["returns"] > 0 else "off")

    st.divider()
    p1, p2, p3 = st.columns(3)
    p1.metric(t("pnl.cogs"), "฿{:,.0f}".format(p["cogs"]))
    p2.metric(t("pnl.gross_profit"), "฿{:,.0f}".format(p["gross_profit"]))
    p3.metric(t("pnl.gross_margin"), str(p["gross_margin"]) + "%",
              delta_color="normal" if p["gross_margin"] > 20 else "inverse")

    st.divider()
    p4, p5, p6 = st.columns(3)
    p4.metric(t("pnl.expenses"), "฿{:,.0f}".format(p["total_expenses"]))
    net_color = "normal" if p["net_profit"] > 0 else "inverse"
    p5.metric(t("pnl.net_profit"), "฿{:,.0f}".format(p["net_profit"]),
              delta_color=net_color)
    p6.metric(t("pnl.net_margin"), str(p["net_margin"]) + "%",
              delta_color=net_color)

    if p["expenses"]:
        st.subheader(t("pnl.expense_breakdown"))
        total_exp = p["total_expenses"] or 1
        for cat, amt in sorted(p["expenses"].items(), key=lambda x: x[1], reverse=True):
            pct = round(amt / total_exp * 100, 1)
            bar_w = int(pct * 2)
            row_html = (
                "<div style='margin:2px 0;font-size:0.83rem'>"
                "<span style='color:#9a9485;width:160px;display:inline-block'>" + expense_category(cat) + "</span>"
                "<div style='display:inline-block;background:#2a2a2a;width:" +
                str(bar_w) + "px;height:10px;vertical-align:middle'></div>"
                " <span style='color:#d4d0c8'>฿{:,.0f}".format(amt) +
                " (" + str(pct) + "%)</span>"
                "</div>"
            )
            st.html(row_html)

with tab_month:
    now = datetime.now()
    col1, col2 = st.columns(2)
    year_m  = col1.number_input(t("pnl.year"), value=now.year, min_value=2020, max_value=2040, step=1)
    month_m = col2.selectbox(t("pnl.month"), list(range(1,13)),
                              index=now.month-1,
                              format_func=lambda m: str(m).zfill(2))
    with st.spinner(t("pnl.loading")):
        data_m = pnl.monthly(int(year_m), int(month_m))
    st.subheader(data_m["label"])
    _render_pnl(data_m)

with tab_quarter:
    col1, col2 = st.columns(2)
    year_q = col1.number_input(t("pnl.year"), value=datetime.now().year,
                                min_value=2020, max_value=2040, step=1, key="pnl_yr_q")
    qtr    = col2.selectbox(t("pnl.quarter"), [1,2,3,4],
                             format_func=lambda q: "Q" + str(q))
    with st.spinner(t("pnl.loading")):
        data_q = pnl.quarterly(int(year_q), int(qtr))
    st.subheader(data_q["label"])
    _render_pnl(data_q)

with tab_year:
    year_a = st.number_input(t("pnl.year"), value=datetime.now().year,
                              min_value=2020, max_value=2040, step=1, key="pnl_yr_a")
    with st.spinner(t("pnl.loading")):
        data_a = pnl.annual(int(year_a))
    st.subheader(data_a["label"])
    _render_pnl(data_a)

with tab_trend:
    st.subheader(t("pnl.trend_title"))
    months_t = st.slider(t("pnl.months"), 3, 12, 6)
    with st.spinner(t("pnl.loading")):
        trend = pnl.monthly_trend(months=months_t)
    if trend:
        max_rev = max(abs(r["revenue"]) for r in trend) or 1
        for r in trend:
            np = r["net_profit"]
            color = "#4d6c5c" if np > 0 else "#c54c4c"
            bar_w = int(abs(r["revenue"]) / max_rev * 200)
            row_html = (
                "<div style='margin:4px 0;font-size:0.84rem'>"
                "<span style='color:#9a9485;width:75px;display:inline-block'>" + r["month"] + "</span>"
                "<div style='display:inline-block;background:#2a2a2a;width:" +
                str(bar_w) + "px;height:12px;vertical-align:middle'></div>"
                " <span style='color:#d4d0c8'>฿{:,.0f}".format(r["revenue"]) +
                t("pnl.trend_rev") + "</span>"
                " <span style='color:" + color + ";margin-left:8px'>"
                "฿{:,.0f}".format(np) + t("pnl.trend_net") + "</span>"
                "</div>"
            )
            st.html(row_html)
    else:
        st.info(t("pnl.empty"))
