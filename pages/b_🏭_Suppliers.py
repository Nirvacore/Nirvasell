"""Supplier Management — know who gives you the best price.

Track multiple suppliers per SKU. Compare costs. Record purchase orders.
Spot when one supplier quietly raises prices while another stays cheap."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import supplier_mgmt as sm
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Suppliers",
                   page_icon="🏭", layout="wide")
apply_theme()
require_auth()
db.init()
sm.init()
render_sidebar()

page_header(icon="🏭", title=t("sup.title"), subtitle=t("sup.caption"))


# ---- KPI overview -----------------------------------------------------------

suppliers = sm.all_suppliers()
spend = sm.total_spend()

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("sup.kpi_count"), str(len(suppliers)),
        hint=t("sup.hint_add") if not suppliers else "",
        hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("sup.kpi_orders"), str(spend["total_orders"]),
        hint="", hint_tone="info",
    )
with k3:
    metric_with_hint(
        t("sup.kpi_spent"), "{:,.0f}".format(spend["total_spent"]),
        hint="", hint_tone="info",
    )


# ---- Add supplier -----------------------------------------------------------

st.divider()
with st.expander(t("sup.add_title"), expanded=not suppliers):
    with st.form("add_supplier"):
        c1, c2 = st.columns(2)
        with c1:
            n_name = st.text_input(t("sup.f_name") + " *", placeholder="Synnex, VSTECS, etc.")
            n_contact = st.text_input(t("sup.f_contact"), placeholder=t("sup.contact_placeholder"))
            n_phone = st.text_input(t("sup.f_phone"))
        with c2:
            n_email = st.text_input("Email")
            n_line = st.text_input("LINE ID")
            n_lead = st.number_input(
                t("sup.f_lead_days"), min_value=1, max_value=90, value=3,
            )
        n_terms = st.text_input(t("sup.f_terms"), placeholder="Net 30, COD, etc.")
        n_note = st.text_input(t("sup.f_note"))

        if st.form_submit_button(t("sup.add_btn"), type="primary"):
            if n_name.strip():
                sm.add_supplier(
                    name=n_name.strip(), contact=n_contact, phone=n_phone,
                    email=n_email, line_id=n_line, lead_days=n_lead,
                    payment_terms=n_terms, note=n_note,
                )
                toast(t("sup.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("sup.need_name"))


# ---- Supplier list ----------------------------------------------------------

if suppliers:
    st.divider()
    st.markdown("### " + t("sup.list_title"))

    for s in suppliers:
        cA, cB = st.columns([5, 2])
        with cA:
            sku_str = str(s.get("sku_count", 0))
            ord_str = str(s.get("order_count", 0))
            lead_str = str(s.get("lead_days", 3))

            st.markdown(
                "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
                "border-radius:10px;padding:14px 18px;margin-bottom:6px'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                "<div><span style='font-size:15px;font-weight:600'>"
                "🏭 " + s["name"] + "</span>"
                "<span style='color:#7a7569;font-size:12px;margin-left:8px'>" +
                (s.get("payment_terms") or "") + "</span></div>"
                "<div style='display:flex;gap:14px;font-size:12px;color:#7a7569'>"
                "<span>📦 " + sku_str + " SKUs</span>"
                "<span>📋 " + ord_str + " POs</span>"
                "<span>📅 " + lead_str + "d lead</span>"
                "</div></div>"
                "<div style='color:#9a9485;font-size:12px;margin-top:4px'>" +
                " · ".join(filter(None, [
                    s.get("contact"), s.get("phone"), s.get("email"),
                ])) +
                "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if st.button("💰", key="_sp_" + str(s["id"]),
                             type="tertiary", help=t("sup.add_price")):
                    st.session_state["_sup_price_id"] = s["id"]
                    st.rerun()
            with bc2:
                if st.button("📋", key="_so_" + str(s["id"]),
                             type="tertiary", help=t("sup.add_po")):
                    st.session_state["_sup_po_id"] = s["id"]
                    st.rerun()
            with bc3:
                if st.button("🗑", key="_sd_" + str(s["id"]),
                             type="tertiary", help=t("common.delete")):
                    sm.delete_supplier(s["id"])
                    toast(t("common.deleted"), icon="🗑")
                    st.rerun()


# ---- Price entry drawer -----------------------------------------------------

price_sup_id = st.session_state.get("_sup_price_id")
if price_sup_id:
    sup_info = sm.get_supplier(price_sup_id)
    if sup_info:
        st.divider()
        st.markdown("### 💰 " + t("sup.prices_for") + " " + sup_info["name"])

        # Show existing prices
        prices = sm.prices_for_supplier(price_sup_id)
        if prices:
            for p in prices:
                cP, cD = st.columns([5, 1])
                with cP:
                    st.markdown(
                        "<div style='display:flex;justify-content:space-between;"
                        "padding:6px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                        "<div>📦 " + p["sku"] +
                        " <span style='color:#7a7569;font-size:12px'>" +
                        (p.get("product_name") or "") + "</span></div>"
                        "<div style='font-weight:600;color:#4d6c5c'>฿" +
                        "{:,.0f}".format(p["unit_cost"]) +
                        " <span style='font-weight:400;color:#9a9485;font-size:11px'>"
                        "min " + str(p.get("min_qty", 1)) + "</span></div>"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                with cD:
                    if st.button("🗑", key="_dp_" + str(p["id"]), type="tertiary"):
                        sm.delete_price(p["id"])
                        st.rerun()

        # Add price form
        with st.form("add_price_" + str(price_sup_id)):
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                np_sku = st.text_input("SKU *")
                np_name = st.text_input(t("sup.f_product_name"))
            with pc2:
                np_cost = st.number_input(t("sup.f_unit_cost"), min_value=0.0, step=10.0, format="%.0f")
                np_min = st.number_input(t("sup.f_min_qty"), min_value=1, value=1)
            with pc3:
                np_note = st.text_input(t("sup.f_note"))

            if st.form_submit_button(t("sup.save_price"), type="primary"):
                if np_sku.strip() and np_cost > 0:
                    sm.set_price(
                        price_sup_id, np_sku.strip(), np_cost,
                        product_name=np_name, min_qty=np_min, note=np_note,
                    )
                    toast(t("common.saved"), icon="✓")
                    st.rerun()

        if st.button(t("common.close"), key="_close_price"):
            st.session_state.pop("_sup_price_id", None)
            st.rerun()


# ---- Purchase order drawer --------------------------------------------------

po_sup_id = st.session_state.get("_sup_po_id")
if po_sup_id:
    sup_info = sm.get_supplier(po_sup_id)
    if sup_info:
        st.divider()
        st.markdown("### 📋 " + t("sup.po_for") + " " + sup_info["name"])

        # PO history
        pos = sm.supplier_order_history(po_sup_id)
        if pos:
            for po in pos:
                st.markdown(
                    "<div style='display:flex;justify-content:space-between;"
                    "padding:6px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                    "<div>📋 " + (po.get("order_date") or "—") +
                    " · " + t("common.n_items", n=str(po.get("items_count", 0))) +
                    " <span style='color:#9a9485;font-size:11px'>" +
                    (po.get("note") or "") + "</span></div>"
                    "<div style='font-weight:600'>฿" +
                    "{:,.0f}".format(po.get("total_amount", 0)) + "</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )

        # Add PO form
        with st.form("add_po_" + str(po_sup_id)):
            poc1, poc2 = st.columns(2)
            with poc1:
                po_amount = st.number_input(
                    t("sup.f_po_amount"), min_value=0.0, step=100.0, format="%.0f",
                )
                po_items = st.number_input(
                    t("sup.f_po_items"), min_value=0, value=1,
                )
            with poc2:
                po_note = st.text_input(t("sup.f_note"))

            if st.form_submit_button(t("sup.save_po"), type="primary"):
                sm.add_order(po_sup_id, po_amount, po_items, po_note)
                toast(t("common.saved"), icon="✓")
                st.rerun()

        if st.button(t("common.close"), key="_close_po"):
            st.session_state.pop("_sup_po_id", None)
            st.rerun()


# ---- Price comparison (multi-supplier SKUs) ---------------------------------

st.divider()
st.markdown("### " + t("sup.compare_title"))
st.caption(t("sup.compare_help"))

comparisons = sm.price_comparison()
if comparisons:
    for c in comparisons:
        spread = c["max_cost"] - c["min_cost"]
        save_pct = round(spread / c["max_cost"] * 100, 0) if c["max_cost"] else 0
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div><strong>" + c["sku"] + "</strong>"
            " <span style='color:#7a7569;font-size:12px'>" +
            str(c["suppliers"]) + " " + t("sup.suppliers") + "</span></div>"
            "<div style='display:flex;gap:18px;align-items:center;font-size:13px'>"
            "<span style='color:#4d6c5c'>฿" + "{:,.0f}".format(c["min_cost"]) + "</span>"
            "<span style='color:#9a9485'>~</span>"
            "<span style='color:#c54c4c'>฿" + "{:,.0f}".format(c["max_cost"]) + "</span>"
            "<span style='background:rgba(77,108,92,0.1);padding:2px 8px;"
            "border-radius:6px;font-size:11px;color:#4d6c5c'>" +
            t("sup.save") + " " + str(int(save_pct)) + "%</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )
else:
    st.caption(t("sup.no_compare"))
