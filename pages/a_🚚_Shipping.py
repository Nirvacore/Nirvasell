"""Shipping Calculator — compare Thai carriers in seconds.

Kerry, Flash, J&T, Thailand Post, Best, NinjaVan — different rates,
different COD fees, different speeds. This page shows them all side-by-side
so sellers pick the cheapest option per shipment."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import shipping_calc as sc
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header
from i18n import t

st.set_page_config(page_title="nirva.sell · Shipping",
                   page_icon="🚚", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🚚", title=t("ship.title"), subtitle=t("ship.caption"))


# ---- Quick compare ----------------------------------------------------------

st.markdown("### " + t("ship.compare_title"))

c1, c2, c3 = st.columns(3)
with c1:
    weight = st.number_input(
        t("ship.weight_kg"), min_value=0.1, max_value=30.0,
        value=1.0, step=0.5, format="%.1f",
    )
with c2:
    order_amount = st.number_input(
        t("ship.order_amount"), min_value=0.0,
        value=500.0, step=50.0, format="%.0f",
    )
with c3:
    is_cod = st.checkbox(t("ship.is_cod"), value=False)

results = sc.compare_all(weight, order_amount, is_cod)

# Highlight cheapest
cheapest_total = results[0]["total"] if results else 0

for i, r in enumerate(results):
    is_best = (i == 0)
    bg = "rgba(77,108,92,0.06)" if is_best else "transparent"
    border = "2px solid rgba(77,108,92,0.3)" if is_best else "0.5px solid rgba(40,30,20,0.05)"
    badge = ""
    if is_best:
        badge = (" <span style='background:#4d6c5c;color:white;font-size:10px;"
                 "padding:2px 8px;border-radius:8px;margin-left:6px'>"
                 + t("ship.cheapest") + "</span>")

    ship_str = "{:,.0f}".format(r["shipping"])
    cod_str = ""
    if is_cod and r["cod_fee"] > 0:
        cod_str = " + COD ฿" + "{:,.0f}".format(r["cod_fee"])
    total_str = "{:,.0f}".format(r["total"])

    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:12px 18px;border:" + border + ";border-radius:10px;"
        "background:" + bg + ";margin-bottom:6px'>"
        "<div>"
        "<span style='font-size:15px;font-weight:600'>" +
        r["icon"] + " " + r["name"] + "</span>" + badge +
        "<div style='color:#7a7569;font-size:12px;margin-top:2px'>"
        "📅 " + r["est_days"] + " " + t("dashboard.days") + "</div>"
        "</div>"
        "<div style='text-align:right'>"
        "<div style='font-size:1.2rem;font-weight:600;color:#4d6c5c;"
        "font-variant-numeric:tabular-nums'>฿" + total_str + "</div>"
        "<div style='color:#9a9485;font-size:11px'>" +
        t("ship.shipping") + " ฿" + ship_str + cod_str + "</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )


# ---- Margin after shipping --------------------------------------------------

st.divider()
st.markdown("### " + t("ship.margin_title"))
st.caption(t("ship.margin_help"))

mc1, mc2 = st.columns(2)
with mc1:
    sell_price = st.number_input(
        t("ship.sell_price"), min_value=0.0, value=599.0, step=10.0, format="%.0f",
    )
    cost_price = st.number_input(
        t("ship.cost_price"), min_value=0.0, value=350.0, step=10.0, format="%.0f",
    )

with mc2:
    m_weight = st.number_input(
        t("ship.weight_kg"), min_value=0.1, max_value=30.0,
        value=weight, step=0.5, format="%.1f", key="_m_weight",
    )
    m_cod = st.checkbox(t("ship.is_cod"), value=is_cod, key="_m_cod")

st.markdown("---")

for key, info in sc.CARRIERS.items():
    m = sc.margin_after_shipping(sell_price, cost_price, m_weight, key, m_cod)
    margin_color = "#4d6c5c" if m["margin"] > 15 else ("#c5963d" if m["margin"] > 5 else "#c54c4c")
    margin_icon = "✅" if m["margin"] > 15 else ("⚠️" if m["margin"] > 5 else "❌")

    ship_detail = t("ship.shipping") + " ฿" + "{:,.0f}".format(m["shipping"])
    if m_cod and m["cod_fee"] > 0:
        ship_detail = ship_detail + " + COD ฿" + "{:,.0f}".format(m["cod_fee"])

    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<div>" + info["icon"] + " " + info["name"] +
        " <span style='color:#9a9485;font-size:11px'>" + ship_detail + "</span></div>"
        "<div style='display:flex;gap:18px;align-items:center'>"
        "<span style='font-variant-numeric:tabular-nums'>" +
        t("ship.profit") + " ฿" + "{:,.0f}".format(m["profit"]) + "</span>"
        "<span style='color:" + margin_color + ";font-weight:600'>" +
        margin_icon + " " + "{:.1f}%".format(m["margin"]) + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )


# ---- Rate reference table ---------------------------------------------------

st.divider()
with st.expander(t("ship.rate_table"), expanded=False):
    import pandas as pd
    weight_tiers = [0.5, 1, 2, 3, 5, 10, 15, 20]
    data = {}
    for key, info in sc.CARRIERS.items():
        data[info["name"]] = [sc.shipping_cost(key, w) for w in weight_tiers]
    df = pd.DataFrame(data, index=[str(w) + " kg" for w in weight_tiers])
    st.dataframe(df, width="stretch")
