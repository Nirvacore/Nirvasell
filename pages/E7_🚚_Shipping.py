"""E7 Shipping Calculator — compare carriers, find cheapest, see true margin."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import shipping_calc as sc
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import carrier_name, ship_est_days
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("ship.title"))
st.caption(t("ship.caption"))

tab_compare, tab_margin, tab_rates = st.tabs([
    t("ship.tab_compare"), t("ship.tab_margin"), t("ship.tab_rates")
])

with tab_compare:
    st.subheader(t("ship.compare_title"))
    col1, col2, col3 = st.columns(3)
    weight   = col1.number_input(t("ship.weight"), min_value=0.1, value=0.5,
                                   step=0.1, format="%.1f",
                                   help=t("ship.weight_help"))
    order_amt = col2.number_input(t("ship.order_amount"), min_value=0.0,
                                   value=0.0, step=50.0)
    is_cod   = col3.checkbox(t("ship.is_cod"))

    results = sc.compare_all(weight, order_amt, is_cod)
    cheapest = results[0]["carrier"] if results else None

    if results:
        st.write("**" + t("ship.cheapest") + ": " + results[0]["name"] + "** 🏆")
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("ship.col_carrier"), t("ship.col_shipping"),
                    t("ship.col_cod"), t("ship.col_total"), t("ship.col_days")]:
            table_html += "<th style='text-align:left;padding:5px 8px'>" + col + "</th>"
        table_html += "</tr>"
        for r in results:
            is_best = r["carrier"] == cheapest
            bg = " background:#1a2a1a" if is_best else ""
            table_html += "<tr style='border-top:1px solid #2a2a2a;" + bg + "'>"
            table_html += "<td style='padding:5px 8px'>" + r["icon"] + " " + r["name"] + \
                          (" ⭐" if is_best else "") + "</td>"
            table_html += "<td style='padding:5px 8px'>฿{:,.0f}".format(r["shipping"]) + "</td>"
            table_html += "<td style='padding:5px 8px'>฿{:,.0f}".format(r["cod_fee"]) + "</td>"
            total_color = "#4d6c5c" if is_best else "#d4d0c8"
            table_html += "<td style='padding:5px 8px;color:" + total_color + ";font-weight:bold'>฿{:,.0f}".format(r["total"]) + "</td>"
            table_html += "<td style='padding:5px 8px;color:#9a9485'>" + r["est_days"] + t("ship.days") + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)

with tab_margin:
    st.subheader(t("ship.margin_title"))
    col1, col2 = st.columns(2)
    sell_price = col1.number_input(t("ship.sell_price"), min_value=0.0,
                                    value=299.0, step=10.0)
    cost_price = col2.number_input(t("ship.cost_price"), min_value=0.0,
                                    value=120.0, step=10.0)
    col3, col4 = st.columns(2)
    weight_m   = col3.number_input(t("ship.weight"), min_value=0.1, value=0.5,
                                    step=0.1, format="%.1f")
    is_cod_m   = col4.checkbox(t("ship.is_cod"), key="cod_margin")

    if sell_price > 0:
        carrier_options = list(sc.CARRIERS.keys())
        sel_carrier = st.selectbox(
            t("ship.carrier"),
            carrier_options,
            format_func=lambda k: sc.CARRIERS[k]["icon"] + " " + carrier_name(k),
        )
        m = sc.margin_after_shipping(sell_price, cost_price, weight_m,
                                      sel_carrier, is_cod_m)
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric(t("ship.m_shipping"), "฿{:,.0f}".format(m["shipping"]))
        mc2.metric(t("ship.m_cod_fee"), "฿{:,.0f}".format(m["cod_fee"]))
        mc3.metric(t("ship.m_profit"), "฿{:,.0f}".format(m["profit"]),
                   delta_color="normal" if m["profit"] > 0 else "inverse")
        margin_color = "normal" if m["margin"] > 20 else "inverse"
        mc4.metric(t("ship.m_margin"), str(m["margin"]) + "%",
                   delta_color=margin_color)

        breakdown_html = (
            "<div style='font-size:0.85rem;color:#9a9485;margin-top:8px'>"
            + t("ship.sell_price") + ": ฿{:,.0f}".format(m["sell_price"])
            + " − " + t("ship.cost_price") + ": ฿{:,.0f}".format(m["cost_price"])
            + " − " + t("ship.m_shipping") + ": ฿{:,.0f}".format(m["shipping"])
            + " − " + t("ship.m_cod_fee") + ": ฿{:,.0f}".format(m["cod_fee"])
            + " = ฿{:,.0f}".format(m["profit"])
            + "</div>"
        )
        st.html(breakdown_html)

        st.divider()
        st.write("**" + t("ship.compare_all_carriers") + "**")
        for r in sc.compare_all(weight_m, sell_price, is_cod_m):
            m2 = sc.margin_after_shipping(sell_price, cost_price, weight_m,
                                           r["carrier"], is_cod_m)
            color = "#4d6c5c" if m2["margin"] > 20 else \
                    ("#c5963d" if m2["margin"] > 10 else "#c54c4c")
            row_html = (
                "<div style='margin:3px 0;font-size:0.84rem'>"
                "<span style='color:#9a9485;width:180px;display:inline-block'>"
                + r["icon"] + " " + r["name"] + "</span>"
                "<span style='color:" + color + "'>" +
                t("ship.carrier_margin_line",
                  margin=str(m2["margin"]),
                  profit="{:,.0f}".format(m2["profit"])) + "</span>"
                "</div>"
            )
            st.html(row_html)

with tab_rates:
    st.subheader(t("ship.rates_title"))
    for key, info in sc.CARRIERS.items():
        with st.expander(info["icon"] + " " + carrier_name(key) +
                          " · COD " + str(info["cod_pct"]) + "%"):
            col1, col2 = st.columns(2)
            col1.write(t("ship.est_days") + ": " + ship_est_days(info["est_key"]))
            col2.write(t("ship.cod_flat") + ": ฿" + str(info["cod_fee"]))
            rate_html = "<table style='font-size:0.82rem;border-collapse:collapse'>"
            rate_html += "<tr style='color:#9a9485'><th style='padding:2px 8px'>" + t("ship.weight") + "</th><th style='padding:2px 8px'>" + t("ship.rate_price") + "</th></tr>"
            for w, p in info["rates"]:
                rate_html += (
                    "<tr><td style='padding:2px 8px;color:#9a9485'>"
                    + t("ship.weight_lte", w=str(w)) + "</td>"
                )
                rate_html += "<td style='padding:2px 8px'>฿" + str(p) + "</td></tr>"
            rate_html += "</table>"
            st.html(rate_html)
