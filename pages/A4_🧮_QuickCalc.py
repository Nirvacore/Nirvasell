"""Quick Calculator — margin, shipping, break-even, ROI, discount impact.

Business calculators every Thai reseller needs, all in one place."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import quick_calc as qc
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header
from i18n import t
from i18n_inline import carrier_name

st.set_page_config(page_title="nirva.sell · Calculator",
                   page_icon="🧮", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🧮", title=t("calc.title"), subtitle=t("calc.caption"))

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 " + t("calc.tab_margin"),
    "🚚 " + t("calc.tab_shipping"),
    "📊 " + t("calc.tab_breakeven"),
    "📈 " + t("calc.tab_roi"),
    "🏷 " + t("calc.tab_discount"),
])


# ---- Margin Calculator ------------------------------------------------------

with tab1:
    st.markdown("### " + t("calc.margin_title"))

    mc1, mc2 = st.columns(2)
    with mc1:
        cost = st.number_input(t("calc.f_cost"), min_value=0.0, value=100.0,
                               step=10.0, key="_mc_cost")
        sell = st.number_input(t("calc.f_sell"), min_value=0.0, value=250.0,
                               step=10.0, key="_mc_sell")
        platform_fee = st.number_input(t("calc.f_platform_fee"),
                                       min_value=0.0, max_value=50.0,
                                       value=6.0, step=0.5, key="_mc_fee")
    with mc2:
        shipping = st.number_input(t("calc.f_shipping"), min_value=0.0,
                                   value=0.0, step=5.0, key="_mc_ship")
        packaging = st.number_input(t("calc.f_packaging"), min_value=0.0,
                                    value=5.0, step=1.0, key="_mc_pack")

    if st.button(t("calc.calc_btn"), key="_mc_go", type="primary"):
        r = qc.margin_calc(cost, sell, platform_fee, shipping, packaging)
        color = "#4d6c5c" if r["profitable"] else "#c54c4c"

        st.markdown(
            "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-left:4px solid " + color + ";border-radius:10px;"
            "padding:16px;margin-top:10px'>"
            "<div style='display:flex;justify-content:space-around;text-align:center'>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_profit") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600;color:" + color + "'>"
            "฿" + "{:,.2f}".format(r["profit"]) + "</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_margin") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600'>"
            + str(r["margin_pct"]) + "%</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_markup") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600'>"
            + str(r["markup_pct"]) + "%</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_fee") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600'>฿"
            + "{:,.2f}".format(r["platform_fee"]) + "</div></div>"
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("#### " + t("calc.reverse_title"))
    rc1, rc2 = st.columns(2)
    with rc1:
        target_margin = st.number_input(t("calc.f_target_margin"),
                                        min_value=1.0, max_value=90.0,
                                        value=30.0, step=5.0, key="_mc_tm")
    if st.button(t("calc.reverse_btn"), key="_mc_rev", type="tertiary"):
        r2 = qc.price_from_margin(cost, target_margin, platform_fee,
                                   shipping, packaging)
        if r2.get("error"):
            st.error(r2["msg"])
        else:
            st.success(t("calc.reverse_result", fmt={
                "price": "{:,.0f}".format(r2["suggested_price"]),
                "profit": "{:,.2f}".format(r2["profit_per_unit"]),
            }))


# ---- Shipping Calculator ----------------------------------------------------

with tab2:
    st.markdown("### " + t("calc.shipping_title"))

    weight = st.number_input(t("calc.f_weight"), min_value=0.1,
                             value=1.0, step=0.5, key="_sc_wt")

    rates = qc.shipping_calc(weight)
    for r in rates:
        carrier_label = carrier_name(r["carrier"])
        is_cheapest = r == rates[0]
        border_color = "#4d6c5c" if is_cheapest else "rgba(40,30,20,0.07)"
        badge = " 🏆 " + t("calc.cheapest") if is_cheapest else ""

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border:0.5px solid " + border_color + ";"
            "border-left:3px solid " + border_color + ";border-radius:8px;"
            "margin-bottom:4px;background:white'>"
            "<span><strong>" + carrier_label + "</strong>" + badge + "</span>"
            "<span style='font-size:1.2rem;font-weight:600'>฿"
            + "{:,.0f}".format(r["cost"]) + "</span></div>",
            unsafe_allow_html=True,
        )


# ---- Break-Even Calculator --------------------------------------------------

with tab3:
    st.markdown("### " + t("calc.be_title"))

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        fixed_costs = st.number_input(t("calc.f_fixed_costs"),
                                      min_value=0.0, value=5000.0,
                                      step=500.0, key="_be_fixed")
    with bc2:
        be_price = st.number_input(t("calc.f_be_price"),
                                   min_value=0.0, value=350.0,
                                   step=10.0, key="_be_price")
    with bc3:
        be_var = st.number_input(t("calc.f_variable_cost"),
                                 min_value=0.0, value=150.0,
                                 step=10.0, key="_be_var")

    if st.button(t("calc.calc_btn"), key="_be_go", type="primary"):
        be = qc.break_even(fixed_costs, be_price, be_var)
        if not be["achievable"]:
            st.error("❌ " + be["msg"])
        else:
            st.markdown(
                "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
                "border-radius:10px;padding:16px;margin-top:10px'>"
                "<div style='display:flex;justify-content:space-around;text-align:center'>"
                "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.be_units") + "</div>"
                "<div style='font-size:1.6rem;font-weight:600;color:#4d6c5c'>"
                + "{:,.0f}".format(be["break_even_units"]) + " " + t("calc.units") + "</div></div>"
                "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.be_revenue") + "</div>"
                "<div style='font-size:1.6rem;font-weight:600'>฿"
                + "{:,.0f}".format(be["break_even_revenue"]) + "</div></div>"
                "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.be_contrib") + "</div>"
                "<div style='font-size:1.6rem;font-weight:600'>฿"
                + "{:,.2f}".format(be["contribution_margin"]) +
                " (" + str(be["contribution_pct"]) + "%)</div></div>"
                "</div></div>",
                unsafe_allow_html=True,
            )


# ---- ROI Calculator ---------------------------------------------------------

with tab4:
    st.markdown("### " + t("calc.roi_title"))

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        investment = st.number_input(t("calc.f_investment"),
                                     min_value=0.0, value=10000.0,
                                     step=1000.0, key="_roi_inv")
    with rc2:
        revenue = st.number_input(t("calc.f_revenue"),
                                  min_value=0.0, value=15000.0,
                                  step=1000.0, key="_roi_rev")
    with rc3:
        period = st.number_input(t("calc.f_period_months"),
                                 min_value=1, value=1, step=1, key="_roi_per")

    if st.button(t("calc.calc_btn"), key="_roi_go", type="primary"):
        roi = qc.roi_calc(investment, revenue, period)
        color = "#4d6c5c" if roi["profitable"] else "#c54c4c"
        payback_str = str(roi["payback_months"]) + " " + t("calc.months") if roi["payback_months"] else "—"

        st.markdown(
            "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-left:4px solid " + color + ";border-radius:10px;"
            "padding:16px;margin-top:10px'>"
            "<div style='display:flex;justify-content:space-around;text-align:center'>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_roi") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600;color:" + color + "'>"
            + str(roi["roi_pct"]) + "%</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_annual") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600'>"
            + str(roi["annual_roi"]) + "%</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_payback") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600'>"
            + payback_str + "</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.r_profit") + "</div>"
            "<div style='font-size:1.4rem;font-weight:600;color:" + color + "'>฿"
            + "{:,.0f}".format(roi["profit"]) + "</div></div>"
            "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Discount Impact -------------------------------------------------------

with tab5:
    st.markdown("### " + t("calc.disc_title"))

    dc1, dc2 = st.columns(2)
    with dc1:
        disc_price = st.number_input(t("calc.f_original_price"),
                                     min_value=0.0, value=500.0,
                                     step=10.0, key="_dc_price")
        disc_pct = st.number_input(t("calc.f_discount_pct"),
                                   min_value=1.0, max_value=90.0,
                                   value=15.0, step=5.0, key="_dc_pct")
    with dc2:
        disc_cost = st.number_input(t("calc.f_cost"), min_value=0.0,
                                    value=200.0, step=10.0, key="_dc_cost")
        disc_qty = st.number_input(t("calc.f_current_qty"),
                                   min_value=1, value=100,
                                   step=10, key="_dc_qty")

    if st.button(t("calc.calc_btn"), key="_dc_go", type="primary"):
        di = qc.discount_impact(disc_price, disc_pct, disc_cost, disc_qty)

        st.markdown(
            "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-radius:10px;padding:16px;margin-top:10px'>"
            "<div style='text-align:center;margin-bottom:10px'>"
            "<span style='font-size:1.3rem;text-decoration:line-through;color:#9a9485'>"
            "฿" + "{:,.0f}".format(di["original_price"]) + "</span>"
            " → <span style='font-size:1.5rem;font-weight:600;color:#c54c4c'>฿"
            + "{:,.0f}".format(di["discount_price"]) + "</span>"
            " <span style='color:#c54c4c'>(-" + str(di["discount_pct"]) + "%)</span></div>"
            "<div style='display:flex;justify-content:space-around;text-align:center'>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.profit_before") + "</div>"
            "<div style='font-size:1.1rem;font-weight:600'>฿"
            + "{:,.2f}".format(di["profit_per_unit_before"]) + "</div></div>"
            "<div><div style='font-size:12px;color:#7a7569'>" + t("calc.profit_after") + "</div>"
            "<div style='font-size:1.1rem;font-weight:600;color:#c54c4c'>฿"
            + "{:,.2f}".format(di["profit_per_unit_after"]) + "</div></div>"
            + ("<div><div style='font-size:12px;color:#7a7569'>" + t("calc.units_to_match") + "</div>"
               "<div style='font-size:1.1rem;font-weight:600'>"
               + str(di["units_needed_to_match"]) + " " + t("calc.units") + "</div></div>"
               if di["units_needed_to_match"] else "") +
            "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### " + t("calc.scenarios"))
        for sc in di["scenarios"]:
            sc_color = "#4d6c5c" if sc["better"] else "#c54c4c"
            sc_icon = "✅" if sc["better"] else "🔴"
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<span>" + sc_icon + " " + t("calc.scenario_sell_qty", n=str(sc["qty"])) + "</span>"
                "<span>" + t("calc.scenario_total_profit", amount="{:,.0f}".format(sc["total_profit"])) + "</span>"
                "<span style='color:" + sc_color + ";font-weight:600'>"
                + ("+" if sc["vs_original"] > 0 else "") +
                "{:,.0f}".format(sc["vs_original"]) + "</span></div>",
                unsafe_allow_html=True,
            )
