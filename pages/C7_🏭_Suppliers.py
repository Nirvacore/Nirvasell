"""Supplier Directory — manage contacts, terms, linked SKUs."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import supplier_directory as sd
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
sd.init()
render_sidebar()

page_header(icon="🏭", title=t("sup.title"), subtitle=t("sup.caption"))

s = sd.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("🏭 " + t("sup.kpi_total"), str(s["active"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("📦 " + t("sup.kpi_skus"), str(s["linked_skus"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("📋 " + t("sup.kpi_all"), str(s["total"]),
                     hint="", hint_tone="info")

# ---- Add supplier -----------------------------------------------------------
st.divider()
with st.expander(t("sup.add_title"), expanded=s["total"] == 0):
    with st.form("add_supplier"):
        sc1, sc2 = st.columns(2)
        with sc1:
            sup_name = st.text_input(t("sup.f_name"), placeholder=t("sup.name_ph"))
            contact = st.text_input(t("sup.f_contact"), placeholder=t("sup.contact_ph"))
            phone = st.text_input(t("sup.f_phone"), placeholder=t("sup.phone_ph"))
            line_id = st.text_input(t("sup.f_line"), placeholder=t("sup.line_id_ph"))
        with sc2:
            email = st.text_input(t("sup.f_email"), placeholder=t("sup.email_ph"))
            category = st.selectbox(t("sup.f_category"), sd.CATEGORIES)
            payment_terms = st.selectbox(
                t("sup.f_terms"),
                list(sd.PAYMENT_TERMS.keys()),
                format_func=lambda k: sd.PAYMENT_TERMS[k],
            )
            min_order = st.number_input(t("sup.f_min_order"),
                                         min_value=0.0, value=0.0, step=100.0)
        sup_notes = st.text_area(t("sup.f_notes"), placeholder="", height=60)
        if st.form_submit_button(t("sup.add_btn"), type="primary"):
            if sup_name.strip():
                sd.add(
                    name=sup_name.strip(),
                    contact_name=contact.strip(),
                    phone=phone.strip(),
                    email=email.strip(),
                    line_id=line_id.strip(),
                    category=category,
                    payment_terms=payment_terms,
                    min_order_amount=min_order,
                    notes=sup_notes.strip(),
                )
                toast(t("sup.added"), icon="✓")
                st.rerun()

# ---- Supplier list ----------------------------------------------------------
st.divider()
st.markdown("### " + t("sup.list_title"))

suppliers = sd.all_suppliers(active_only=False)
if not suppliers:
    st.info(t("sup.empty"))
    st.stop()

for sup in suppliers:
    active_color = "#4d6c5c" if sup["active"] else "#9a9485"
    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + active_color + ";"
        "border-radius:8px;background:white;margin-bottom:6px'>"
        "<div><strong>" + sup["name"] + "</strong>"
        + (" · " + (sup.get("contact_name") or "")
           if sup.get("contact_name") else "") +
        "<span style='font-size:11px;color:#9a9485;margin-left:6px'>"
        + sup.get("terms_label", "") + "</span></div>"
        "<div style='display:flex;gap:12px;font-size:12px'>"
        "<span>" + (sup.get("phone") or "") + "</span>"
        "<span style='color:#9a9485'>" + t("common.n_skus", n=str(sup.get("sku_count", 0))) + "</span>"
        "<span style='color:#9a9485'>" + t("common.n_pos", n=str(sup.get("po_count", 0))) + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    with st.expander(t("sup.detail_title") + " — " + sup["name"]):
        details = sd.get(sup["id"])
        if details:
            di1, di2, di3 = st.columns(3)
            with di1:
                st.markdown("📞 " + (details.get("phone") or "—"))
                st.markdown(t("sup.line_display") + " " + (details.get("line_id") or "—"))
            with di2:
                st.markdown("📧 " + (details.get("email") or "—"))
                st.markdown("💳 " + details["terms_label"])
            with di3:
                st.markdown(t("sup.min_order_line", amount="{:,.0f}".format(
                    details.get("min_order_amount") or 0
                )))
                st.markdown(t("sup.total_spent_line", amount="{:,.0f}".format(
                    details.get("total_spent") or 0
                )))

            # Link SKU
            st.markdown("#### " + t("sup.link_sku_title"))
            with db.conn() as c:
                products = c.execute(
                    "SELECT sku, name FROM products ORDER BY sku"
                ).fetchall()
            if products:
                with st.form("link_sku_" + str(sup["id"])):
                    lc1, lc2, lc3 = st.columns(3)
                    with lc1:
                        p_opts = [p["sku"] + " — " + (p["name"] or "")[:20]
                                  for p in products]
                        pi = st.selectbox(t("sup.f_sku"), range(len(p_opts)),
                                          format_func=lambda i: p_opts[i],
                                          key="_ls_p_" + str(sup["id"]))
                    with lc2:
                        lk_cost = st.number_input(t("sup.f_cost"),
                                                   min_value=0.0, value=0.0,
                                                   step=10.0)
                    with lc3:
                        lk_lead = st.number_input(t("sup.f_lead"),
                                                   min_value=1, value=7)
                    if st.form_submit_button(t("sup.link_btn"), type="primary"):
                        sd.link_sku(sup["id"], products[pi]["sku"],
                                    cost_price=lk_cost, lead_days=lk_lead)
                        toast(t("sup.linked"), icon="✓")
                        st.rerun()

            if details.get("skus"):
                st.markdown("**" + t("sup.linked_skus_title") + ":**")
                for sku_r in details["skus"]:
                    st.markdown(
                        "<div style='font-size:12px;padding:2px 0'>"
                        "📦 <strong>" + sku_r["sku"] + "</strong>"
                        + (" · " + (sku_r.get("product_name") or "")[:20]
                           if sku_r.get("product_name") else "") +
                        " · ฿{:,.0f}".format(sku_r.get("cost_price") or 0) +
                        t("common.per_piece") +
                        " · " + t("sup.lead_days_short", n=str(sku_r.get("lead_days", 7))) +
                        "</div>",
                        unsafe_allow_html=True,
                    )
