"""Notifications — configure where alerts go (email/telegram/line/webhook)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import notifier
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from i18n_inline import notif_kind_name
from _components import page_header

_NOTIF_KINDS = {
    "email": "notif.kind_email",
    "telegram": "notif.kind_telegram",
    "line": "notif.kind_line",
    "webhook": "notif.kind_webhook",
}

st.set_page_config(page_title="nirva.sell · Notifications", page_icon="🔔", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()
notifier.init()

page_header(icon="🔔", title=t("notif.title"), subtitle=t("notif.caption"))


# ---- Event preferences ---------------------------------------------------

import user_settings as us
prefs = us.notify_prefs()

st.markdown(f"### {t('notif.prefs_title')}")
st.caption(t("notif.prefs_help"))

c1, c2, c3, c4, c5 = st.columns(5)
new_prefs = {}
new_prefs["batch_done"] = c1.checkbox(t("notif.event_batch_done"), value=prefs["batch_done"])
new_prefs["policy_change"] = c2.checkbox(t("notif.event_policy_change"), value=prefs["policy_change"])
new_prefs["review_block"] = c3.checkbox(t("notif.event_review_block"), value=prefs["review_block"])
new_prefs["low_stock"] = c4.checkbox(t("notif.event_low_stock"), value=prefs["low_stock"])
new_prefs["import_done"] = c5.checkbox(t("notif.event_import_done"), value=prefs["import_done"])

if new_prefs != prefs:
    us.set_notify_prefs(new_prefs)
    st.toast(t("common.saved"))


st.divider()


# ---- Existing channels ---------------------------------------------------

channels = notifier.list_channels()

st.markdown(f"### {t('notif.existing_title')}")
if not channels:
    st.info(t("notif.no_channels"))
else:
    for ch in channels:
        disabled = t("notif.disabled_suffix") if not ch.get("enabled") else ""
        with st.expander(
            f"{['📧','💬','💚','🔗'][['email','telegram','line','webhook'].index(ch['kind'])]}"
            f"  {ch.get('name') or ch['kind']}"
            f"{disabled}",
            expanded=False,
        ):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button(t("notif.test_btn"), key=f"test_{ch['id']}"):
                    ok, msg = notifier.test_channel(ch["id"])
                    if ok:
                        st.success(t("notif.test_ok"))
                    else:
                        st.error(msg)
            with c2:
                if st.button(
                    t("notif.disable_btn") if ch.get("enabled") else t("notif.enable_btn"),
                    key=f"toggle_{ch['id']}",
                ):
                    notifier.update_channel(ch["id"], enabled=not ch.get("enabled"))
                    st.rerun()
            with c3:
                if st.button(t("notif.delete_btn"), key=f"del_{ch['id']}"):
                    notifier.delete_channel(ch["id"])
                    st.rerun()

            when = ch.get("last_used") or t("notif.never_used")
            st.caption(t("notif.last_used_line", id=ch["id"], when=when))
            with st.expander(t("notif.show_config")):
                # Mask secrets
                cfg = dict(ch.get("config", {}))
                for k in ("password", "bot_token", "token"):
                    if cfg.get(k):
                        cfg[k] = cfg[k][:4] + "•" * (max(len(cfg[k]) - 8, 0)) + cfg[k][-4:]
                st.json(cfg)


# ---- Add new channel -----------------------------------------------------

st.divider()
st.markdown(f"### {t('notif.add_title')}")

kind = st.radio(
    t("notif.kind_label"),
    ["email", "telegram", "line", "webhook"],
    format_func=lambda k: t(_NOTIF_KINDS[k]),
    horizontal=True,
)

with st.form(f"add_{kind}"):
    name = st.text_input(t("notif.channel_name"), placeholder=t("notif.channel_name_ph", kind=kind))
    config: dict = {}

    if kind == "email":
        st.caption(t("notif.email_help"))
        c1, c2 = st.columns(2)
        with c1:
            config["host"] = st.text_input(t("notif.smtp_host"), "smtp.gmail.com")
            config["user"] = st.text_input(t("notif.smtp_user"))
            config["to"] = st.text_input(t("notif.email_to"), help=t("notif.email_to_help"))
        with c2:
            config["port"] = st.number_input(t("notif.smtp_port"), value=587, step=1)
            config["password"] = st.text_input(t("notif.smtp_password"), type="password",
                                                 help=t("notif.smtp_password_help"))
            config["from"] = st.text_input(t("notif.email_from"), help=t("notif.email_from_help"))

    elif kind == "telegram":
        st.caption(t("notif.telegram_help"))
        config["bot_token"] = st.text_input(t("notif.bot_token"), type="password",
                                              help=t("notif.telegram_token_help"))
        config["chat_id"] = st.text_input(t("notif.chat_id"),
                                            help=t("notif.chat_id_help"))

    elif kind == "line":
        st.caption(t("notif.line_help"))
        config["token"] = st.text_input(t("notif.line_token"), type="password",
                                          help=t("notif.line_token_help"))

    elif kind == "webhook":
        st.caption(t("notif.webhook_help"))
        config["url"] = st.text_input(t("notif.webhook_url"),
                                        placeholder=t("notif.webhook_url_ph"))
        config["method"] = st.selectbox(t("notif.http_method"), ["POST", "PUT"])

    submitted = st.form_submit_button(t("notif.add_btn"), type="primary")
    if submitted:
        # Drop empty values
        clean = {k: v for k, v in config.items() if v not in ("", None)}
        if not clean:
            st.error(t("notif.config_empty"))
        else:
            cid = notifier.add_channel(kind, name or notif_kind_name(kind), clean)
            st.success(t("notif.added", id=cid))
            st.rerun()


# ---- Test from here ------------------------------------------------------

st.divider()
st.markdown(f"### {t('notif.broadcast_test')}")
c1, c2 = st.columns([1, 4])
with c1:
    if st.button(t("notif.send_test_all"), type="primary", width='stretch'):
        results = notifier.notify(
            t("notif.test_subject"),
            t("notif.test_body"),
        )
        for r in results:
            icon = "✅" if r["ok"] else "❌"
            st.write(f"{icon}  {r['kind']}  ·  {r.get('name', '')}  ·  {r['msg']}")
        if not results:
            st.info(t("notif.no_enabled"))
with c2:
    st.caption(t("notif.broadcast_hint"))
