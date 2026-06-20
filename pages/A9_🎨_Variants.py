"""Product Variants — manage color/size combos with individual stock."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import product_variants as pv
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Variants",
                   page_icon="🎨", layout="wide")
apply_theme()
require_auth()
db.init()
pv.init()
render_sidebar()

page_header(icon="🎨", title=t("var.title"), subtitle=t("var.caption"))

s = pv.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📦 " + t("var.kpi_groups"), str(s["groups"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🎨 " + t("var.kpi_variants"), str(s["variants"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("🏪 " + t("var.kpi_stock"), str(s["total_stock"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("❌ " + t("var.kpi_oos"), str(s["out_of_stock"]),
                     hint=t("var.oos_hint") if s["out_of_stock"] > 0 else "",
                     hint_tone="danger" if s["out_of_stock"] > 0 else "ok")

# ---- Add variant group -------------------------------------------------------
st.divider()
with st.expander(t("var.add_title"), expanded=s["groups"] == 0):
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name FROM products ORDER BY sku"
        ).fetchall()

    if not products:
        st.info(t("var.no_products"))
    else:
        with st.form("add_variant_group"):
            prod_opts = [p["sku"] + " — " + (p["name"] or "")[:30]
                         for p in products]
            sel_idx = st.selectbox(
                t("var.f_parent_sku"), range(len(prod_opts)),
                format_func=lambda i: prod_opts[i],
                key="_var_parent",
            )
            parent_sku = products[sel_idx]["sku"]

            st.caption(t("var.axes_help"))
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                axis1_name = st.text_input(
                    t("var.f_axis1"), placeholder=t("var.axis1_ph"), key="_va1n")
                axis1_vals = st.text_input(
                    t("var.f_axis1_vals"), placeholder=t("var.axis1_vals_ph"),
                    key="_va1v")
            with ac2:
                axis2_name = st.text_input(
                    t("var.f_axis2"), placeholder=t("var.axis2_ph"), key="_va2n")
                axis2_vals = st.text_input(
                    t("var.f_axis2_vals"), placeholder=t("var.axis2_vals_ph"),
                    key="_va2v")
            with ac3:
                axis3_name = st.text_input(
                    t("var.f_axis3"), placeholder="", key="_va3n")
                axis3_vals = st.text_input(
                    t("var.f_axis3_vals"), placeholder="",
                    key="_va3v")

            base_cost = st.number_input(t("var.f_base_cost"), min_value=0.0,
                                        value=0.0, step=10.0)
            base_sell = st.number_input(t("var.f_base_sell"), min_value=0.0,
                                        value=0.0, step=10.0)
            base_stock = st.number_input(t("var.f_base_stock"), min_value=0,
                                         value=0, step=1)

            if st.form_submit_button(t("var.generate_btn"), type="primary"):
                axes = []
                combos_per_axis = []

                for name_in, vals_in in [(axis1_name, axis1_vals),
                                          (axis2_name, axis2_vals),
                                          (axis3_name, axis3_vals)]:
                    if name_in.strip() and vals_in.strip():
                        vals_list = [v.strip() for v in vals_in.split(",")
                                     if v.strip()]
                        axes.append(name_in.strip())
                        combos_per_axis.append((name_in.strip(), vals_list))

                if axes:
                    pv.create_group(parent_sku, axes)
                    count = 0
                    if len(combos_per_axis) == 1:
                        for v1 in combos_per_axis[0][1]:
                            attrs = {combos_per_axis[0][0]: v1}
                            pv.add_variant(parent_sku, attrs, base_stock,
                                           base_cost or None, base_sell or None)
                            count += 1
                    elif len(combos_per_axis) >= 2:
                        for v1 in combos_per_axis[0][1]:
                            for v2 in combos_per_axis[1][1]:
                                if len(combos_per_axis) >= 3:
                                    for v3 in combos_per_axis[2][1]:
                                        attrs = {combos_per_axis[0][0]: v1,
                                                 combos_per_axis[1][0]: v2,
                                                 combos_per_axis[2][0]: v3}
                                        pv.add_variant(parent_sku, attrs,
                                                        base_stock,
                                                        base_cost or None,
                                                        base_sell or None)
                                        count += 1
                                else:
                                    attrs = {combos_per_axis[0][0]: v1,
                                             combos_per_axis[1][0]: v2}
                                    pv.add_variant(parent_sku, attrs, base_stock,
                                                   base_cost or None,
                                                   base_sell or None)
                                    count += 1
                    toast(t("var.generated", fmt={"count": str(count)}), icon="✅")
                    st.rerun()

# ---- View and edit variants -------------------------------------------------
st.divider()
groups = pv.all_groups()

if not groups:
    st.info(t("var.empty"))
    st.stop()

for grp in groups:
    details = pv.get_variants(grp["parent_sku"])
    with st.expander(
        "📦 " + grp["parent_sku"] + " — " +
        (grp.get("product_name") or "")[:25] +
        " (" + t("var.group_expander_suffix",
                  variants=str(details["active_count"]),
                  stock=str(details["total_stock"])) + ")"
    ):
        for var in details["variants"]:
            vc1, vc2, vc3, vc4 = st.columns([3, 1, 1, 1])
            with vc1:
                oos = var["stock"] == 0
                st.markdown(
                    "<span style='font-size:13px'>"
                    + ("🔴 " if oos else "🟢 ")
                    + "<strong>" + var["label"] + "</strong>"
                    " <span style='color:#9a9485;font-size:11px'>"
                    + var["variant_sku"] + "</span></span>",
                    unsafe_allow_html=True,
                )
            with vc2:
                new_stock = st.number_input(
                    t("var.f_stock"),
                    value=var["stock"],
                    min_value=0,
                    step=1,
                    key="_vs_" + var["variant_sku"],
                    label_visibility="collapsed",
                )
                if new_stock != var["stock"]:
                    pv.update_stock(var["variant_sku"], new_stock)
                    st.rerun()
            with vc3:
                st.caption(
                    t("var.cost_line", amount="{:,.0f}".format(var["cost_price"] or 0))
                )
            with vc4:
                st.caption(
                    t("var.sell_line", amount="{:,.0f}".format(var["sell_price"] or 0))
                )
