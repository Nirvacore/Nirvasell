"""Terms of Service + Privacy Policy + Contact.

Public — readable WITHOUT logging in (the only such page). Admin sees an
'Edit' panel below to override the defaults per-deployment."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import legal
import auth
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from i18n import t, current_lang
from _components import page_header

st.set_page_config(page_title="nirva.sell · Legal", page_icon="📄", layout="wide")
apply_theme()
# NOTE: no require_auth() — this page is intentionally public.

# Sidebar render only makes sense once logged in; otherwise show a back-link.
if auth.is_authenticated():
    render_sidebar()
else:
    st.sidebar.markdown(
        "<div style='font-family:Inter,sans-serif;font-size:18px;"
        "font-weight:600;letter-spacing:-0.02em;margin:6px 0 14px'>"
        "nirva<span style='color:#4d6c5c'>.sell</span></div>",
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("app.py", label=f"← {t('legal.back_to_login')}")

lang = "th" if current_lang() == "th" else "en"

# ---- Tabs: ToS · Privacy · Contact -------------------------------------

page_header(icon="📄", title=t("legal.title"), subtitle=t("legal.caption"))

tab_tos, tab_priv, tab_contact = st.tabs([
    f"📜 {t('legal.tab_tos')}",
    f"🔒 {t('legal.tab_privacy')}",
    f"☎ {t('legal.tab_contact')}",
])

with tab_tos:
    st.markdown(legal.get_tos(lang))

with tab_priv:
    st.markdown(legal.get_privacy(lang))

with tab_contact:
    info = legal.get_contact()
    if any(info.values()):
        if info.get("company"):
            st.markdown(f"### {info['company']}")
        rows = []
        if info.get("email"):   rows.append(("📧 " + t('legal.email'), info["email"]))
        if info.get("line_id"): rows.append(("💚 LINE", info["line_id"]))
        if info.get("address"): rows.append(("📮 " + t('legal.address'), info["address"]))
        if info.get("tax_id"):  rows.append(("🧾 " + t('legal.tax_id'),  info["tax_id"]))
        for label, val in rows:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{label}**")
            c2.markdown(val)
    else:
        st.caption(t("legal.contact_not_set"))


# ---- Admin edit panel --------------------------------------------------

if auth.is_admin():
    st.divider()
    with st.expander(f"⚙ {t('legal.admin_title')}"):
        st.caption(t("legal.admin_help"))

        # ---- Contact info ----
        st.markdown(f"#### {t('legal.section_contact')}")
        info = legal.get_contact()
        with st.form("legal_contact"):
            c1, c2 = st.columns(2)
            with c1:
                new_company = st.text_input(t("legal.f_company"), value=info.get("company", ""))
                new_email = st.text_input(t("legal.f_email"), value=info.get("email", ""))
                new_line = st.text_input(t("legal.f_line"), value=info.get("line_id", ""))
            with c2:
                new_address = st.text_area(t("legal.f_address"), value=info.get("address", ""), height=90)
                new_tax = st.text_input(t("legal.f_tax_id"), value=info.get("tax_id", ""))
            if st.form_submit_button(t("common.save"), type="primary"):
                legal.set_contact(company=new_company, email=new_email,
                                  line_id=new_line, address=new_address, tax_id=new_tax)
                st.success(t("common.saved"))
                st.rerun()

        # ---- ToS / Privacy override ----
        st.markdown(f"#### {t('legal.section_text')}")
        ed_lang = st.radio(t("legal.edit_lang"), ["th", "en"], horizontal=True)
        ed_doc = st.radio(t("legal.edit_doc"),
                          ["tos", "privacy"], horizontal=True,
                          format_func=lambda k: t(f"legal.tab_{k}") if k == "tos" else t("legal.tab_privacy"))

        if ed_doc == "tos":
            current = legal.get_tos(ed_lang)
        else:
            current = legal.get_privacy(ed_lang)

        edited = st.text_area(t("legal.edit_text"), value=current, height=400)
        ec1, ec2 = st.columns([1, 4])
        with ec1:
            if st.button(t("common.save"), key="save_legal", type="primary"):
                if ed_doc == "tos":
                    legal.set_tos(ed_lang, edited)
                else:
                    legal.set_privacy(ed_lang, edited)
                st.success(t("common.saved"))
                st.rerun()
        with ec2:
            st.caption(t("legal.edit_hint"))
