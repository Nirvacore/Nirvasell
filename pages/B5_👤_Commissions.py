"""Staff Commission Tracker — track commissions per staff member."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
import db
import commissions as cm
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Commissions",
                   page_icon="👤", layout="wide")
apply_theme()
require_auth()
db.init()
cm.init()
render_sidebar()

page_header(icon="👤", title=t("comm.title"), subtitle=t("comm.caption"))

s = cm.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("👥 " + t("comm.kpi_staff"), str(s["staff_count"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("⏳ " + t("comm.kpi_pending"),
                     "฿{:,.0f}".format(s["total_pending"]),
                     hint=t("comm.pending_hint") if s["total_pending"] > 0 else "",
                     hint_tone="warn" if s["total_pending"] > 0 else "ok")
with k3:
    metric_with_hint("📅 " + t("comm.kpi_this_month"),
                     "฿{:,.0f}".format(s["this_month"]),
                     hint="", hint_tone="info")

# ---- Add staff --------------------------------------------------------------
st.divider()
with st.expander(t("comm.add_staff_title"), expanded=s["staff_count"] == 0):
    with st.form("add_staff"):
        sc1, sc2 = st.columns(2)
        with sc1:
            staff_name = st.text_input(t("comm.f_name"),
                                       placeholder=t("comm.name_ph"))
        with sc2:
            pct = st.number_input(t("comm.f_pct"), min_value=0.5,
                                   max_value=50.0, value=5.0, step=0.5)
        if st.form_submit_button(t("comm.add_btn"), type="primary"):
            if staff_name.strip():
                cm.add_staff(staff_name.strip(), pct)
                toast(t("comm.added"), icon="✓")
                st.rerun()

# ---- Record commission ------------------------------------------------------
st.divider()
st.markdown("### ➕ " + t("comm.record_title"))

staff_list = cm.all_staff()
if not staff_list:
    st.info(t("comm.no_staff"))
else:
    with st.form("record_comm"):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            staff_opts = [s["name"] + " (" + str(s["commission_pct"]) + "%)"
                          for s in staff_list]
            sel_staff_idx = st.selectbox(
                t("comm.f_staff"), range(len(staff_opts)),
                format_func=lambda i: staff_opts[i], key="_cm_st",
            )
        with rc2:
            sale_amount = st.number_input(t("comm.f_amount"),
                                          min_value=0.0, value=0.0,
                                          step=100.0)
        with rc3:
            order_id = st.text_input(t("comm.f_order_id"),
                                     placeholder=t("comm.order_ph"))
        overrides_pct = st.number_input(
            t("comm.f_override_pct"),
            min_value=0.0, max_value=50.0,
            value=float(staff_list[sel_staff_idx]["commission_pct"]),
            step=0.5,
        )
        if st.form_submit_button(t("comm.record_btn"), type="primary"):
            if sale_amount > 0:
                cm.record(
                    staff_id=staff_list[sel_staff_idx]["id"],
                    order_id=order_id.strip(),
                    sale_amount=sale_amount,
                    commission_pct=overrides_pct,
                )
                toast(t("comm.recorded"), icon="✓")
                st.rerun()

# ---- Period summary ---------------------------------------------------------
st.divider()
st.markdown("### 📅 " + t("comm.period_title"))

current_period = datetime.today().strftime("%Y-%m")
period_data = cm.period_summary(current_period)

for staff_row in period_data:
    p_color = "#4d6c5c" if staff_row["pending"] == 0 else "#c5963d"
    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-radius:8px;background:white;margin-bottom:4px'>"
        "<div>"
        "👤 <strong>" + staff_row["name"] + "</strong>"
        " <span style='color:#9a9485;font-size:12px'>"
        + str(staff_row["commission_pct"]) + "%</span></div>"
        "<div style='display:flex;gap:16px;font-size:13px'>"
        "<span>" + t("common.sales") + " ฿{:,.0f}".format(staff_row["total_sales"]) + "</span>"
        "<span>" + t("common.commission") + " ฿<strong>{:,.0f}".format(staff_row["total_commission"]) + "</strong></span>"
        "<span style='color:" + p_color + ";font-weight:600'>"
        + t("common.pending_pay") + " ฿{:,.0f}".format(staff_row["pending"]) + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    if staff_row["pending"] > 0:
        staff_id = next(
            (s["id"] for s in staff_list if s["name"] == staff_row["name"]), None
        )
        if staff_id and st.button(
            t("comm.pay_btn") + " ฿{:,.0f}".format(staff_row["pending"]),
            key="_pay_" + staff_row["name"],
            type="tertiary",
        ):
            paid = cm.mark_paid(staff_id, current_period)
            toast(t("comm.paid_msg", fmt={"name": staff_row["name"],
                                          "amount": "{:,.0f}".format(paid)}),
                  icon="💰")
            st.rerun()
