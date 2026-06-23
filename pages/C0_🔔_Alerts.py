"""Smart Alerts — aggregated business signals from all modules."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import alerts
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import alert_kind_name

st.set_page_config(page_title="nirva.sell · Alerts",
                   page_icon="🔔", layout="wide")
apply_theme()
require_auth()
db.init()
alerts.init()
render_sidebar()

page_header(icon="🔔", title=t("alrt.title"), subtitle=t("alrt.caption"))

active_alerts = alerts.check_all()
critical = [a for a in active_alerts if a["color"] == "#c54c4c"]
warnings = [a for a in active_alerts if a["color"] != "#c54c4c"]

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("🚨 " + t("alrt.kpi_active"), str(len(active_alerts)),
                     hint="", hint_tone="danger" if active_alerts else "ok")
with k2:
    metric_with_hint("🔴 " + t("alrt.kpi_critical"), str(len(critical)),
                     hint="", hint_tone="danger" if critical else "ok")
with k3:
    metric_with_hint("🟡 " + t("alrt.kpi_warnings"), str(len(warnings)),
                     hint="", hint_tone="warn" if warnings else "ok")

st.divider()

if not active_alerts:
    st.success("✅ " + t("alrt.all_clear"))
else:
    st.markdown("### " + t("alrt.active_title"))
    for alrt in active_alerts:
        st.markdown(
            "<div style='padding:12px 16px;margin-bottom:6px;"
            "border-left:4px solid " + alrt["color"] + ";"
            "background:white;border-radius:0 8px 8px 0;"
            "border:0.5px solid rgba(40,30,20,0.07);"
            "border-left:4px solid " + alrt["color"] + "'>"
            "<div style='display:flex;justify-content:space-between;"
            "align-items:center'>"
            "<span>" + alrt["icon"] + " <strong>" +
            alrt["label"] + "</strong>"
            " · <span style='font-size:13px'>" + alrt["message"] + "</span></span>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        if st.button(t("alrt.dismiss_btn"), key="_dismiss_" + alrt["key"],
                     type="tertiary"):
            alerts.dismiss(alrt["key"])
            toast(t("alrt.dismissed"), icon="✓")
            st.rerun()

# ---- Configure alerts -------------------------------------------------------
st.divider()
st.markdown("### ⚙️ " + t("alrt.configure_title"))

cfg = alerts.get_config()
with st.form("alert_config"):
    for atype, info in alerts.ALERT_TYPES.items():
        c1, c2, c3 = st.columns(3)
        row_cfg = cfg.get(atype, {})
        with c1:
            st.markdown(
                "<div style='padding-top:8px'>" + info["icon"] +
                " <strong>" + alert_kind_name(atype) + "</strong></div>",
                unsafe_allow_html=True,
            )
        with c2:
            enabled = st.checkbox(
                t("alrt.f_enabled"),
                value=bool(row_cfg.get("enabled", 1)),
                key="_alrt_en_" + atype,
            )
        with c3:
            if info.get("default_threshold", 0) > 0:
                threshold = st.number_input(
                    t("alrt.f_threshold"),
                    min_value=0.0,
                    value=float(row_cfg.get("threshold") or info["default_threshold"]),
                    step=1.0,
                    key="_alrt_th_" + atype,
                    label_visibility="collapsed",
                )
            else:
                threshold = 0
                st.markdown(
                    "<div style='padding-top:24px;font-size:12px;color:#9a9485'>"
                    "—</div>",
                    unsafe_allow_html=True,
                )
    if st.form_submit_button(t("alrt.save_config_btn"), type="primary"):
        for atype in alerts.ALERT_TYPES:
            info = alerts.ALERT_TYPES[atype]
            en_val = st.session_state.get("_alrt_en_" + atype, True)
            th_val = st.session_state.get("_alrt_th_" + atype,
                                           info.get("default_threshold", 0))
            alerts.configure(atype, threshold=th_val, enabled=en_val)
        toast(t("alrt.config_saved"), icon="✓")
        st.rerun()
