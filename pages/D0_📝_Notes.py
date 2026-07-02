"""Operational Notes — quick memos, pinned reminders, urgent flags."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import notes as nt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import note_type_label, note_priority_label

st.set_page_config(page_title="nirva.sell · Notes",
                   page_icon="📝", layout="wide")
apply_theme()
require_auth()
db.init()
nt.init()
render_sidebar()

page_header(icon="📝", title=t("nt.title"), subtitle=t("nt.caption"))

s = nt.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("📝 " + t("nt.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🔴 " + t("nt.kpi_urgent"), str(s["urgent"]),
                     hint="", hint_tone="danger" if s["urgent"] > 0 else "ok")
with k3:
    metric_with_hint("📌 " + t("nt.kpi_pinned"), str(s["pinned"]),
                     hint="", hint_tone="info")

# ---- Add note ---------------------------------------------------------------
st.divider()
with st.expander(t("nt.add_title"), expanded=False):
    with st.form("add_note"):
        nc1, nc2 = st.columns(2)
        with nc1:
            note_title = st.text_input(t("nt.f_title"),
                                        placeholder=t("nt.title_ph"))
            note_type = st.selectbox(
                t("nt.f_type"),
                list(nt.NOTE_TYPES.keys()),
                format_func=lambda k: nt.NOTE_TYPES[k]["icon"] + " " +
                note_type_label(k),
            )
        with nc2:
            ref_key = st.text_input(t("nt.f_ref"),
                                     placeholder=t("nt.ref_ph"))
            priority = st.selectbox(
                t("nt.f_priority"),
                list(nt.PRIORITIES.keys()),
                format_func=note_priority_label,
            )
            pinned = st.checkbox(t("nt.f_pin"), value=False)
        body = st.text_area(t("nt.f_body"), placeholder="", height=80)
        if st.form_submit_button(t("nt.add_btn"), type="primary"):
            if note_title.strip():
                nt.add(
                    title=note_title.strip(),
                    body=body.strip(),
                    note_type=note_type,
                    ref_key=ref_key.strip(),
                    priority=priority,
                    pinned=pinned,
                )
                toast(t("nt.added"), icon="✓")
                st.rerun()

# ---- Filter -----------------------------------------------------------------
st.divider()
fc1, fc2 = st.columns(2)
with fc1:
    filter_type = st.selectbox(
        t("nt.f_filter"),
        ["all"] + list(nt.NOTE_TYPES.keys()),
        format_func=lambda k: ("🔍 " + t("nt.all_types")) if k == "all"
        else nt.NOTE_TYPES[k]["icon"] + " " + note_type_label(k),
        key="_nt_ft",
    )
with fc2:
    show_resolved = st.checkbox(t("nt.show_resolved"), value=False)

all_notes = nt.all_notes(
    note_type=None if filter_type == "all" else filter_type,
    include_resolved=show_resolved,
)

if not all_notes:
    st.info(t("nt.empty"))
    st.stop()

# ---- Notes list -------------------------------------------------------------
for note in all_notes:
    p_info = note["priority_info"]
    t_info = note["type_info"]
    pin_icon = "📌 " if note["pinned"] else ""

    st.markdown(
        "<div style='padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + p_info["color"] + ";"
        "border-radius:8px;background:white;margin-bottom:6px'>"
        "<div style='display:flex;justify-content:space-between;"
        "align-items:baseline;margin-bottom:4px'>"
        "<span>" + pin_icon + t_info["icon"] +
        " <strong>" + note["title"] + "</strong>"
        + (" · <span style='font-size:11px;color:#9a9485'>" +
           note["ref_key"] + "</span>" if note.get("ref_key") else "") +
        "</span>"
        "<span style='font-size:11px;color:" + p_info["color"] +
        ";font-weight:600'>" + note_priority_label(note.get("priority", "normal")) + " · " +
        (note.get("created_at") or "")[:10] + "</span></div>"
        + ("<div style='font-size:13px;color:#3d3530;white-space:pre-wrap'>" +
           (note.get("body") or "")[:200] + "</div>" if note.get("body") else "") +
        "</div>",
        unsafe_allow_html=True,
    )

    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        if not note.get("resolved") and st.button(
            t("nt.resolve_btn"), key="_res_" + str(note["id"]), type="tertiary"
        ):
            nt.resolve(note["id"])
            toast(t("nt.resolved"), icon="✓")
            st.rerun()
    with ac2:
        pin_label = t("nt.unpin_btn") if note["pinned"] else t("nt.pin_btn")
        if st.button(pin_label, key="_pin_" + str(note["id"]), type="tertiary"):
            nt.update(note["id"], pinned=not note["pinned"])
            st.rerun()
    with ac3:
        if st.button(t("nt.delete_btn"), key="_del_" + str(note["id"]),
                     type="tertiary"):
            nt.delete(note["id"])
            st.rerun()
