"""Competitor Watch — track rival prices, spot undercuts.

Enter competitor prices manually. System alerts when they're cheaper."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import competitor_watch as cw
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Competitors",
                   page_icon="🔍", layout="wide")
apply_theme()
require_auth()
db.init()
cw.init()
render_sidebar()

page_header(icon="🔍", title=t("comp.title"), subtitle=t("comp.caption"))

s = cw.stats()

# ---- KPIs -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(t("comp.kpi_skus"), str(s["tracked_skus"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint(t("comp.kpi_competitors"), str(s["competitors"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("✅ " + t("comp.kpi_cheaper"), str(s["cheaper"]),
                     hint="", hint_tone="ok")
with k4:
    metric_with_hint("🔴 " + t("comp.kpi_undercut"), str(s["more_expensive"]),
                     hint=t("comp.undercut_hint") if s["more_expensive"] > 0 else "",
                     hint_tone="danger" if s["more_expensive"] > 0 else "ok")


# ---- Add price entry ---------------------------------------------------------

st.divider()
with st.expander(t("comp.add_title"), expanded=s["tracked_skus"] == 0):
    with st.form("add_comp"):
        # Get product list for SKU dropdown
        with db.conn() as c:
            products = c.execute(
                "SELECT sku, name FROM products ORDER BY sku"
            ).fetchall()

        if products:
            sku_options = [p["sku"] + " — " + (p["name"] or "")[:30] for p in products]
            selected_idx = st.selectbox(t("comp.f_sku"), range(len(sku_options)),
                                        format_func=lambda i: sku_options[i])
            selected_sku = products[selected_idx]["sku"]
        else:
            selected_sku = st.text_input(t("comp.f_sku") + " *")

        cc1, cc2 = st.columns(2)
        with cc1:
            comp_name = st.text_input(
                t("comp.f_competitor") + " *",
                placeholder=t("comp.comp_ph"),
            )
        with cc2:
            comp_price = st.number_input(
                t("comp.f_price") + " *",
                min_value=0.0, step=10.0,
            )

        cc3, cc4 = st.columns(2)
        with cc3:
            comp_platform = st.selectbox(
                t("comp.f_platform"),
                ["shopee", "lazada", "tiktok", "facebook", "website", "other"],
            )
        with cc4:
            comp_url = st.text_input(t("comp.f_url"), placeholder="https://...")

        comp_note = st.text_input(t("comp.f_note"))

        if st.form_submit_button(t("comp.add_btn"), type="primary"):
            if selected_sku and comp_name.strip() and comp_price > 0:
                cw.add(
                    sku=selected_sku if isinstance(selected_sku, str) else selected_sku,
                    competitor=comp_name.strip(),
                    price=comp_price,
                    platform=comp_platform,
                    url=comp_url.strip(),
                    note=comp_note.strip(),
                )
                toast(t("comp.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("comp.need_fields"))


# ---- Undercut alerts ---------------------------------------------------------

undercuts = cw.undercut_alerts()
if undercuts:
    st.divider()
    st.markdown("### 🚨 " + t("comp.alert_title"))

    for u in undercuts:
        diff_str = "{:,.0f}".format(abs(u["diff"]))
        my_str = "{:,.0f}".format(u.get("my_price") or 0)
        their_str = "{:,.0f}".format(u.get("price") or 0)

        st.markdown(
            "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid #c54c4c'>"
            "🔴 <strong>" + u["sku"] + "</strong>"
            " — " + u["competitor"] +
            " (" + (u.get("platform") or "") + ")"
            + t("comp.you_vs", you=my_str, them=their_str) +
            " · <span style='color:#c54c4c;font-weight:600'>" +
            t("comp.cheaper_by", amount=diff_str) + "</span></div>",
            unsafe_allow_html=True,
        )


# ---- Full comparison ---------------------------------------------------------

comp = cw.comparison()
if comp:
    st.divider()
    st.markdown("### " + t("comp.comparison_title"))

    for c_item in comp:
        pos = c_item["position"]
        pos_icon = {"cheaper": "✅", "same": "🟰", "more_expensive": "🔴", "unknown": "⚪"}.get(pos, "?")
        pos_color = {"cheaper": "#4d6c5c", "same": "#9a9485",
                     "more_expensive": "#c54c4c", "unknown": "#7a7569"}.get(pos, "#7a7569")

        my_str = "{:,.0f}".format(c_item.get("my_price") or 0)
        their_str = "{:,.0f}".format(c_item.get("price") or 0)
        diff_str = ("+" if c_item["diff"] > 0 else "") + "{:,.0f}".format(c_item["diff"])

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>"
            + pos_icon + " <strong>" + c_item["sku"] + "</strong>"
            " <span style='color:#9a9485;font-size:11px'>"
            "vs " + c_item["competitor"] + " (" + (c_item.get("platform") or "") + ")</span>"
            "</div>"
            "<div style='display:flex;gap:12px;font-size:13px'>"
            "<span>" + t("comp.price_you", amount=my_str) + "</span>"
            "<span>" + t("comp.price_them", amount=their_str) + "</span>"
            "<span style='font-weight:600;color:" + pos_color + "'>" + diff_str + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )
