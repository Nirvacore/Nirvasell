"""D8 Expense Tracker — log and analyze business costs."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import expenses as ex
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import expense_category
from sidebar import render_sidebar
from datetime import datetime

apply_theme()
require_auth()
ex.init()
render_sidebar()

st.title(t("exp.title"))
st.caption(t("exp.caption"))

stats = ex.stats()
c1, c2, c3 = st.columns(3)
c1.metric(t("exp.kpi_this_month"), "฿{:,.0f}".format(stats["this_month"]))
c2.metric(t("exp.kpi_last_month"), "฿{:,.0f}".format(stats["last_month"]))
delta_val = str(stats["change_pct"]) + "%"
c3.metric(t("exp.kpi_change"), delta_val,
          delta=delta_val,
          delta_color="inverse" if stats["change_pct"] > 0 else "normal")

st.divider()

tab_log, tab_list, tab_chart = st.tabs([
    t("exp.tab_log"), t("exp.tab_list"), t("exp.tab_chart")
])

with tab_log:
    st.subheader(t("exp.log_title"))
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        category = col1.selectbox(
            t("exp.f_category"),
            ex.CATEGORIES,
            format_func=lambda c: ex.CATEGORY_ICONS.get(c, "") + " " +
            expense_category(c),
        )
        amount   = col2.number_input(t("exp.f_amount"), min_value=0.0, step=10.0)
        col3, col4 = st.columns(2)
        exp_date = col3.text_input(t("exp.f_date"),
                                    value=datetime.now().strftime("%Y-%m-%d"))
        platform = col4.text_input(t("exp.f_platform"), placeholder=t("exp.platform_ph"))
        note     = st.text_input(t("exp.f_note"))
        if st.form_submit_button(t("exp.log_btn")):
            if amount > 0:
                ex.add(date=exp_date, category=category,
                       amount=amount, note=note, platform=platform)
                st.success(t("exp.logged"))
                st.rerun()

with tab_list:
    month_sel = st.text_input(t("exp.f_month_filter"),
                               value=datetime.now().strftime("%Y-%m"),
                               placeholder=t("common.month_ph"))
    expenses = ex.all_expenses(month=month_sel.strip())
    if not expenses:
        st.info(t("exp.empty"))
    else:
        for e in expenses:
            icon = ex.CATEGORY_ICONS.get(e["category"], "📋")
            label = t("exp.list_line",
                      icon=icon,
                      date=e.get("date", ""),
                      category=expense_category(e["category"]),
                      amount="{:,.0f}".format(e["amount"]))
            if e.get("note"):
                label += " · " + e["note"]
            col_l, col_d = st.columns([5,1])
            col_l.write(label)
            if col_d.button("🗑", key="edel_" + str(e["id"])):
                ex.delete(e["id"])
                st.rerun()

with tab_chart:
    st.subheader(t("exp.chart_title"))
    month_chart = st.text_input(t("exp.f_month_filter"),
                                 value=datetime.now().strftime("%Y-%m"),
                                 placeholder=t("common.month_ph"),
                                 key="exp_chart_month")
    summary = ex.monthly_summary(month_chart.strip())
    if summary["total"] > 0:
        st.metric(t("exp.total_month"), "฿{:,.0f}".format(summary["total"]))
        breakdown = summary["breakdown"]
        total_b = summary["total"] or 1
        for cat, amt in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            icon = ex.CATEGORY_ICONS.get(cat,"")
            pct = round(amt / total_b * 100, 1)
            bar_w = int(pct * 2)
            bar_html = (
                "<div style='margin:3px 0'>"
                "<span style='font-size:0.8rem;color:#9a9485;width:160px;display:inline-block'>"
                + icon + " " + expense_category(cat) + "</span>"
                "<div style='display:inline-block;background:#2a2a2a;width:" + str(bar_w) + "px;height:12px;vertical-align:middle'></div>"
                " <span style='font-size:0.8rem;color:#d4d0c8'>฿{:,.0f}".format(amt) +
                " (" + str(pct) + "%)</span>"
                "</div>"
            )
            st.html(bar_html)
    else:
        st.info(t("exp.empty"))

    st.subheader(t("exp.trend_title"))
    monthly = ex.monthly_totals(months=6)
    if monthly:
        for m in monthly:
            bar_html2 = (
                "<div style='margin:4px 0;font-size:0.85rem'>"
                "<span style='color:#9a9485;width:80px;display:inline-block'>" + m["month"] + "</span>"
                " ฿{:,.0f}".format(m["total"]) +
                "</div>"
            )
            st.html(bar_html2)
