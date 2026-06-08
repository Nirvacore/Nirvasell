"""Slip Verifier — Thai home seller's anti-fraud tool.

Upload a transfer slip → Claude Vision reads amount, date, bank, sender,
flags suspicious markers. Optional: enter the amount you expect and we
diff it.

Designed for one-screen, one-upload, one-answer. No nav, no jargon — for
home sellers who never want to learn a dashboard."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import slip_verify
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, friendly_error
from i18n import t

st.set_page_config(page_title="nirva.sell · Slip Verifier",
                   page_icon="📱", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📱", title=t("slip.title"), subtitle=t("slip.caption"))

# ---- API key gate ------------------------------------------------------
api_key = st.session_state.get("api_key", "")
if not api_key:
    st.warning(t("generate.api_warn"))
    st.stop()


# ---- Upload + expected amount -----------------------------------------
c1, c2 = st.columns([3, 2])
with c1:
    uploaded = st.file_uploader(
        t("slip.upload_label"),
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        help=t("slip.upload_help"),
    )
with c2:
    expected = st.number_input(
        t("slip.expected_amount"),
        min_value=0.0, value=0.0, step=10.0,
        help=t("slip.expected_help"),
    )

if not uploaded:
    st.markdown(
        f"<div style='margin-top:14px;color:#7a7569;font-size:13px;"
        f"line-height:1.7;max-width:680px'>"
        f"💡 <strong>{t('slip.tip_title')}</strong><br/>"
        f"{t('slip.tip_body')}</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ---- Show the uploaded slip + run AI ----------------------------------
cI, cR = st.columns([1, 1])
with cI:
    st.image(uploaded, caption=uploaded.name, width='stretch')

with cR:
    with st.spinner(t("slip.checking")):
        try:
            mime = (uploaded.type or "image/jpeg").lower()
            report = slip_verify.verify(uploaded.getvalue(), api_key=api_key, mime=mime)
            if expected and expected > 0:
                report = slip_verify.check_against_expected(report, expected)
        except Exception as e:
            friendly_error(e, hint=t("slip.err_hint"))
            st.stop()

    # ---- Top banner — green/amber/red based on confidence + match ----
    conf = report["confidence"]
    match = report.get("matches_expected")
    suspicious = report.get("suspicious") or []

    if match is False:
        banner_color, banner_icon, banner_label = "#c54c4c", "🔴", t("slip.banner_mismatch")
    elif suspicious:
        banner_color, banner_icon, banner_label = "#c5963d", "⚠", t("slip.banner_suspicious")
    elif conf == "high":
        banner_color, banner_icon, banner_label = "#4d6c5c", "✅", t("slip.banner_ok")
    elif conf == "medium":
        banner_color, banner_icon, banner_label = "#c5963d", "🟡", t("slip.banner_medium")
    else:
        banner_color, banner_icon, banner_label = "#c54c4c", "🔴", t("slip.banner_low")

    st.markdown(
        f"<div style='background:rgba(0,0,0,0);border:2px solid {banner_color};"
        f"border-radius:12px;padding:14px 18px;margin-bottom:14px'>"
        f"<div style='font-size:18px;font-weight:600;color:{banner_color}'>"
        f"{banner_icon}  {banner_label}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---- Extracted fields table ---------------------------------------
    amt = report.get("amount")
    amt_display = f"฿{amt:,.2f}" if amt is not None else "—"
    rows = [
        (t("slip.f_amount"),  amt_display),
        (t("slip.f_date"),    report.get("date")    or "—"),
        (t("slip.f_bank"),    report.get("bank")    or "—"),
        (t("slip.f_sender"),  report.get("sender")  or "—"),
        (t("slip.f_recip"),   report.get("recipient") or "—"),
        (t("slip.f_ref"),     report.get("ref")     or "—"),
        (t("slip.f_conf"),    conf.upper()),
    ]
    for label, val in rows:
        cA, cB = st.columns([1, 2])
        cA.markdown(f"<div style='color:#7a7569;font-size:13px;padding:6px 0'>"
                    f"{label}</div>", unsafe_allow_html=True)
        cB.markdown(f"<div style='color:#1f1f1f;font-size:14px;font-weight:500;"
                    f"padding:6px 0'>{val}</div>", unsafe_allow_html=True)

    # ---- Expected match (if user gave a value) ------------------------
    if match is not None:
        match_icon = "✅" if match else "🔴"
        match_bg = "rgba(77,108,92,0.08)" if match else "rgba(197,76,76,0.08)"
        st.markdown(
            f"<div style='background:{match_bg};border-radius:8px;"
            f"padding:10px 14px;margin-top:8px;font-size:13px'>"
            f"{match_icon} {report.get('match_reason', '')}</div>",
            unsafe_allow_html=True,
        )

    # ---- Suspicious flags ---------------------------------------------
    if suspicious:
        st.markdown(f"### ⚠ {t('slip.suspicious_title')}")
        for s in suspicious:
            st.markdown(f"- {s}")

    # ---- Raw notes (collapsible) --------------------------------------
    if report.get("raw_notes"):
        with st.expander(t("slip.raw_notes_title"), expanded=False):
            st.write(report["raw_notes"])

    # ---- Log to events feed -------------------------------------------
    try:
        import events
        sev = ("error" if match is False else
               "warn" if suspicious else
               "success" if conf == "high" else "info")
        title = (f"{banner_icon} Slip {conf.upper()}"
                 + (f" · ฿{amt:,.2f}" if amt else ""))
        body = (f"Bank={report.get('bank') or '?'} · "
                f"Sender={report.get('sender') or '?'}")
        events.log(category="payment", severity=sev, title=title, body=body)
    except Exception:
        pass


st.divider()
st.caption(t("slip.disclaimer"))
