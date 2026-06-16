"""Compliance Center — public transparency page showing every standard
nirva.sell touches, what's in place, and what's intentionally NOT yet.

Honest beats hand-wavy. This page is the "trust the operator" floor that
lets a serious buyer evaluate us in 5 minutes instead of a 200-question
security questionnaire."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import auth
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _components import page_header
from i18n import t

st.set_page_config(page_title="nirva.sell · Compliance",
                   page_icon="🛡", layout="wide")
apply_theme()
# Intentionally PUBLIC — visible without auth so prospects + auditors can read it.
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


page_header(icon="🛡", title=t("comp.title"), subtitle=t("comp.caption"))

# ---- Hero — honest one-liner ------------------------------------------
st.markdown(
    "<div style='background:linear-gradient(135deg,rgba(77,108,92,0.06),"
    "rgba(77,108,92,0.02));border:1px solid rgba(77,108,92,0.15);"
    "border-radius:12px;padding:22px 24px;margin:6px 0 22px;"
    "font-family:Cormorant Garamond,serif;font-size:1.3rem;color:#1f1f1f;"
    "font-weight:500;line-height:1.5'>"
    f"📜 {t('comp.thesis')}"
    "</div>",
    unsafe_allow_html=True,
)

# ---- Link to Universal Compliance Graph ---------------------------------
try:
    from standards_kb.graph import Graph
    _g = Graph.load()
    _top = max(_g.controls, key=_g.reuse_factor)
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    with sc1:
        st.page_link(
            "pages/01_📚_Standards.py",
            label="📚 " + t("comp.standards_cta"),
            icon="📚",
        )
    with sc2:
        st.metric(t("skb.kpi_standards"), _g.summary()["standards"])
    with sc3:
        st.metric(
            t("comp.standards_reuse"),
            f"{_top} ×{_g.reuse_factor(_top)}",
        )
except Exception:
    pass

st.divider()

# ---- Standards table ---------------------------------------------------

STANDARDS = [
    # (key, status, controls_key, gaps_key)
    ("pdpa",       "ok",     "comp.pdpa_in",       "comp.pdpa_gap"),
    ("gdpr",       "ok",     "comp.gdpr_in",       "comp.gdpr_gap"),
    ("pci",        "ok",     "comp.pci_in",        "comp.pci_gap"),
    ("emvco",      "ok",     "comp.emvco_in",      "comp.emvco_gap"),
    ("mit",        "ok",     "comp.mit_in",        "comp.mit_gap"),
    ("iso27001",   "partial","comp.iso_in",        "comp.iso_gap"),
    ("soc2",       "partial","comp.soc_in",        "comp.soc_gap"),
    ("wcag",       "partial","comp.wcag_in",       "comp.wcag_gap"),
    ("eu_ai_act",  "gap",    "comp.aiact_in",      "comp.aiact_gap"),
    ("2fa_sso",    "gap",    "comp.2fa_in",        "comp.2fa_gap"),
]

ICONS = {"ok": "✅", "partial": "🟡", "gap": "🔴"}
LABELS = {"ok": "comp.status_ok", "partial": "comp.status_partial",
          "gap": "comp.status_gap"}

st.markdown(f"### {t('comp.matrix_title')}")
st.caption(t("comp.matrix_legend"))

for key, status, ctrl_key, gap_key in STANDARDS:
    icon = ICONS[status]
    name = t(f"comp.std_{key}")
    status_label = t(LABELS[status])
    status_color = {"ok": "#4d6c5c", "partial": "#c5963d", "gap": "#c54c4c"}[status]

    with st.expander(f"{icon}  **{name}**  ·  {status_label}",
                     expanded=False):
        cA, cB = st.columns(2)
        with cA:
            st.markdown(f"**{t('comp.in_place')}**")
            st.markdown(t(ctrl_key))
        with cB:
            st.markdown(f"**{t('comp.gaps')}**")
            st.markdown(t(gap_key))


# ---- Technical controls summary ---------------------------------------

st.divider()
st.markdown(f"### {t('comp.controls_title')}")
st.caption(t("comp.controls_caption"))

CONTROLS = [
    ("🔐", "comp.ctrl_pw",       "comp.ctrl_pw_d"),
    ("🛡", "comp.ctrl_rate",     "comp.ctrl_rate_d"),
    ("🔑", "comp.ctrl_hmac",     "comp.ctrl_hmac_d"),
    ("🔒", "comp.ctrl_https",    "comp.ctrl_https_d"),
    ("💾", "comp.ctrl_backup",   "comp.ctrl_backup_d"),
    ("📓", "comp.ctrl_log",      "comp.ctrl_log_d"),
    ("🗂", "comp.ctrl_isolation","comp.ctrl_isolation_d"),
    ("🔑", "comp.ctrl_byok",     "comp.ctrl_byok_d"),
]

ctrl_cols = st.columns(2)
for i, (icon, title_key, desc_key) in enumerate(CONTROLS):
    with ctrl_cols[i % 2]:
        st.markdown(
            f"<div style='background:white;border:1px solid rgba(40,30,20,0.06);"
            f"border-radius:10px;padding:14px 16px;margin-bottom:10px'>"
            f"<div style='font-size:13px;color:#4d6c5c;font-weight:600'>"
            f"{icon}  {t(title_key)}</div>"
            f"<div style='color:#6b6b6b;font-size:13px;margin-top:4px;"
            f"line-height:1.55'>{t(desc_key)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ---- Honesty footer ----------------------------------------------------
st.divider()
st.markdown(
    f"<div style='text-align:center;color:#9a9485;font-size:12px;"
    f"line-height:1.7;max-width:680px;margin:14px auto'>"
    f"{t('comp.honest_footer')}"
    f"</div>",
    unsafe_allow_html=True,
)
