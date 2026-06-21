"""Promotions — plan flash sales, track coupons, measure ROI.

12.12 sale? LINE coupon giveaway? Free shipping threshold?
Plan it, track it, kill what doesn't work."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import promo_engine as pe
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Promotions",
                   page_icon="🎪", layout="wide")
apply_theme()
require_auth()
db.init()
pe.init()
render_sidebar()

page_header(icon="🎪", title=t("promo.title"), subtitle=t("promo.caption"))


# ---- KPIs -------------------------------------------------------------------

s = pe.stats()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("promo.kpi_total"), str(s["total"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("promo.kpi_active"), str(s["active"]),
        hint="", hint_tone="ok",
    )
with k3:
    metric_with_hint(
        t("promo.kpi_redemptions"), str(s["total_redemptions"]),
        hint="", hint_tone="info",
    )
with k4:
    roi_tone = "ok" if s["overall_roi"] > 0 else "danger"
    metric_with_hint(
        t("promo.kpi_roi"), str(s["overall_roi"]) + "%",
        hint="", hint_tone=roi_tone,
    )


# ---- Create promotion -------------------------------------------------------

st.divider()
with st.expander(t("promo.create_title"), expanded=s["total"] == 0):
    with st.form("create_promo"):
        p_name = st.text_input(
            t("promo.f_name") + " *",
            placeholder=t("promo.name_ph"),
        )

        pc1, pc2 = st.columns(2)
        with pc1:
            type_keys = list(pe.PROMO_TYPES.keys())
            p_type = st.selectbox(
                t("promo.f_type"),
                type_keys,
                format_func=lambda k: pe.PROMO_TYPES[k]["icon"] + " " + pe.PROMO_TYPES[k]["label"],
            )
        with pc2:
            platforms = ["all", "shopee", "lazada", "tiktok", "facebook", "line", "website"]
            p_platform = st.selectbox(t("promo.f_platform"), platforms)

        dc1, dc2 = st.columns(2)
        with dc1:
            p_start = st.date_input(t("promo.f_start"))
        with dc2:
            p_end = st.date_input(t("promo.f_end"))

        dc3, dc4, dc5 = st.columns(3)
        with dc3:
            dtype_keys = list(pe.DISCOUNT_TYPES.keys())
            p_dtype = st.selectbox(
                t("promo.f_discount_type"),
                dtype_keys,
                format_func=lambda k: pe.DISCOUNT_TYPES[k],
            )
        with dc4:
            p_dvalue = st.number_input(
                t("promo.f_discount_value"),
                min_value=0.0, value=10.0, step=1.0,
            )
        with dc5:
            p_max_disc = st.number_input(
                t("promo.f_max_discount"),
                min_value=0.0, value=0.0, step=10.0,
            )

        mc1, mc2 = st.columns(2)
        with mc1:
            p_min_order = st.number_input(
                t("promo.f_min_order"),
                min_value=0.0, value=0.0, step=50.0,
            )
        with mc2:
            p_budget = st.number_input(
                t("promo.f_budget"),
                min_value=0.0, value=0.0, step=100.0,
            )

        p_coupon = st.text_input(
            t("promo.f_coupon"),
            placeholder=t("promo.coupon_ph"),
        )
        p_note = st.text_input(t("promo.f_note"), placeholder="")

        if st.form_submit_button(t("promo.create_btn"), type="primary"):
            if p_name.strip():
                pe.add(
                    name=p_name.strip(),
                    promo_type=p_type,
                    platform=p_platform,
                    start_date=str(p_start),
                    end_date=str(p_end),
                    discount_type=p_dtype,
                    discount_value=p_dvalue,
                    min_order=p_min_order,
                    max_discount=p_max_disc,
                    coupon_code=p_coupon.strip(),
                    budget=p_budget,
                    note=p_note.strip(),
                )
                toast(t("promo.created"), icon="✓")
                st.rerun()
            else:
                st.warning(t("promo.need_name"))


# ---- Promotion list ----------------------------------------------------------

promos = pe.all_promos()
if promos:
    st.divider()
    st.markdown("### " + t("promo.list_title"))

    for p in promos:
        status = p.get("status", "draft")
        status_icon = {"draft": "📝", "active": "🟢", "ended": "⏹", "cancelled": "❌"}.get(status, "?")
        type_info = pe.PROMO_TYPES.get(p["promo_type"], {})
        type_icon = type_info.get("icon", "🎪")
        roi_str = str(p.get("roi", 0)) + "%"
        redemp = str(p.get("redemptions", 0))
        rev_str = "{:,.0f}".format(p.get("revenue_generated", 0))

        budget_str = ""
        if p.get("budget") and p["budget"] > 0:
            budget_str = t("promo.budget_used", n=str(int(p["budget_used_pct"])))

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<div>" + status_icon + " " + type_icon +
                " <strong>" + (p.get("name") or "—") + "</strong>"
                " <span style='color:#9a9485;font-size:11px'>" +
                (p.get("coupon_code") or "") + "</span></div>"
                "<div style='font-size:12px;color:#9a9485'>"
                + t("promo.list_redemptions", n=redemp) + " · 💵 ฿" + rev_str +
                t("promo.list_roi", roi=roi_str) + budget_str + "</div></div>"
                "<div style='font-size:11px;color:#7a7569;margin-top:3px'>"
                + (p.get("start_date") or "") + " → " + (p.get("end_date") or "") +
                " · " + p.get("platform", "all") + "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if status == "draft":
                    if st.button("▶", key="_pa_" + str(p["id"]), type="tertiary",
                                 help=t("promo.activate")):
                        pe.update_status(p["id"], "active")
                        st.rerun()
                elif status == "active":
                    if st.button("⏹", key="_pe_" + str(p["id"]), type="tertiary",
                                 help=t("promo.end")):
                        pe.update_status(p["id"], "ended")
                        st.rerun()
            with bc2:
                if status in ("draft", "active"):
                    if st.button("❌", key="_pc_" + str(p["id"]), type="tertiary"):
                        pe.update_status(p["id"], "cancelled")
                        st.rerun()
            with bc3:
                if st.button("🗑", key="_pd_" + str(p["id"]), type="tertiary"):
                    pe.delete(p["id"])
                    st.rerun()
