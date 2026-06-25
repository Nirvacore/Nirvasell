"""D2 Tax Report — Thai seller income tax summary."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import tax_report as tr
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import tax_expense_cat_label, tax_quarter_label, quarter_short_label
from sidebar import render_sidebar
from datetime import datetime

apply_theme()
require_auth()
render_sidebar()

st.title(t("tax.title"))
st.caption(t("tax.caption"))

year = datetime.now().year
st.info(t("tax.disclaimer"), icon="⚠️")

vat = tr.vat_check(year)
c1, c2, c3 = st.columns(3)
c1.metric(t("tax.kpi_ytd"), "฿{:,.0f}".format(vat["revenue"]))
pct = vat["pct_of_threshold"]
c2.metric(t("tax.kpi_vat_threshold"),
          "฿{:,.0f}".format(tr.VAT_THRESHOLD),
          delta=str(pct) + "%",
          delta_color="inverse" if vat["requires_vat"] else "normal")
if vat["requires_vat"]:
    c3.metric(t("tax.kpi_vat_status"), t("tax.vat_required"), delta=t("tax.must_register"))
else:
    c3.metric(t("tax.kpi_vat_status"), t("tax.vat_safe"),
              delta=t("tax.remaining_headroom",
                      amount="{:,.0f}".format(vat["remaining_headroom"])))

st.divider()

tab_q, tab_annual = st.tabs([t("tax.tab_quarterly"), t("tax.tab_annual")])

with tab_q:
    col_y, col_q = st.columns(2)
    sel_year = col_y.number_input(t("tax.sel_year"), min_value=2020, max_value=year+1,
                                   value=year, step=1)
    sel_q = col_q.selectbox(t("tax.sel_quarter"), [1, 2, 3, 4],
                             format_func=quarter_short_label)
    try:
        data = tr.quarterly(int(sel_year), sel_q)
        q1, q2, q3 = st.columns(3)
        q1.metric(t("tax.revenue"), "฿{:,.0f}".format(data["revenue"]))
        q2.metric(t("tax.net_revenue"), "฿{:,.0f}".format(data["net_revenue"]))
        q3.metric(t("tax.gross_profit"), "฿{:,.0f}".format(data["gross_profit"]))

        st.subheader(t("tax.deduction_title"))
        d1, d2 = st.columns(2)
        d1.metric(t("tax.std_deduction") + " (60%)",
                  "฿{:,.0f}".format(data["standard_deduction"]))
        d1.metric(t("tax.taxable_std"),
                  "฿{:,.0f}".format(data["taxable_income_std"]))
        if data["expenses"]:
            d2.metric(t("tax.actual_expenses"),
                      "฿{:,.0f}".format(data["total_expenses"]))
            d2.metric(t("tax.taxable_actual"),
                      "฿{:,.0f}".format(data["taxable_income_actual"]))

        if data["expenses"]:
            st.subheader(t("tax.expenses_title"))
            for cat, amt in sorted(data["expenses"].items(),
                                   key=lambda x: x[1], reverse=True):
                st.write(t("tax.expense_line",
                           cat=tax_expense_cat_label(cat),
                           amount="{:,.0f}".format(amt)))
    except Exception as e:
        st.error(t("tax.error") + ": " + str(e))

with tab_annual:
    sel_year_a = st.number_input(t("tax.sel_year"), min_value=2020,
                                  max_value=year+1, value=year,
                                  step=1, key="tax_yr_a")
    try:
        ann = tr.annual(int(sel_year_a))
        a1, a2, a3 = st.columns(3)
        a1.metric(t("tax.revenue"), "฿{:,.0f}".format(ann["revenue"]))
        a2.metric(t("tax.net_revenue"), "฿{:,.0f}".format(ann["net_revenue"]))
        a3.metric(t("tax.orders"), str(ann["orders"]) + t("tax.orders_unit"))

        b1, b2 = st.columns(2)
        b1.metric(t("tax.taxable_std"),
                  "฿{:,.0f}".format(ann["taxable_income_std"]))
        b2.metric(t("tax.taxable_actual"),
                  "฿{:,.0f}".format(ann["taxable_income_actual"]))

        if ann.get("vat_required"):
            st.warning(t("tax.vat_alert"))

        st.subheader(t("tax.quarterly_breakdown"))
        for q in ann["by_quarter"]:
            st.write(tax_quarter_label(q["quarter"], q["year"]) + ": " +
                     t("tax.quarter_line",
                       net="{:,.0f}".format(q["net_revenue"]),
                       profit="{:,.0f}".format(q["gross_profit"])))
    except Exception as e:
        st.error(t("tax.error") + ": " + str(e))
