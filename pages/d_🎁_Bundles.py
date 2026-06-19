"""Bundle Manager — sell more per order with smart bundles.

AI analyzes order history to find products frequently bought together,
then suggests bundle pricing with psychological discounts."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import bundle_engine as be
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
be.init()
render_sidebar()

page_header(icon="🎁", title=t("bundle.title"), subtitle=t("bundle.caption"))


# ---- KPI overview -----------------------------------------------------------

bs = be.stats()

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("bundle.kpi_active"), str(bs["active"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("bundle.kpi_sold"), str(bs["total_sold"]),
        hint="", hint_tone="info",
    )
with k3:
    metric_with_hint(
        t("bundle.kpi_revenue"), "{:,.0f}".format(bs["total_revenue"]),
        hint="", hint_tone="info",
    )


# ---- AI Bundle Suggestions --------------------------------------------------

st.divider()
st.markdown("### 🤖 " + t("bundle.suggest_title"))
st.caption(t("bundle.suggest_help"))

suggestions = be.suggest_bundles(8)
if suggestions:
    for i, s in enumerate(suggestions):
        saving_str = "{:,.0f}".format(s["saving"])
        discount_str = "{:.0f}%".format(s["discount_pct"])
        individual_str = "{:,.0f}".format(s["individual_total"])
        bundle_str = "{:,.0f}".format(s["bundle_price"])

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='background:rgba(77,108,92,0.03);border:0.5px solid rgba(40,30,20,0.06);"
                "border-radius:10px;padding:12px 16px;margin-bottom:6px'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                "<div><span style='font-size:14px;font-weight:600'>"
                "🔗 " + s["sku_a"] + " + " + s["sku_b"] + "</span>"
                " <span style='color:#7a7569;font-size:12px'>" +
                t("bundle.bought_together") + " " + str(s["freq"]) + "x</span></div>"
                "<div style='display:flex;gap:12px;align-items:baseline'>"
                "<span style='text-decoration:line-through;color:#9a9485;font-size:13px'>"
                "฿" + individual_str + "</span>"
                "<span style='font-size:1.2rem;font-weight:600;color:#4d6c5c'>"
                "฿" + bundle_str + "</span>"
                "<span style='background:rgba(197,75,75,0.08);color:#c54c4c;"
                "padding:2px 8px;border-radius:6px;font-size:11px'>"
                "-" + discount_str + " " + t("bundle.save") + " ฿" + saving_str + "</span>"
                "</div></div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            if st.button(
                "✅ " + t("bundle.create_btn"),
                key="_bs_" + str(i),
                type="tertiary",
            ):
                name = s["sku_a"] + " + " + s["sku_b"]
                be.create_bundle(
                    name=name,
                    skus=[s["sku_a"], s["sku_b"]],
                    individual_total=s["individual_total"],
                    bundle_price=s["bundle_price"],
                )
                toast(t("bundle.created"), icon="🎁")
                st.rerun()
else:
    st.info(t("bundle.no_suggestions"))
    st.caption(t("bundle.no_suggestions_help"))


# ---- Manual bundle creation --------------------------------------------------

st.divider()
with st.expander(t("bundle.manual_title"), expanded=False):
    with st.form("create_bundle"):
        mb_name = st.text_input(t("bundle.f_name"), placeholder="Solar Panel + Inverter Set")

        with db.conn() as c:
            all_skus = [r["sku"] for r in c.execute(
                "SELECT sku FROM products WHERE sku IS NOT NULL ORDER BY sku"
            ).fetchall()]

        mb_skus = st.multiselect(t("bundle.f_skus"), all_skus)

        mc1, mc2 = st.columns(2)
        with mc1:
            mb_total = st.number_input(
                t("bundle.f_individual"), min_value=0.0, step=50.0, format="%.0f",
            )
        with mc2:
            mb_price = st.number_input(
                t("bundle.f_bundle_price"), min_value=0.0, step=50.0, format="%.0f",
            )

        if st.form_submit_button(t("bundle.create_btn"), type="primary"):
            if mb_name.strip() and mb_skus and mb_price > 0:
                be.create_bundle(mb_name.strip(), mb_skus, mb_total, mb_price)
                toast(t("bundle.created"), icon="🎁")
                st.rerun()
            else:
                st.warning(t("bundle.need_fields"))


# ---- Active bundles ----------------------------------------------------------

bundles = be.all_bundles()
if bundles:
    st.divider()
    st.markdown("### " + t("bundle.active_title"))

    for b in bundles:
        status = b.get("status", "active")
        s_icon = "🟢" if status == "active" else "⏹"
        discount = b.get("discount_pct", 0)
        sold = b.get("times_sold", 0)

        cA, cB = st.columns([5, 2])
        with cA:
            individual_str = "{:,.0f}".format(b.get("individual_total", 0))
            bundle_str = "{:,.0f}".format(b.get("bundle_price", 0))
            st.markdown(
                "<div style='padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<div>" + s_icon + " <strong>" + (b.get("name") or "—") + "</strong>"
                " <span style='color:#7a7569;font-size:12px'>" +
                (b.get("skus") or "") + "</span></div>"
                "<div style='display:flex;gap:14px;align-items:center;font-size:13px'>"
                "<span style='text-decoration:line-through;color:#9a9485'>฿" + individual_str + "</span>"
                "<span style='font-weight:600;color:#4d6c5c'>฿" + bundle_str + "</span>"
                "<span style='color:#7a7569'>-" + "{:.0f}%".format(discount) + "</span>"
                "<span>📦 " + t("common.n_sold", n=str(sold)) + "</span>"
                "</div></div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if st.button("📦+1", key="_bsold_" + str(b["id"]),
                             type="tertiary", help=t("bundle.record_sale")):
                    be.record_sale(b["id"])
                    st.rerun()
            with bc2:
                new_status = "inactive" if status == "active" else "active"
                toggle = "⏹" if status == "active" else "▶"
                if st.button(toggle, key="_bt_" + str(b["id"]), type="tertiary"):
                    be.update_bundle(b["id"], status=new_status)
                    st.rerun()
            with bc3:
                if st.button("🗑", key="_bd_" + str(b["id"]),
                             type="tertiary", help=t("common.delete")):
                    be.delete_bundle(b["id"])
                    st.rerun()
