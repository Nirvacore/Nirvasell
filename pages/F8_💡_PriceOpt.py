"""F8 target-price adviser using configured platform-fee assumptions."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import price_optimizer as po
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()


def render_target_calculation(result: dict, *, cost: float,
                              target_margin: float) -> None:
    if result.get("error"):
        st.warning(t("popt.advisory_unavailable"))
        return

    selected = result["selected"]
    r1, r2, r3, r4 = st.columns(4)
    r1.metric(t("popt.target_price"), "฿{:,.0f}".format(selected["price"]))
    r2.metric(
        t("popt.calculated_margin"),
        str(selected["actual_margin_pct"]) + "%",
        delta_color=(
            "normal"
            if selected["actual_margin_pct"] >= target_margin
            else "inverse"
        ),
    )
    r3.metric(
        t("popt.net_after_listed_costs"), "฿{:,.0f}".format(selected["net"])
    )
    r4.metric(
        t("popt.estimated_platform_fees"),
        "฿{:,.0f}".format(selected["platform_fee"]),
    )
    st.html(
        "<div style='font-size:0.83rem;color:#9a9485;margin-top:8px'>"
        + t("popt.cost") + ": ฿{:,.0f}".format(cost)
        + " · " + t("popt.fee") + ": ฿{:,.0f}".format(selected["platform_fee"])
        + " · " + t("popt.profit") + ": ฿{:,.0f}".format(selected["net"])
        + "</div>"
    )

    st.divider()
    st.subheader(t("popt.check_title"))
    col5, col6 = st.columns(2)
    check_price = col5.number_input(
        t("popt.check_price"),
        value=float(selected["price"]),
        step=10.0,
        min_value=0.0,
    )
    check_platform = col6.selectbox(
        t("popt.platform"), po.CANONICAL_PLATFORMS, key="chk_plat"
    )
    if check_price <= 0:
        return
    margin = po.margin_at_price(cost, check_price, check_platform)
    if margin.get("error"):
        st.warning(t("popt.advisory_unavailable"))
        return
    cr1, cr2, cr3 = st.columns(3)
    cr1.metric(t("popt.fee"), "฿{:,.0f}".format(margin["platform_fee"]))
    margin_color = (
        "normal" if margin["actual_margin_pct"] >= target_margin else "inverse"
    )
    cr2.metric(
        t("popt.calculated_margin"),
        str(margin["actual_margin_pct"]) + "%",
        delta_color=margin_color,
    )
    cr3.metric(t("popt.profit"), "฿{:,.0f}".format(margin["net"]))


st.title(t("popt.advisory_title"))
st.caption(t("popt.advisory_caption"))

tab_calc, tab_compare = st.tabs([t("popt.tab_calc"), t("popt.tab_compare")])

with tab_calc:
    st.subheader(t("popt.target_calc_title"))
    col1, col2 = st.columns(2)
    cost       = col1.number_input(t("popt.cost"), min_value=0.0, value=100.0, step=10.0)
    target_m   = col2.number_input(t("popt.target_margin"), min_value=0.1, value=25.0,
                                    step=5.0, format="%.0f")
    col3, col4 = st.columns(2)
    platform   = col3.selectbox(t("popt.platform"), po.CANONICAL_PLATFORMS)
    psych      = col4.checkbox(t("popt.safe_psych_price"), value=True)

    if cost > 0:
        result = po.target_price(
            cost=cost,
            target_margin_pct=target_m,
            platform=platform,
            psychological=psych,
        )
        render_target_calculation(
            result,
            cost=cost,
            target_margin=target_m,
        )

with tab_compare:
    st.subheader(t("popt.compare_title"))
    col1, col2, col3 = st.columns(3)
    c_cost    = col1.number_input(t("popt.cost"), min_value=0.0, value=100.0, step=10.0,
                                   key="cmp_cost")
    c_margin  = col2.number_input(t("popt.target_margin"), min_value=0.1, value=25.0,
                                   step=5.0, key="cmp_m")
    c_psych   = col3.checkbox(t("popt.safe_psych_price"), value=True, key="cmp_p")

    if c_cost > 0:
        results = [
            row for row in po.compare_platforms(
                cost=c_cost,
                target_margin_pct=c_margin,
                psychological=c_psych,
            )
            if not row.get("error")
        ]
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.84rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("popt.platform"), t("popt.target_price"),
                    t("popt.estimated_platform_fees"), t("popt.calculated_margin"),
                    t("popt.net_after_listed_costs")]:
            table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
        table_html += "</tr>"
        best_margin = max(r["selected"]["actual_margin_pct"] for r in results) if results else 0
        for r in results:
            selected = r["selected"]
            is_best = selected["actual_margin_pct"] == best_margin
            bg = " background:#1a2a1a" if is_best else ""
            col_m = "#4d6c5c" if selected["actual_margin_pct"] >= c_margin else "#c54c4c"
            table_html += "<tr style='border-top:1px solid #2a2a2a;" + bg + "'>"
            table_html += "<td style='padding:4px 8px'>" + r["platform_label"] + ("⭐" if is_best else "") + "</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(selected["price"]) + "</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(selected["platform_fee"]) + "</td>"
            table_html += "<td style='padding:4px 8px;color:" + col_m + "'>" + str(selected["actual_margin_pct"]) + "%</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(selected["net"]) + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)
