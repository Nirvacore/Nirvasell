"""Wholesale Pricing — tiered pricing for bulk buyers."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import wholesale_pricing as wp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Wholesale",
                   page_icon="🏷", layout="wide")
apply_theme()
require_auth()
db.init()
wp.init()
render_sidebar()

page_header(icon="🏷", title=t("ws.title"), subtitle=t("ws.caption"))

s = wp.stats()
k1, k2 = st.columns(2)
with k1:
    metric_with_hint("📦 " + t("ws.kpi_skus"), str(s["skus_with_wholesale"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🏷 " + t("ws.kpi_tiers"), str(s["total_tiers"]),
                     hint="", hint_tone="info")

# ---- Set tiers for a SKU ----------------------------------------------------
st.divider()
with st.expander(t("ws.set_title"), expanded=s["skus_with_wholesale"] == 0):
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, sell_price, cost_price FROM products ORDER BY sku"
        ).fetchall()

    if not products:
        st.info(t("ws.no_products"))
    else:
        prod_opts = [
            p["sku"] + " — " + (p["name"] or "")[:25] +
            " (ขาย ฿" + "{:,.0f}".format(p["sell_price"] or 0) + ")"
            for p in products
        ]
        sel_idx = st.selectbox(
            t("ws.f_sku"), range(len(prod_opts)),
            format_func=lambda i: prod_opts[i], key="_ws_sku",
        )
        sel_prod = products[sel_idx]
        retail_price = sel_prod["sell_price"] or 0
        cost_price = sel_prod["cost_price"] or 0

        st.caption(t("ws.tier_help"))
        tier_rows = []
        for i, default in enumerate(wp.DEFAULT_TIERS):
            tc1, tc2, tc3, tc4 = st.columns(4)
            with tc1:
                min_qty = st.number_input(
                    t("ws.f_min_qty"), min_value=1,
                    value=default["min_qty"], step=1,
                    key="_wt_mq_" + str(i),
                )
            with tc2:
                label = st.text_input(
                    t("ws.f_label"),
                    value=default["label"],
                    key="_wt_lb_" + str(i),
                )
            with tc3:
                disc = st.number_input(
                    t("ws.f_discount"),
                    min_value=0.0, max_value=80.0,
                    value=float(default["discount_pct"]),
                    step=5.0, key="_wt_dc_" + str(i),
                )
            with tc4:
                price = round(retail_price * (1 - disc / 100), 0)
                margin = round((price - cost_price) / price * 100, 1) if price > 0 else 0
                st.markdown(
                    "<div style='padding-top:24px;font-size:12px'>"
                    "฿{:,.0f}".format(price) +
                    " <span style='color:" +
                    ("#4d6c5c" if margin > 15 else "#c54c4c") + "'>"
                    + str(margin) + "% margin</span></div>",
                    unsafe_allow_html=True,
                )
            tier_rows.append({
                "min_qty": min_qty,
                "label": label.strip(),
                "discount_pct": disc,
                "price": round(retail_price * (1 - disc / 100), 0),
            })

        if st.button(t("ws.save_btn"), type="primary", key="_ws_save"):
            wp.set_tiers(sel_prod["sku"], tier_rows)
            toast(t("ws.saved"), icon="✓")
            st.rerun()

# ---- Quick Quote ------------------------------------------------------------
st.divider()
st.markdown("### 💬 " + t("ws.quote_title"))

with st.form("quick_quote"):
    qc1, qc2 = st.columns(2)
    with qc1:
        if products:
            qprod_opts = [p["sku"] + " — " + (p["name"] or "")[:25]
                          for p in products]
            qi = st.selectbox(t("ws.f_sku"), range(len(qprod_opts)),
                              format_func=lambda i: qprod_opts[i],
                              key="_qq_sku")
            q_sku = products[qi]["sku"]
        else:
            q_sku = ""
    with qc2:
        q_qty = st.number_input(t("ws.f_qty"), min_value=1, value=20,
                                step=10, key="_qq_qty")

    if st.form_submit_button(t("ws.quote_btn"), type="primary"):
        result = wp.price_for_qty(q_sku, q_qty)
        if result.get("price"):
            st.success(
                "💬 " + str(q_qty) + "x " + q_sku +
                " → **฿{:,.0f}**".format(result["price"]) + "/ชิ้น" +
                " = ฿{:,.0f}".format(result["total"]) +
                " (" + result.get("tier_label", "") + ")"
            )
        else:
            st.info(t("ws.no_tiers_set"))

# ---- All SKUs with wholesale ------------------------------------------------
st.divider()
st.markdown("### " + t("ws.skus_title"))

skus = wp.skus_with_tiers()
if not skus:
    st.info(t("ws.empty"))
    st.stop()

for grp in skus:
    tiers = wp.get_tiers(grp["parent_sku"] if "parent_sku" in grp else grp["sku"])
    with st.expander(
        "📦 " + grp["sku"] + " — " + (grp.get("name") or "")[:25] +
        " (" + str(grp["tier_count"]) + " tiers)"
    ):
        hc = st.columns(len(tiers))
        for i, tier in enumerate(tiers):
            with hc[i]:
                price_str = "฿{:,.0f}".format(tier["price"]) if tier["price"] else "—"
                m_color = "#4d6c5c" if (tier.get("margin_pct") or 0) >= 15 else "#c54c4c"
                st.markdown(
                    "<div style='text-align:center;padding:8px;"
                    "border:0.5px solid rgba(40,30,20,0.08);border-radius:8px'>"
                    "<div style='font-size:11px;color:#7a7569'>"
                    + str(tier["min_qty"]) + "+ ชิ้น</div>"
                    "<div style='font-weight:600'>" + tier["label"] + "</div>"
                    "<div style='font-size:1.1rem;font-weight:600'>"
                    + price_str + "</div>"
                    "<div style='font-size:11px;color:#9a9485'>"
                    "-" + str(tier["discount_pct"]) + "% ลด</div>"
                    + ("<div style='font-size:11px;color:" + m_color + "'>"
                       + str(tier.get("margin_pct") or 0) + "% margin</div>"
                       if tier.get("margin_pct") is not None else "") +
                    "</div>",
                    unsafe_allow_html=True,
                )
