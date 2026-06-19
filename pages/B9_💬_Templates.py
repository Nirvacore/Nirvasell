"""Message Templates — quick reply for FB/Line/IG/TikTok."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import message_templates as mt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Templates",
                   page_icon="💬", layout="wide")
apply_theme()
require_auth()
db.init()
mt.init()
render_sidebar()

page_header(icon="💬", title=t("tmpl.title"), subtitle=t("tmpl.caption"))

s = mt.stats()
k1, k2 = st.columns(2)
with k1:
    metric_with_hint("📝 " + t("tmpl.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🔥 " + t("tmpl.kpi_uses"), str(s["total_uses"]),
                     hint="", hint_tone="ok")

# ---- Add new template -------------------------------------------------------
st.divider()
with st.expander(t("tmpl.add_title"), expanded=False):
    with st.form("add_tmpl"):
        tc1, tc2 = st.columns(2)
        with tc1:
            tmpl_title = st.text_input(t("tmpl.f_title"),
                                       placeholder=t("tmpl.title_ph"))
            category = st.selectbox(
                t("tmpl.f_category"),
                list(mt.CATEGORIES.keys()),
                format_func=lambda k: mt.CATEGORIES[k]["icon"] + " " +
                mt.CATEGORIES[k]["label"],
            )
        with tc2:
            platforms = st.selectbox(t("tmpl.f_platform"), mt.PLATFORMS)
            notes = st.text_input(t("tmpl.f_notes"), placeholder="")
        content = st.text_area(t("tmpl.f_content"),
                               placeholder=t("tmpl.content_ph"),
                               height=100)
        st.caption(t("tmpl.vars_hint"))
        if st.form_submit_button(t("tmpl.add_btn"), type="primary"):
            if tmpl_title.strip() and content.strip():
                mt.add(category, tmpl_title.strip(),
                       content.strip(), platforms, notes.strip())
                toast(t("tmpl.added"), icon="✓")
                st.rerun()

# ---- Filter -----------------------------------------------------------------
st.divider()
fc1, fc2 = st.columns(2)
with fc1:
    filter_cat = st.selectbox(
        t("tmpl.f_filter_cat"),
        ["all"] + list(mt.CATEGORIES.keys()),
        format_func=lambda k: ("🔍 " + t("tmpl.all_cats")) if k == "all"
        else mt.CATEGORIES[k]["icon"] + " " + mt.CATEGORIES[k]["label"],
    )
with fc2:
    filter_platform = st.selectbox(
        t("tmpl.f_filter_platform"),
        ["all"] + mt.PLATFORMS,
        format_func=lambda x: ("🔍 " + t("tmpl.all_platforms")) if x == "all" else x,
    )

templates = mt.all_templates(
    category=None if filter_cat == "all" else filter_cat,
    platform=None if filter_platform == "all" else filter_platform,
)

if not templates:
    st.info(t("tmpl.empty"))
    st.stop()

# ---- List -------------------------------------------------------------------
for tmpl in templates:
    cat_info = tmpl["category_info"]
    st.markdown(
        "<div style='padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-radius:8px;background:white;margin-bottom:6px'>"
        "<div style='display:flex;justify-content:space-between;margin-bottom:4px'>"
        "<span>" + cat_info["icon"] + " <strong>" + tmpl["title"] + "</strong>"
        " <span style='font-size:11px;color:#9a9485;margin-left:6px'>"
        + tmpl["platforms"] + "</span></span>"
        "<span style='font-size:11px;color:#9a9485'>" +
        t("common.used_times", n=tmpl["use_count"]) + "</span></div>"
        "<div style='font-size:13px;color:#3d3530;white-space:pre-wrap'>"
        + tmpl["content"][:200] +
        ("..." if len(tmpl["content"]) > 200 else "") + "</div></div>",
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        if st.button(t("tmpl.copy_btn"), key="_copy_" + str(tmpl["id"]),
                     type="tertiary"):
            content_text = mt.use(tmpl["id"])
            st.code(content_text, language=None)
    with col_b:
        with st.expander(t("tmpl.edit_btn"), expanded=False):
            new_content = st.text_area(
                "content",
                value=tmpl["content"],
                key="_edit_" + str(tmpl["id"]),
                label_visibility="collapsed",
            )
            if st.button(t("tmpl.save_btn"),
                         key="_esave_" + str(tmpl["id"])):
                mt.update(tmpl["id"], content=new_content)
                toast(t("tmpl.saved"), icon="✓")
                st.rerun()
    with col_c:
        if st.button(t("tmpl.delete_btn"),
                     key="_del_" + str(tmpl["id"]),
                     type="tertiary"):
            mt.delete(tmpl["id"])
            st.rerun()
