"""Global Search — find anything across products, orders, customers.

One search box for your entire shop."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import global_search as gs
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Search",
                   page_icon="🔎", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🔎", title=t("srch.title"), subtitle=t("srch.caption"))

qs = gs.quick_stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("📦 " + t("srch.kpi_products"), str(qs["products"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🧾 " + t("srch.kpi_orders"), str(qs["orders"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("👥 " + t("srch.kpi_customers"), str(qs["customers"]),
                     hint="", hint_tone="info")

st.divider()

query = st.text_input(
    t("srch.input_label"),
    placeholder=t("srch.input_ph"),
    key="_search_q",
)

if query and len(query.strip()) >= 2:
    results = gs.search(query.strip())

    total = (len(results["products"]) + len(results["orders"]) +
             len(results["customers"]))

    if total == 0:
        st.info(t("srch.no_results"))
        st.stop()

    st.caption(t("srch.found", fmt={"count": str(total), "query": query}))

    # ---- Products ----
    prods = results["products"]
    if prods:
        st.markdown("### 📦 " + t("srch.products_title") +
                     " (" + str(len(prods)) + ")")
        for p in prods:
            margin = ""
            if p.get("sell_price") and p.get("cost_price"):
                m = p["sell_price"] - p["cost_price"]
                margin = " · กำไร ฿" + "{:,.0f}".format(m)

            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "align-items:center;padding:8px 14px;"
                "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div>"
                "<strong>" + (p.get("sku") or "") + "</strong>"
                " · " + (p.get("name") or "")[:40] +
                " <span style='color:#9a9485;font-size:11px'>"
                + (p.get("brand") or "") + " / " + (p.get("category") or "") + "</span>"
                "</div>"
                "<div style='display:flex;gap:12px;font-size:13px'>"
                "<span>฿" + "{:,.0f}".format(p.get("sell_price") or 0) + "</span>"
                "<span style='color:#9a9485'>สต็อก " + str(p.get("stock") or 0) + "</span>"
                + ("<span style='color:#4d6c5c'>" + margin + "</span>" if margin else "") +
                "</div></div>",
                unsafe_allow_html=True,
            )

    # ---- Orders ----
    ords = results["orders"]
    if ords:
        st.markdown("### 🧾 " + t("srch.orders_title") +
                     " (" + str(len(ords)) + ")")
        for o in ords:
            s_icon = {"paid": "✅", "shipped": "🚚", "delivered": "📬",
                      "cancelled": "❌", "returned": "↩"}.get(
                          o.get("status") or "", "📦")
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "align-items:center;padding:8px 14px;"
                "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div>"
                + s_icon + " <strong>" + (o.get("order_id") or "") + "</strong>"
                " · " + (o.get("sku") or "") +
                " <span style='color:#9a9485;font-size:11px'>"
                + (o.get("platform") or "") + "</span>"
                "</div>"
                "<div style='display:flex;gap:12px;font-size:13px'>"
                "<span>฿" + "{:,.0f}".format(o.get("total_amount") or 0) + "</span>"
                "<span style='color:#9a9485'>" +
                (o.get("buyer_name") or "") + "</span>"
                "<span style='font-size:11px;color:#7a7569'>" +
                ((o.get("order_date") or "")[:10]) + "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )

    # ---- Customers ----
    custs = results["customers"]
    if custs:
        st.markdown("### 👥 " + t("srch.customers_title") +
                     " (" + str(len(custs)) + ")")
        for c_item in custs:
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "align-items:center;padding:8px 14px;"
                "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div>"
                "👤 <strong>" + (c_item.get("buyer_name") or c_item.get("customer_key") or "") + "</strong>"
                " <span style='color:#9a9485;font-size:11px'>"
                + (c_item.get("buyer_phone") or "") + "</span>"
                "</div>"
                "<div style='display:flex;gap:12px;font-size:13px'>"
                "<span>" + str(c_item.get("order_count") or 0) + "x</span>"
                "<span style='color:#4d6c5c'>฿" +
                "{:,.0f}".format(c_item.get("total_spent") or 0) + "</span>"
                "<span style='font-size:11px;color:#7a7569'>" +
                ((c_item.get("last_order") or "")[:10]) + "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )
else:
    if query:
        st.caption(t("srch.min_chars"))
