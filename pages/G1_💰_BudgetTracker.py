"""G1 Budget Tracker — set monthly limits, see what's over."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import budget_tracker as bt
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import budget_category
from sidebar import render_sidebar
from datetime import datetime

apply_theme()
require_auth()
bt.init()
render_sidebar()

st.title(t("bgt.title"))
st.caption(t("bgt.caption"))

month = st.text_input(t("bgt.month"), value=datetime.now().strftime("%Y-%m"),
                      placeholder=t("common.month_ph"))
summary = bt.summary(month=month.strip())

c1, c2, c3 = st.columns(3)
c1.metric(t("bgt.kpi_total_budget"), "฿{:,.0f}".format(summary.get("total_budget",0)))
c2.metric(t("bgt.kpi_actual"), "฿{:,.0f}".format(summary.get("total_actual",0)))
over = summary.get("categories_over_budget", 0)
c3.metric(t("bgt.kpi_over"), over, delta_color="inverse" if over > 0 else "off")

if over > 0:
    st.warning("⚠️ " + str(over) + t("bgt.over_warning"))

st.divider()
tab_overview, tab_set = st.tabs([t("bgt.tab_overview"), t("bgt.tab_set")])

with tab_overview:
    details = bt.budget_vs_actual(month=month.strip())
    if not details:
        st.info(t("bgt.empty"))
    else:
        for d in details:
            cat_info = bt.CATEGORIES.get(d["category"], {})
            icon  = cat_info.get("icon","📋")
            label_cat = budget_category(d["category"])
            limit = d.get("monthly_limit",0)
            actual = d.get("actual",0)
            pct = round(actual / limit * 100, 0) if limit > 0 else 0
            alert_pct = d.get("alert_pct", 80)
            bar_color = "#c54c4c" if pct > 100 else ("#c5963d" if pct > alert_pct else "#4d6c5c")
            bar_w = min(int(pct * 2), 220)
            row_html = (
                "<div style='margin:5px 0'>"
                "<div style='font-size:0.85rem'>"
                "<span style='width:180px;display:inline-block'>" + icon + " " + label_cat + "</span>"
                "<span style='color:#9a9485'>฿{:,.0f}".format(actual) +
                " / ฿{:,.0f}".format(limit) + "</span>"
                "</div>"
                "<div style='display:flex;align-items:center;gap:6px;margin-top:2px'>"
                "<div style='background:" + bar_color + ";width:" + str(bar_w) + "px;height:8px'></div>"
                "<span style='font-size:0.78rem;color:" + bar_color + "'>" + str(int(pct)) + "%</span>"
                "</div></div>"
            )
            st.html(row_html)

with tab_set:
    st.subheader(t("bgt.set_title"))
    existing = {b["category"]: b for b in bt.all_budgets()}
    with st.form("budget_form"):
        updates = {}
        for cat, info in bt.CATEGORIES.items():
            curr = existing.get(cat, {})
            col1, col2, col3 = st.columns([2,2,1])
            col1.write(info["icon"] + " " + budget_category(cat))
            limit = col2.number_input(t("bgt.f_limit"),
                                       value=float(curr.get("monthly_limit",0)),
                                       min_value=0.0, step=100.0,
                                       key="bl_" + cat)
            alert_pct = col3.number_input(t("bgt.f_alert"),
                                           value=float(curr.get("alert_pct",80)),
                                           min_value=0.0, max_value=100.0,
                                           key="ba_" + cat)
            updates[cat] = {"limit": limit, "alert_pct": alert_pct}
        if st.form_submit_button(t("bgt.save_btn")):
            for cat, vals in updates.items():
                if vals["limit"] > 0:
                    bt.set_budget(cat, vals["limit"], vals["alert_pct"])
            st.success(t("bgt.saved"))
            st.rerun()
