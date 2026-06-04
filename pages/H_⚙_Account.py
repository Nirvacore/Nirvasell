"""Account settings — user-facing (not admin). Profile, password, data export, self-delete."""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import auth
import data_export
import db
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from _components import page_header

st.set_page_config(page_title="nirva.sell · Account", page_icon="⚙", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

u = auth.current_user()
page_header(icon="⚙", title=t("account.title"), subtitle=t("account.caption"))


# ---- Profile -------------------------------------------------------------

st.markdown(f"### {t('account.profile_title')}")
c1, c2 = st.columns(2)
with c1:
    st.text_input(t("auth.email"), u["email"], disabled=True)
    new_name = st.text_input(t("auth.display_name"), u.get("display_name") or "")
    if st.button(t("account.save_name_btn")):
        if auth.update_display_name(u["id"], new_name):
            # Refresh session
            ok, fresh = auth.login(u["email"], "")  # won't work; just refetch
            # Cleaner: directly update session state
            st.session_state["auth_user"]["display_name"] = new_name
            st.success(t("common.saved"))
            st.rerun()

with c2:
    st.text_input("Role", u.get("role") or "user", disabled=True)
    st.text_input("User ID", str(u["id"]), disabled=True)


# ---- Password ------------------------------------------------------------

st.divider()
st.markdown(f"### {t('account.password_title')}")
with st.form("change_password"):
    old_pw = st.text_input(t("account.old_password"), type="password")
    new_pw = st.text_input(t("account.new_password"), type="password", help=t("auth.password_help"))
    submitted = st.form_submit_button(t("account.change_pw_btn"), type="primary")
    if submitted:
        if not old_pw or not new_pw:
            st.error(t("account.both_fields_required"))
        else:
            ok, msg = auth.change_password(u["id"], old_pw, new_pw)
            if ok:
                st.success(t("account.pw_changed"))
            else:
                st.error(msg)


# ---- Data export ---------------------------------------------------------

st.divider()
st.markdown(f"### {t('account.export_title')}")
st.caption(t("account.export_help"))

c1, c2 = st.columns([1, 4])
with c1:
    size_b = data_export.export_size_estimate(u["id"])
    if size_b == 0:
        st.caption(t("account.export_no_data"))
    else:
        if st.button(t("account.export_btn"), type="primary", width='stretch'):
            with st.spinner(t("account.exporting")):
                blob = data_export.export_user(u)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                t("account.export_dl", size=len(blob) // 1024),
                data=blob,
                file_name=f"nirva_{u['email'].split('@')[0]}_{ts}.zip",
                mime="application/zip",
                width='stretch',
            )

with c2:
    st.caption(f"💾 ขนาดประมาณ: {size_b / 1024:.1f} KB")


# ---- Danger zone — delete own account ------------------------------------

st.divider()
with st.expander(f"⚠ {t('account.danger_title')}"):
    st.warning(t("account.delete_warning"))
    confirm = st.text_input(
        t("admin.delete_confirm_prompt"),
        placeholder="DELETE",
        key="self_delete_confirm",
    )
    if st.button(
        t("account.delete_self_btn"),
        type="primary",
        disabled=confirm != "DELETE",
    ):
        ok, msg = auth.delete_user(u["id"])
        if ok:
            auth.logout()
            st.success(t("account.deleted_ok"))
            st.rerun()
        else:
            st.error(msg)
