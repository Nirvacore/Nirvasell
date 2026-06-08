"""F4 Smart Alerts — aggregated business signals across all modules."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import alerts as al
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
al.init()
render_sidebar()

st.title(t("alert.title"))
st.caption(t("alert.caption"))

with st.spinner(t("alert.loading")):
    active_alerts = al.check_all()
    alert_stats   = al.stats()

c1, c2 = st.columns(2)
c1.metric(t("alert.kpi_active"), len(active_alerts),
          delta_color="inverse" if active_alerts else "off")
c2.metric(t("alert.kpi_dismissed_today"), alert_stats.get("dismissed_today", 0))

st.divider()

tab_active, tab_configure = st.tabs([
    t("alert.tab_active"), t("alert.tab_configure")
])

with tab_active:
    if not active_alerts:
        st.success("✅ " + t("alert.all_clear"))
        st.caption(t("alert.all_clear_hint"))
    else:
        for a in active_alerts:
            col_msg, col_dismiss = st.columns([5,1])
            alert_html = (
                "<div style='padding:10px 14px;border-left:4px solid " +
                a["color"] + ";margin:6px 0;background:#1a1a1a'>"
                "<div style='font-size:0.95rem'>" +
                a["icon"] + " <b style='color:" + a["color"] + "'>" + a["label"] + "</b>"
                " — " + a["message"] + "</div>"
                + ("<div style='font-size:0.78rem;color:#9a9485;margin-top:4px'>" +
                   t("alert.action") + ": " + a["action"] + "</div>" if a.get("action") else "") +
                "</div>"
            )
            col_msg.html(alert_html)
            if col_dismiss.button(t("alert.dismiss_btn"), key="adis_" + a["key"]):
                al.dismiss(a["key"])
                st.rerun()

with tab_configure:
    st.subheader(t("alert.config_title"))
    cfg = al.get_config()
    with st.form("alert_config_form"):
        updates = {}
        for atype, info in al.ALERT_TYPES.items():
            current = cfg.get(atype, {})
            col1, col2, col3 = st.columns([2,2,1])
            col1.write(info["icon"] + " **" + info["label"] + "**")
            threshold = col2.number_input(
                t("alert.threshold"),
                value=float(current.get("threshold", info["default_threshold"])),
                min_value=0.0, step=1.0,
                key="thr_" + atype,
            )
            enabled = col3.checkbox(
                t("alert.enabled"),
                value=bool(current.get("enabled", 1)),
                key="en_" + atype,
            )
            updates[atype] = {"threshold": threshold, "enabled": enabled}
        if st.form_submit_button(t("alert.save_btn")):
            for atype, vals in updates.items():
                al.configure(atype, threshold=vals["threshold"],
                              enabled=vals["enabled"])
            st.success(t("alert.saved"))
            st.rerun()
