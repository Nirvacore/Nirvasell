"""F8 Price Optimizer — find optimal selling prices per platform."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import price_optimizer as po
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("popt.title"))
st.caption(t("popt.caption"))

tab_calc, tab_compare = st.tabs([t("popt.tab_calc"), t("popt.tab_compare")])

with tab_calc:
    st.subheader(t("popt.calc_title"))
    col1, col2 = st.columns(2)
    cost       = col1.number_input(t("popt.cost"), min_value=0.0, value=100.0, step=10.0)
    target_m   = col2.number_input(t("popt.target_margin"), min_value=0.0, value=25.0,
                                    step=5.0, format="%.0f")
    col3, col4 = st.columns(2)
    platform   = col3.selectbox(t("popt.platform"),
                                 ["shopee","lazada","tiktok_shop","facebook","line","direct"])
    psych      = col4.checkbox(t("popt.psych_price"), value=True)

    if cost > 0:
        result = po.optimal_price(cost=cost, target_margin_pct=target_m,
                                   platform=platform, round_psych=psych)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric(t("popt.optimal_price"), "฿{:,.0f}".format(result["optimal_price"]))
        r2.metric(t("popt.actual_margin"), str(result["actual_margin_pct"]) + "%",
                  delta_color="normal" if result["actual_margin_pct"] >= target_m else "inverse")
        r3.metric(t("popt.gross_profit"), "฿{:,.0f}".format(result["gross_profit"]))
        r4.metric(t("popt.platform_fees"), "฿{:,.0f}".format(result.get("platform_fee", 0)))

        breakdown_html = (
            "<div style='font-size:0.83rem;color:#9a9485;margin-top:8px'>"
            + t("popt.cost") + ": ฿{:,.0f}".format(cost)
            + " · " + t("popt.fee") + ": ฿{:,.0f}".format(result.get("platform_fee", 0))
            + " · " + t("popt.profit") + ": ฿{:,.0f}".format(result["gross_profit"])
            + "</div>"
        )
        st.html(breakdown_html)

        st.divider()
        st.subheader(t("popt.check_title"))
        col5, col6 = st.columns(2)
        check_price  = col5.number_input(t("popt.check_price"), value=float(result["optimal_price"]),
                                          step=10.0, min_value=0.0)
        check_plat   = col6.selectbox(t("popt.platform"), ["shopee","lazada","tiktok_shop","facebook","direct"],
                                       key="chk_plat")
        if check_price > 0:
            m = po.margin_at_price(cost, check_price, check_plat)
            cr1, cr2, cr3 = st.columns(3)
            cr1.metric(t("popt.fee"), "฿{:,.0f}".format(m.get("platform_fee", 0)))
            margin_c = "normal" if m["margin_pct"] >= target_m else "inverse"
            cr2.metric(t("popt.actual_margin"), str(m["margin_pct"]) + "%",
                       delta_color=margin_c)
            cr3.metric(t("popt.profit"), "฿{:,.0f}".format(m["profit"]))

with tab_compare:
    st.subheader(t("popt.compare_title"))
    col1, col2, col3 = st.columns(3)
    c_cost    = col1.number_input(t("popt.cost"), min_value=0.0, value=100.0, step=10.0,
                                   key="cmp_cost")
    c_margin  = col2.number_input(t("popt.target_margin"), min_value=0.0, value=25.0,
                                   step=5.0, key="cmp_m")
    c_psych   = col3.checkbox(t("popt.psych_price"), value=True, key="cmp_p")

    if c_cost > 0:
        results = po.compare_platforms(c_cost, c_margin, c_psych)
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.84rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("popt.platform"), t("popt.optimal_price"),
                    t("popt.fee"), t("popt.actual_margin"), t("popt.profit")]:
            table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
        table_html += "</tr>"
        best_margin = max(r["actual_margin_pct"] for r in results) if results else 0
        for r in results:
            is_best = r["actual_margin_pct"] == best_margin
            bg = " background:#1a2a1a" if is_best else ""
            col_m = "#4d6c5c" if r["actual_margin_pct"] >= c_margin else "#c54c4c"
            table_html += "<tr style='border-top:1px solid #2a2a2a;" + bg + "'>"
            table_html += "<td style='padding:4px 8px'>" + r["platform"] + ("⭐" if is_best else "") + "</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(r["optimal_price"]) + "</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(r.get("platform_fee",0)) + "</td>"
            table_html += "<td style='padding:4px 8px;color:" + col_m + "'>" + str(r["actual_margin_pct"]) + "%</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(r["gross_profit"]) + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)
