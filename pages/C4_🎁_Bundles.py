"""Product Bundles — package multiple SKUs, auto-stock from components."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import bundles as bn
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Bundles",
                   page_icon="🎁", layout="wide")
apply_theme()
require_auth()
db.init()
bn.init()
render_sidebar()

page_header(icon="🎁", title=t("bndl.title"), subtitle=t("bndl.caption"))

s = bn.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("🎁 " + t("bndl.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("✅ " + t("bndl.kpi_active"), str(s["active"]),
                     hint="", hint_tone="ok" if s["active"] > 0 else "info")
with k3:
    metric_with_hint("📦 " + t("bndl.kpi_stock"),
                     str(s["total_available_stock"]),
                     hint="", hint_tone="ok" if s["total_available_stock"] > 0 else "warn")

# ---- Create bundle ----------------------------------------------------------
st.divider()
with st.expander(t("bndl.create_title"), expanded=s["total"] == 0):
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, sell_price FROM products ORDER BY sku"
        ).fetchall()

    if not products:
        st.info(t("bndl.no_products"))
    else:
        bc1, bc2 = st.columns(2)
        with bc1:
            bname = st.text_input(t("bndl.f_name"), placeholder=t("bndl.name_ph"))
            bdesc = st.text_input(t("bndl.f_desc"), placeholder="")
        with bc2:
            bprice = st.number_input(t("bndl.f_price"), min_value=0.0,
                                     value=0.0, step=10.0)
            bnotes = st.text_input(t("bndl.f_notes"), placeholder="")

        st.markdown("#### " + t("bndl.items_title"))
        num_items = st.slider(t("bndl.f_num"), 2, 6, 2, key="_bndl_n")
        p_opts = [p["sku"] + " — " + (p["name"] or "")[:22]
                  for p in products]
        bundle_items = []
        for idx in range(num_items):
            bi1, bi2 = st.columns([4, 1])
            with bi1:
                pi = st.selectbox(
                    t("bndl.f_sku"), range(len(p_opts)),
                    format_func=lambda i: p_opts[i],
                    key="_bsku_" + str(idx),
                    label_visibility="collapsed",
                )
            with bi2:
                qty = st.number_input(t("bndl.f_qty"), min_value=1,
                                      value=1, step=1,
                                      key="_bqty_" + str(idx),
                                      label_visibility="collapsed")
            bundle_items.append({"sku": products[pi]["sku"], "qty": qty})

        component_value = sum(
            (products[bi["sku"] == p["sku"] and i or 0]["sell_price"] or 0) * bi["qty"]
            if False else  # skip, compute below
            0
            for bi in bundle_items
        )
        # Compute component value correctly
        sku_price = {p["sku"]: p["sell_price"] or 0 for p in products}
        component_value = sum(
            sku_price.get(bi["sku"], 0) * bi["qty"] for bi in bundle_items
        )
        savings = round(component_value - bprice, 2) if bprice > 0 else 0
        if bprice > 0:
            st.markdown(
                "<div style='text-align:right;font-size:12px;color:#9a9485'>"
                + t("bndl.regular_price", amount="{:,.0f}".format(component_value))
                + " · " + t("bndl.bundle_price", amount="{:,.0f}".format(bprice))
                + (" · <span style='color:#4d6c5c'>"
                   + t("bndl.savings",
                       amount="{:,.0f}".format(savings),
                       pct="{:.0f}".format(savings / component_value * 100))
                   + "</span>"
                   if component_value > 0 else "")
                + "</div>",
                unsafe_allow_html=True,
            )

        if st.button(t("bndl.create_btn"), type="primary", key="_bndl_c"):
            if bname.strip():
                bundle_id = bn.create(
                    name=bname.strip(),
                    description=bdesc.strip(),
                    bundle_price=bprice,
                    skus_qtys=bundle_items,
                    notes=bnotes.strip(),
                )
                toast(t("bndl.created"), icon="🎁")
                st.rerun()

# ---- Refresh all stocks -----------------------------------------------------
if st.button(t("bndl.refresh_btn"), type="tertiary", key="_bndl_refresh"):
    bn.refresh_all_stocks()
    toast(t("bndl.refreshed"), icon="✓")
    st.rerun()

# ---- Bundle list -----------------------------------------------------------
st.divider()
st.markdown("### " + t("bndl.list_title"))

all_bundles = bn.all_bundles()
if not all_bundles:
    st.info(t("bndl.empty"))
    st.stop()

for bundle in all_bundles:
    active_color = "#4d6c5c" if bundle["active"] else "#9a9485"
    details = bn.get(bundle["id"])
    savings_pct = details.get("savings_pct", 0) if details else 0

    st.markdown(
        "<div style='padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + active_color + ";"
        "border-radius:8px;background:white;margin-bottom:6px'>"
        "<div style='display:flex;justify-content:space-between;align-items:center'>"
        "<div>🎁 <strong>" + bundle["name"] + "</strong>"
        + (" · " + bundle["description"][:30] if bundle.get("description") else "") +
        "</div>"
        "<div style='display:flex;gap:12px;font-size:13px;align-items:center'>"
        "<span>" + t("bndl.stock_line") + " <strong>" + str(bundle["available_stock"]) + "</strong></span>"
        "<span style='font-weight:600;color:#4d6c5c'>"
        "฿{:,.0f}".format(bundle["bundle_price"]) + "</span>"
        + ("<span style='font-size:11px;color:#4d6c5c'>-" +
           str(savings_pct) + "%</span>" if savings_pct > 0 else "") +
        "<span style='font-size:11px;color:" + active_color + ";font-weight:600'>"
        + ("✅ " + t("common.active") if bundle["active"] else "⏸ " + t("common.inactive")) + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    if details:
        items_str = " + ".join(
            str(i["qty"]) + "× " + i["sku"]
            for i in details.get("items", [])
        )
        st.markdown(
            "<div style='font-size:11px;color:#9a9485;padding:2px 14px 8px'>"
            + items_str + "</div>",
            unsafe_allow_html=True,
        )

    la1, la2, la3 = st.columns(3)
    with la1:
        if not bundle["active"] and st.button(
            t("bndl.activate_btn"), key="_ba_" + str(bundle["id"]), type="tertiary"
        ):
            bn.activate(bundle["id"])
            st.rerun()
    with la2:
        if bundle["active"] and st.button(
            t("bndl.deactivate_btn"), key="_bd_" + str(bundle["id"]), type="tertiary"
        ):
            bn.deactivate(bundle["id"])
            st.rerun()
    with la3:
        if st.button(t("bndl.refresh_stock_btn"),
                     key="_br_" + str(bundle["id"]), type="tertiary"):
            bn.update_stock(bundle["id"])
            st.rerun()
