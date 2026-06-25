"""Admin — manage user accounts. Admin role only."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import auth
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from i18n_inline import oauth_provider_label, oauth_setup_hint
from _components import page_header

st.set_page_config(page_title="nirva.sell · Admin", page_icon="👑", layout="wide")
apply_theme()
require_auth()
render_sidebar()

if not auth.is_admin():
    st.error(t("admin.not_authorized"))
    st.caption(t("admin.not_authorized_hint"))
    st.stop()

page_header(icon="👑", title=t("admin.title"), subtitle=t("admin.caption"))


# ---- User list -----------------------------------------------------------

users = auth.list_users()

m1, m2, m3 = st.columns(3)
m1.metric(t("admin.total_users"), len(users))
m2.metric(t("admin.admins"), sum(1 for u in users if u.get("role") == "admin"))
m3.metric(t("admin.total_data_mb"), f"{sum(auth.user_db_size(u['id']) for u in users) / 1024 / 1024:.2f}")


rows = []
for u in users:
    rows.append({
        "id": u["id"],
        "email": u["email"],
        "name": u.get("display_name") or "",
        "role": u.get("role") or "user",
        "created": (u.get("created_at") or "")[:16],
        "last_login": (u.get("last_login") or "—")[:16],
        "data_kb": auth.user_db_size(u["id"]) // 1024,
    })
df = pd.DataFrame(rows)

st.dataframe(
    df,
    width='stretch',
    hide_index=True,
    column_config={
        "id":         st.column_config.NumberColumn(width="small"),
        "data_kb":    st.column_config.NumberColumn("data (KB)", format="%d"),
    },
)


# ---- Per-user actions ----------------------------------------------------

st.divider()
st.markdown(f"### {t('admin.actions_title')}")

if not users:
    st.info(t("admin.no_users"))
    st.stop()

picked_id = st.selectbox(
    t("admin.pick_user"),
    [u["id"] for u in users],
    format_func=lambda i: next(
        (f"#{u['id']} · {u['email']} ({u.get('role','user')})"
         for u in users if u["id"] == i),
        str(i),
    ),
)
picked = next(u for u in users if u["id"] == picked_id)
me = auth.current_user()
is_self = me and me["id"] == picked_id


c1, c2, c3 = st.columns(3)

# Action 1 — promote/demote
with c1:
    current_role = picked.get("role") or "user"
    new_role = "user" if current_role == "admin" else "admin"
    if st.button(
        t("admin.set_role", role=new_role),
        width='stretch',
        disabled=is_self,
    ):
        if auth.set_role(picked_id, new_role):
            st.success(t("admin.role_changed"))
            st.rerun()
        else:
            st.error(t("admin.action_failed"))

# Action 2 — reset password
with c2:
    with st.popover(t("admin.reset_pw_btn"), width='stretch'):
        new_pw = st.text_input(t("auth.password"), type="password", key=f"reset_pw_{picked_id}")
        if st.button(t("admin.reset_pw_confirm"), key=f"reset_confirm_{picked_id}"):
            ok, msg = auth.reset_password(picked_id, new_pw)
            if ok:
                st.success(t("admin.reset_pw_ok", email=picked["email"]))
            else:
                st.error(msg)

# Action 3 — delete
with c3:
    with st.popover(t("admin.delete_btn"), width='stretch'):
        st.warning(t("admin.delete_warning", email=picked["email"]))
        _del_word = t("common.delete_confirm_word")
        confirm = st.text_input(
            t("admin.delete_confirm_prompt"),
            placeholder=_del_word,
            key=f"del_confirm_{picked_id}",
        )
        if st.button(
            t("admin.delete_confirm"),
            type="primary",
            disabled=confirm != _del_word or is_self,
            key=f"del_btn_{picked_id}",
        ):
            ok, msg = auth.delete_user(picked_id)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

if is_self:
    st.caption(t("admin.self_action_note"))


# ---- Social OAuth provider setup (v30) -----------------------------------

st.divider()
st.markdown(f"### {t('admin.oauth_title')}")
st.caption(t("admin.oauth_caption"))

import oauth as _oauth
import os as _os

# Show the callback URL the admin needs to paste into each provider's
# console. This is the single piece every provider asks for.
_callback_base = _os.getenv("APP_URL", "") or "http://localhost:8501"
st.code(f"{_callback_base.rstrip('/')}/", language=None)
st.caption(t("admin.oauth_callback_hint"))

for _key, _meta in _oauth.PROVIDERS.items():
    _cfg = _oauth.get_config(_key)
    _is_set = bool(_cfg["client_id"] and _cfg["client_secret"])
    _badge = "✅" if _is_set else "⚪"
    with st.expander(f"{_badge} {_meta['icon']} {oauth_provider_label(_key)}"):
        st.caption(oauth_setup_hint(_key))
        st.markdown(f"📖 [{t('admin.oauth_setup_console')}]({_meta['setup_url']})")
        with st.form(f"oauth_form_{_key}"):
            _cid = st.text_input(
                "Client ID",
                value=_cfg["client_id"], key=f"oauth_cid_{_key}",
                type="default",
            )
            _csec = st.text_input(
                "Client Secret",
                value=_cfg["client_secret"], key=f"oauth_csec_{_key}",
                type="password",
            )
            _c1, _c2 = st.columns([1, 1])
            with _c1:
                if st.form_submit_button(t("common.save"), type="primary"):
                    _oauth.set_config(_key, _cid, _csec)
                    st.success(t("admin.oauth_saved"))
                    st.rerun()
            with _c2:
                if _is_set and st.form_submit_button(t("admin.oauth_clear")):
                    _oauth.set_config(_key, "", "")
                    st.rerun()
