"""Customer CRM — notes, tags, follow-ups per customer.

Remember who they are. What they like. When to reach out."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
import db
import customer_crm as crm
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import crm_note_type_label, crm_tag_label

st.set_page_config(page_title="nirva.sell · CRM",
                   page_icon="📇", layout="wide")
apply_theme()
require_auth()
db.init()
crm.init()
render_sidebar()

page_header(icon="📇", title=t("crm.title"), subtitle=t("crm.caption"))

s = crm.stats()

# ---- KPIs -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(t("crm.kpi_tracked"), str(s["customers_tracked"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint(t("crm.kpi_notes"), str(s["notes"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint(t("crm.kpi_tags"), str(s["tags"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("💬 " + t("crm.kpi_followups"), str(s["followups_pending"]),
                     hint=t("crm.followup_hint") if s["followups_pending"] > 0 else "",
                     hint_tone="warn" if s["followups_pending"] > 0 else "ok")


# ---- Pending follow-ups -----------------------------------------------------

followups = crm.pending_followups()
if followups:
    st.divider()
    st.markdown("### 💬 " + t("crm.followups_title"))

    for fu in followups:
        fu_date = (fu.get("followup_date") or "")[:10]
        is_overdue = fu_date < date.today().strftime("%Y-%m-%d")
        d_color = "#c54c4c" if is_overdue else "#c5963d"
        d_icon = "🔴" if is_overdue else "🟡"

        fc1, fc2 = st.columns([5, 1])
        with fc1:
            st.markdown(
                "<div style='padding:6px 14px;border-left:3px solid " + d_color + "'>"
                + d_icon + " <strong>" + fu["customer_key"] + "</strong>"
                " · " + fu_date +
                " · " + (fu.get("reason") or "") + "</div>",
                unsafe_allow_html=True,
            )
        with fc2:
            if st.button("✅", key="_fu_" + str(fu["id"]), type="tertiary"):
                crm.complete_followup(fu["id"])
                st.rerun()


# ---- Customer search & profile -----------------------------------------------

st.divider()
st.markdown("### " + t("crm.search_title"))

# Get all customers from orders
with db.conn() as c:
    all_custs = c.execute("""
        SELECT COALESCE(buyer_phone, buyer_name) AS ckey,
               buyer_name, buyer_phone,
               COUNT(*) AS orders, SUM(total_amount) AS total,
               MAX(order_date) AS last_order
        FROM orders
        WHERE buyer_name IS NOT NULL AND buyer_name != ''
        GROUP BY ckey ORDER BY total DESC
    """).fetchall()

if not all_custs:
    st.info(t("crm.empty"))
    st.stop()

cust_options = [
    (c["ckey"], t("crm.cust_option",
                   name=c["buyer_name"],
                   orders=str(c["orders"]),
                   total="{:,.0f}".format(c["total"] or 0)))
    for c in all_custs
]

selected_cust = st.selectbox(
    t("crm.select_customer"),
    [c[0] for c in cust_options],
    format_func=lambda k: next(c[1] for c in cust_options if c[0] == k),
)

if selected_cust:
    profile = crm.customer_profile(selected_cust)

    # Profile header
    st.markdown(
        "<div style='background:rgba(77,108,92,0.04);border-radius:12px;padding:16px;"
        "margin:10px 0'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
        "<span style='font-size:1.2rem;font-weight:600'>👤 " + selected_cust + "</span>"
        "<span>📦 " + str(profile["orders"]) + "x · ฿" +
        "{:,.0f}".format(profile["total_spent"]) + "</span></div>"
        "<div style='font-size:12px;color:#7a7569;margin-top:4px'>"
        + t("crm.last_order_line", date=(profile.get("last_order") or "—")[:10]) + "</div></div>",
        unsafe_allow_html=True,
    )

    # Tags
    current_tags = profile["tags"]
    st.markdown("**🏷 " + t("crm.tags") + ":** " +
                (" ".join("`" + crm_tag_label(tg) + "`" for tg in current_tags) if current_tags else "—"))

    tag_col1, tag_col2 = st.columns(2)
    with tag_col1:
        new_tag = st.selectbox(
            t("crm.add_tag"),
            [tg for tg in crm.DEFAULT_TAGS if tg not in current_tags],
            label_visibility="collapsed",
            format_func=crm_tag_label,
            key="_tag_sel",
        )
        if st.button(t("crm.add_tag_btn"), key="_add_tag", type="tertiary"):
            crm.add_tag(selected_cust, new_tag)
            st.rerun()

    # Add note
    with st.form("add_note"):
        nc1, nc2 = st.columns([3, 1])
        with nc1:
            note_text = st.text_input(t("crm.f_note"), placeholder=t("crm.note_ph"))
        with nc2:
            note_type = st.selectbox(
                t("crm.f_type"),
                list(crm.NOTE_TYPES.keys()),
                format_func=lambda k: crm.NOTE_TYPES[k]["icon"] + " " + crm_note_type_label(k),
                label_visibility="collapsed",
            )
        if st.form_submit_button(t("crm.add_note_btn"), type="tertiary"):
            if note_text.strip():
                crm.add_note(selected_cust, note_text.strip(), note_type)
                toast(t("crm.note_added"), icon="✓")
                st.rerun()

    # Add follow-up
    with st.form("add_followup"):
        fuc1, fuc2 = st.columns(2)
        with fuc1:
            fu_date = st.date_input(t("crm.f_followup_date"))
        with fuc2:
            fu_reason = st.text_input(t("crm.f_followup_reason"), placeholder=t("crm.followup_ph"))
        if st.form_submit_button(t("crm.add_followup_btn"), type="tertiary"):
            crm.add_followup(selected_cust, str(fu_date), fu_reason.strip())
            toast(t("crm.followup_added"), icon="✓")
            st.rerun()

    # Notes history
    notes = profile["notes"]
    if notes:
        st.markdown("### 📝 " + t("crm.notes_title"))
        for n in notes:
            ntype = crm.NOTE_TYPES.get(n["note_type"], {"icon": "📝"})
            st.markdown(
                "<div style='padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                + ntype["icon"] + " " + n["note"] +
                " <span style='color:#9a9485;font-size:11px'>" +
                (n["created_at"] or "")[:16] + "</span></div>",
                unsafe_allow_html=True,
            )
