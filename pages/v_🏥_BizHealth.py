"""Business Health — one score to rule them all.

8 dimensions aggregated into 0-100 score. The CEO dashboard."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import biz_health as bh
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header
from i18n import t

st.set_page_config(page_title="nirva.sell · Business Health",
                   page_icon="🏥", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🏥", title=t("bh.title"), subtitle=t("bh.caption"))

result = bh.calculate()
score = result["overall"]
grade = result["grade"]
status = result["status"]


# ---- Hero score -------------------------------------------------------------

grade_color = {"A": "#4d6c5c", "B": "#4a7ab5", "C": "#c5963d", "D": "#c54c4c"}.get(grade, "#7a7569")
status_label = t("bh.status_" + status)

st.markdown(
    "<div style='text-align:center;padding:32px;background:rgba(77,108,92,0.04);"
    "border-radius:16px;margin-bottom:20px'>"
    "<div style='font-size:4rem;font-weight:700;color:" + grade_color + "'>"
    + str(int(score)) + "</div>"
    "<div style='font-size:1.5rem;font-weight:600;color:" + grade_color + "'>"
    + t("bh.grade_label", grade=grade) + "</div>"
    "<div style='color:#7a7569;font-size:14px;margin-top:6px'>"
    + status_label + "</div></div>",
    unsafe_allow_html=True,
)


# ---- 8 dimension cards ------------------------------------------------------

st.divider()
st.markdown("### " + t("bh.dimensions_title"))

details = bh.dimension_details()

# Show weakest first (already sorted by score ascending)
for d in details:
    ds = d["score"]
    d_color = "#4d6c5c" if ds >= 80 else ("#4a7ab5" if ds >= 60 else ("#c5963d" if ds >= 40 else "#c54c4c"))
    status_icon = {"excellent": "🟢", "good": "🔵", "needs_work": "🟡", "critical": "🔴"}.get(d["status"], "?")

    bar_width = max(ds, 2)
    weight_str = str(d["weight"]) + "%"

    st.markdown(
        "<div style='padding:12px 16px;margin-bottom:6px;background:white;"
        "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px;"
        "border-left:4px solid " + d_color + "'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline;"
        "margin-bottom:6px'>"
        "<span>" + status_icon + " " + d["icon"] + " <strong>" +
        t("bh.dim_" + d["key"]) + "</strong>"
        " <span style='color:#9a9485;font-size:11px'>(" + weight_str + ")</span></span>"
        "<span style='font-size:1.2rem;font-weight:600;color:" + d_color + "'>"
        + str(int(ds)) + "/100</span></div>"
        "<div style='background:rgba(40,30,20,0.06);border-radius:4px;height:8px;"
        "overflow:hidden'>"
        "<div style='width:" + str(int(bar_width)) + "%;height:100%;background:" + d_color + ";"
        "border-radius:4px;transition:width 0.3s'></div>"
        "</div></div>",
        unsafe_allow_html=True,
    )


# ---- Action items (weakest dimensions) --------------------------------------

weak = [d for d in details if d["score"] < 60]
if weak:
    st.divider()
    st.markdown("### 🎯 " + t("bh.action_title"))
    st.caption(t("bh.action_help"))

    for d in weak[:3]:
        d_color = "#c5963d" if d["score"] >= 40 else "#c54c4c"
        st.markdown(
            "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
            "border-left:3px solid " + d_color + "'>"
            + d["icon"] + " <strong>" + t("bh.dim_" + d["key"]) + "</strong>"
            " — " + str(int(d["score"])) + "/100"
            " — " + t("bh.fix_" + d["key"]) + "</div>",
            unsafe_allow_html=True,
        )
