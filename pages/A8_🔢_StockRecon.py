"""Stock Reconciliation — physical count vs system, log variances."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import stock_recon as sr
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Stock Recon",
                   page_icon="🔢", layout="wide")
apply_theme()
require_auth()
db.init()
sr.init()
render_sidebar()

page_header(icon="🔢", title=t("recon.title"), subtitle=t("recon.caption"))

s = sr.summary()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("📋 " + t("recon.kpi_total_counts"), str(s["total_counts"]),
                     hint="", hint_tone="info")
with k2:
    last_date = s.get("last_count_date") or "—"
    metric_with_hint("📅 " + t("recon.kpi_last"), last_date[:10],
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("⚠️ " + t("recon.kpi_discrepancies"),
                     str(s["total_discrepancies_ever"]),
                     hint="", hint_tone="warn" if s["total_discrepancies_ever"] > 0 else "ok")

# ---- New count or active count ---------------------------------------------
st.divider()

if "active_count_id" not in st.session_state:
    st.session_state.active_count_id = None

if st.session_state.active_count_id is None:
    st.markdown("### " + t("recon.start_title"))
    with st.form("new_count"):
        count_notes = st.text_input(t("recon.f_notes"),
                                    placeholder=t("recon.notes_ph"))
        if st.form_submit_button(t("recon.start_btn"), type="primary"):
            count_id = sr.new_count(count_notes.strip())
            st.session_state.active_count_id = count_id
            toast(t("recon.count_started"), icon="📋")
            st.rerun()

    # History
    history = sr.history(5)
    if history:
        st.divider()
        st.markdown("### " + t("recon.history_title"))
        for h in history:
            h_color = "#c54c4c" if (h.get("total_abs_variance") or 0) > 0 else "#4d6c5c"
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<span>📋 <strong>" + h["count_date"] + "</strong>"
                " · " + (h["notes"] or "—")[:30] + "</span>"
                "<span style='display:flex;gap:12px'>"
                "<span>" + str(h.get("total_skus") or 0) + " SKU</span>"
                "<span style='color:" + h_color + ";font-weight:600'>"
                + ("±" + str(h.get("total_abs_variance") or 0)) + " ต่าง</span>"
                "<span style='font-size:11px;color:#9a9485'>"
                + h["status"] + "</span></span></div>",
                unsafe_allow_html=True,
            )
else:
    count_id = st.session_state.active_count_id
    count = sr.get_count(count_id)

    if not count:
        st.session_state.active_count_id = None
        st.rerun()

    # Active count header
    st.markdown(
        "### 📋 " + t("recon.counting_title") +
        " — " + count["date"] +
        " (" + str(count["discrepancies"]) + " " + t("recon.discrepancies") + ")"
    )

    if count.get("estimated_loss") and count["estimated_loss"] > 0:
        st.error("⚠️ " + t("recon.loss_warning") +
                 " ฿{:,.0f}".format(count["estimated_loss"]))

    # Discrepancy filter
    show_filter = st.selectbox(
        t("recon.f_show"),
        ["all", "discrepancies"],
        format_func=lambda x: {"all": t("recon.show_all"),
                                "discrepancies": t("recon.show_diff")}.get(x, x),
        key="_recon_filter",
    )

    items = count["items"]
    if show_filter == "discrepancies":
        items = [i for i in items if i["variance"] != 0]

    for item in items:
        var = item["variance"]
        var_color = "#4d6c5c" if var == 0 else ("#c54c4c" if var < 0 else "#4a7ab5")
        var_str = str(var) if var == 0 else ("+" + str(var) if var > 0 else str(var))

        ic1, ic2 = st.columns([5, 1])
        with ic1:
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "align-items:center;padding:4px 14px;"
                "border-bottom:0.5px solid rgba(40,30,20,0.04)'>"
                "<span style='font-size:13px'><strong>" + item["sku"] + "</strong>"
                " <span style='color:#9a9485'>" + (item.get("name") or "")[:30] + "</span></span>"
                "<span style='display:flex;gap:12px;font-size:13px'>"
                "<span>ระบบ: " + str(item["system_qty"]) + "</span>"
                "<span>จริง: <strong>" + str(item["physical_qty"]) + "</strong></span>"
                "<span style='color:" + var_color + ";font-weight:600'>"
                + var_str + "</span></span></div>",
                unsafe_allow_html=True,
            )
        with ic2:
            new_qty = st.number_input(
                "qty",
                value=item["physical_qty"],
                min_value=0,
                step=1,
                key="_recon_" + item["sku"],
                label_visibility="collapsed",
            )
            if new_qty != item["physical_qty"]:
                sr.update_physical(count_id, item["sku"], new_qty)
                st.rerun()

    st.divider()
    fc1, fc2 = st.columns(2)
    with fc1:
        if st.button(t("recon.cancel_btn"), key="_recon_cancel", type="tertiary"):
            st.session_state.active_count_id = None
            st.rerun()
    with fc2:
        if st.button(t("recon.finalize_btn"), key="_recon_finalize",
                      type="primary"):
            sr.finalize(count_id, apply_adjustments=True)
            st.session_state.active_count_id = None
            toast(t("recon.finalized"), icon="✅")
            st.rerun()
