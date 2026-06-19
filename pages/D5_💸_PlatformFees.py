"""D5 Platform Fees — fee calculator and actual fee summary."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import platform_fees as pf
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("fees.title"))
st.caption(t("fees.caption"))

tab_calc, tab_compare, tab_actual = st.tabs([
    t("fees.tab_calc"), t("fees.tab_compare"), t("fees.tab_actual")
])

with tab_calc:
    st.subheader(t("fees.calc_title"))
    col1, col2 = st.columns(2)
    platform = col1.selectbox(t("fees.sel_platform"), list(pf.PLATFORMS.keys()),
                               format_func=lambda k: pf.PLATFORMS[k]["label"])
    qty = col2.number_input(t("fees.qty"), min_value=1, value=1, step=1)
    sale_price = col1.number_input(t("fees.sale_price"), min_value=0.0, step=10.0, value=200.0)
    cost_price = col2.number_input(t("fees.cost_price"), min_value=0.0, step=10.0, value=100.0)

    if sale_price > 0:
        result = pf.calculate(platform, sale_price, cost_price, int(qty))
        st.divider()
        r1, r2, r3 = st.columns(3)
        r1.metric(t("fees.revenue"), "฿{:,.2f}".format(result["revenue"]))
        r2.metric(t("fees.total_fees"),
                  "฿{:,.2f}".format(result["total_fees"]),
                  delta="-" + str(result["fee_pct"]) + "%",
                  delta_color="inverse")
        r3.metric(t("fees.net_revenue"), "฿{:,.2f}".format(result["net_revenue"]))
        r4, r5, r6 = st.columns(3)
        r4.metric(t("fees.cogs"), "฿{:,.2f}".format(result["cogs"]))
        r5.metric(t("fees.gross_profit"), "฿{:,.2f}".format(result["gross_profit"]))
        r6.metric(t("fees.margin"), str(result["margin_pct"]) + "%")

        st.caption(pf.PLATFORMS[platform]["notes"])

        st.divider()
        st.write("**" + t("fees.fee_breakdown") + "**")
        breakdown_html = ""
        breakdown_html += "<div style='font-size:0.85rem'>"
        breakdown_html += t("fees.commission") + ": ฿{:,.2f}".format(result["commission"]) + "<br>"
        breakdown_html += t("fees.payment_fee") + ": ฿{:,.2f}".format(result["payment_fee"]) + "<br>"
        if result["transaction_fee"]:
            breakdown_html += t("fees.transaction_fee") + ": ฿{:,.2f}".format(result["transaction_fee"]) + "<br>"
        breakdown_html += t("fees.vat_on_fees",
                            amount="{:,.2f}".format(result["vat_on_fees"])) + "<br>"
        breakdown_html += "</div>"
        st.html(breakdown_html)

with tab_compare:
    st.subheader(t("fees.compare_title"))
    c1, c2 = st.columns(2)
    cmp_price = c1.number_input(t("fees.sale_price"), min_value=0.0, step=10.0,
                                 value=200.0, key="cmp_sp")
    cmp_cost  = c2.number_input(t("fees.cost_price"), min_value=0.0, step=10.0,
                                 value=100.0, key="cmp_cp")
    if cmp_price > 0:
        results = pf.compare_all(cmp_price, cmp_cost)
        best = max(results, key=lambda r: r["gross_profit"])

        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("fees.platform_col"), t("fees.fee_pct_col"),
                    t("fees.net_col"), t("fees.profit_col"), t("fees.margin_col")]:
            table_html += "<th style='text-align:left;padding:6px 8px'>" + col + "</th>"
        table_html += "</tr>"
        for r in results:
            bg = "background:#1a2a1a;" if r["platform"] == best["platform"] else ""
            table_html += "<tr style='border-top:1px solid #2a2a2a;" + bg + "'>"
            star = " ⭐" if r["platform"] == best["platform"] else ""
            table_html += "<td style='padding:6px 8px'>" + r["label"] + star + "</td>"
            table_html += "<td style='padding:6px 8px'>" + str(r["fee_pct"]) + "%</td>"
            table_html += "<td style='padding:6px 8px'>฿{:,.0f}".format(r["net_revenue"]) + "</td>"
            gp_color = "#4d6c5c" if r["gross_profit"] > 0 else "#c54c4c"
            table_html += "<td style='padding:6px 8px;color:" + gp_color + "'>฿{:,.0f}".format(r["gross_profit"]) + "</td>"
            table_html += "<td style='padding:6px 8px'>" + str(r["margin_pct"]) + "%</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)

with tab_actual:
    st.subheader(t("fees.actual_title"))
    days = st.segmented_control(t("fees.period"), [7, 30, 90], default=30,
                                 format_func=lambda d: str(d) + t("fees.days"))
    try:
        actual = pf.fee_summary_from_orders(int(days))
        if actual:
            total_rev = sum(r["revenue"] for r in actual)
            total_fees = sum(r["total_fees"] for r in actual)
            a1, a2, a3 = st.columns(3)
            a1.metric(t("fees.total_revenue"), "฿{:,.0f}".format(total_rev))
            a2.metric(t("fees.total_fees_paid"), "฿{:,.0f}".format(total_fees))
            a3.metric(t("fees.total_net"), "฿{:,.0f}".format(total_rev - total_fees))
            for r in actual:
                p = pf.PLATFORMS.get(r["platform"], {})
                with st.expander(p.get("icon","") + " " + r["label"] + " · " +
                                 str(r["orders"]) + t("fees.orders_unit")):
                    st.write(t("fees.revenue") + ": ฿{:,.0f}".format(r["revenue"]))
                    st.write(t("fees.total_fees") + ": ฿{:,.0f}".format(r["total_fees"]) +
                             " (" + str(r["fee_pct"]) + "%)")
                    st.write(t("fees.net_revenue") + ": ฿{:,.0f}".format(r["net_revenue"]))
        else:
            st.info(t("fees.no_data"))
    except Exception as e:
        st.error(str(e))
