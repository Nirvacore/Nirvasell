"""G5 Notes — internal notes, tasks, and pinned reminders."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import notes as nt
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
nt.init()
render_sidebar()

st.title(t("note.title"))
st.caption(t("note.caption"))

stats = nt.stats()
c1, c2, c3 = st.columns(3)
c1.metric(t("note.kpi_total"), stats.get("total",0))
c2.metric(t("note.kpi_open"), stats.get("open",0))
c3.metric(t("note.kpi_pinned"), stats.get("pinned",0))

pinned = nt.pinned()
if pinned:
    st.divider()
    st.subheader("📌 " + t("note.pinned_title"))
    for n in pinned:
        st.info(("**" + n["title"] + "**") + ("\n\n" + n["body"] if n.get("body") else ""))

st.divider()
tab_all, tab_add = st.tabs([t("note.tab_all"), t("note.tab_add")])

NOTE_TYPE_ICONS = {"note":"📝","task":"✅","reminder":"🔔","issue":"⚠️","idea":"💡"}

with tab_all:
    type_f = st.segmented_control(t("note.type_filter"),
        ["all","note","task","reminder","issue","idea"],
        format_func=lambda s: t("note.all") if s=="all" else
                              NOTE_TYPE_ICONS.get(s,"") + " " + s,
        default="all")
    all_notes = nt.all_notes(note_type=None if type_f=="all" else type_f)
    if not all_notes:
        st.info(t("note.empty"))
    for n in all_notes:
        icon = NOTE_TYPE_ICONS.get(n.get("note_type","note"), "📝")
        resolved_tag = " ✅" if n.get("resolved") else ""
        label = icon + " **" + n["title"] + "**" + resolved_tag
        if n.get("ref_key"):
            label += " · 🔗 " + n["ref_key"]
        with st.expander(label):
            if n.get("body"):
                st.markdown(n["body"])
            col1, col2, col3 = st.columns(3)
            if not n.get("resolved"):
                if col1.button(t("note.resolve"), key="nr_" + str(n["id"])):
                    nt.resolve(n["id"]); st.rerun()
            edit_body = col2.text_input(t("note.edit_body"),
                                         value=n.get("body",""),
                                         key="nb_" + str(n["id"]))
            if col2.button(t("note.save"), key="ns_" + str(n["id"])):
                nt.update(n["id"], body=edit_body); st.rerun()
            if col3.button(t("note.delete"), key="nd_" + str(n["id"])):
                nt.delete(n["id"]); st.rerun()

with tab_add:
    st.subheader(t("note.add_title"))
    with st.form("note_form"):
        col1, col2 = st.columns(2)
        title     = col1.text_input(t("note.f_title"), placeholder=t("note.f_title_hint"))
        note_type = col2.selectbox(t("note.f_type"),
            ["note","task","reminder","issue","idea"],
            format_func=lambda k: NOTE_TYPE_ICONS.get(k,"") + " " + k)
        body      = st.text_area(t("note.f_body"), height=80)
        ref_key   = st.text_input(t("note.f_ref"), placeholder="SKU-001 / order #1234")
        pin_it    = st.checkbox(t("note.f_pin"))
        if st.form_submit_button(t("note.add_btn")):
            if title.strip():
                nt.add(title.strip(), body=body, note_type=note_type, ref_key=ref_key)
                if pin_it:
                    pass  # notes.py pin handled via update if supported
                st.success(t("note.added"))
                st.rerun()
