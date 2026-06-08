"""RFM Segmentation — the gold standard of customer intelligence.

9 segments based on Recency × Frequency × Monetary. Every world-class
e-commerce uses RFM to decide where to spend marketing budget."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import customers as cust
import rfm
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · RFM",
                   page_icon="🎯", layout="wide")
apply_theme()
require_auth()
db.init()
cust.init()
render_sidebar()

page_header(icon="🎯", title=t("rfm.title"), subtitle=t("rfm.caption"))


# ---- Segment overview --------------------------------------------------------

segments = rfm.segment_summary()
total_customers = sum(s["count"] for s in segments)

if total_customers == 0:
    st.info(t("rfm.empty"))
    st.caption(t("rfm.empty_hint"))
    st.stop()

st.markdown("### " + t("rfm.overview"))

# Segment cards in grid
cols_per_row = 3
for row_start in range(0, len(segments), cols_per_row):
    cols = st.columns(cols_per_row)
    for i, seg in enumerate(segments[row_start:row_start + cols_per_row]):
        with cols[i]:
            pct = round(seg["count"] / total_customers * 100, 0) if total_customers else 0
            rev_str = "{:,.0f}".format(seg["revenue"])

            st.markdown(
                "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
                "border-left:4px solid " + seg["color"] + ";border-radius:10px;"
                "padding:14px 16px;margin-bottom:8px;min-height:100px'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                "<span style='font-size:14px;font-weight:600'>" +
                seg["icon"] + " " + seg["label"] + "</span>"
                "<span style='font-size:1.3rem;font-weight:600;color:" + seg["color"] + "'>" +
                str(seg["count"]) + "</span></div>"
                "<div style='color:#9a9485;font-size:12px;margin-top:6px'>"
                + str(int(pct)) + "% · ฿" + rev_str +
                "</div>"
                "<div style='margin-top:6px'>"
                "<span style='background:rgba(77,108,92,0.08);padding:2px 8px;"
                "border-radius:6px;font-size:11px;color:#4d6c5c'>"
                "→ " + t("rfm.action_" + seg["action"]) + "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )


# ---- Segment detail drill-down -----------------------------------------------

st.divider()
st.markdown("### " + t("rfm.drill_title"))

seg_options = [(s["segment"], s["icon"] + " " + s["label"] + " (" + str(s["count"]) + ")")
               for s in segments if s["count"] > 0]

if seg_options:
    selected_seg = st.selectbox(
        t("rfm.select_segment"),
        [s[0] for s in seg_options],
        format_func=lambda k: next(s[1] for s in seg_options if s[0] == k),
    )

    customers_in = rfm.customers_in_segment(selected_seg)
    seg_info = rfm.SEGMENTS.get(selected_seg, {})

    st.caption(t("rfm.action_hint") + ": " + t("rfm.action_" + seg_info.get("action", "engage")))

    for c in customers_in:
        rfm_str = str(c["r_score"]) + "-" + str(c["f_score"]) + "-" + str(c["m_score"])
        spent_str = "{:,.0f}".format(c["monetary"])
        days_str = str(c["recency_days"]) + "d"

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>"
            "<span style='font-weight:600'>" + c["segment_icon"] + " " + c["name"] + "</span>"
            " <span style='color:#9a9485;font-size:11px'>" +
            (c.get("phone") or c.get("email") or "") + "</span>"
            "</div>"
            "<div style='display:flex;gap:14px;align-items:center;font-size:12px'>"
            "<span style='background:rgba(40,30,20,0.04);padding:2px 8px;"
            "border-radius:6px;font-family:monospace'>RFM " + rfm_str + "</span>"
            "<span>📅 " + days_str + "</span>"
            "<span>📦 " + str(c["frequency"]) + "x</span>"
            "<span style='font-weight:600;color:" + c["segment_color"] + "'>฿" + spent_str + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


# ---- RFM explanation ---------------------------------------------------------

st.divider()
with st.expander("📖 " + t("rfm.explain_title"), expanded=False):
    st.markdown(t("rfm.explain_body"))
