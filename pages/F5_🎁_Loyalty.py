"""F5 Loyalty Program — points, tiers, rewards for repeat customers."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import loyalty as loy
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import loyalty_tier
from sidebar import render_sidebar

apply_theme()
require_auth()
loy.init()
render_sidebar()

st.title(t("loy.title"))
st.caption(t("loy.caption"))

stats = loy.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("loy.kpi_members"), stats.get("total_members", 0))
c2.metric(t("loy.kpi_points_issued"), "{:,}".format(stats.get("total_points_issued", 0)))
c3.metric(t("loy.kpi_redeemed"), "{:,}".format(stats.get("total_redeemed", 0)))
c4.metric(t("loy.kpi_top_tier"),
          stats.get("top_tier_count", 0),
          delta_color="normal" if stats.get("top_tier_count", 0) > 0 else "off")

st.divider()

tab_leaderboard, tab_earn, tab_rewards, tab_tiers = st.tabs([
    t("loy.tab_leaders"), t("loy.tab_earn"), t("loy.tab_rewards"), t("loy.tab_tiers")
])

with tab_leaderboard:
    st.subheader(t("loy.leaders_title"))
    leaders = loy.leaderboard(limit=20)
    if not leaders:
        st.info(t("loy.empty"))
    else:
        for i, m in enumerate(leaders):
            tier_info = loy.TIERS.get(m.get("tier","bronze"), {})
            tier_icon = tier_info.get("icon","")
            medal = ["🥇","🥈","🥉"][i] if i < 3 else str(i+1) + "."
            row_html = (
                "<div style='margin:4px 0;font-size:0.84rem'>"
                "<span style='width:32px;display:inline-block;color:#9a9485'>" + medal + "</span>"
                "<span style='width:180px;display:inline-block'>" + (m.get("customer_key","—")[:20]) + "</span>"
                "<span style='color:#9a9485;width:80px;display:inline-block'>" +
                tier_icon + " " + loyalty_tier(m.get("tier", "bronze")) + "</span>"
                "<span style='color:#c5963d'>" + "{:,}".format(m.get("points",0)) + " " + t("loy.pts") + "</span>"
                " <span style='color:#7a7569;font-size:0.78rem'>(" +
                "{:,}".format(m.get("lifetime_points",0)) + " " + t("loy.lifetime") + ")</span>"
                "</div>"
            )
            st.html(row_html)

with tab_earn:
    st.subheader(t("loy.earn_title"))
    with st.form("earn_form"):
        col1, col2 = st.columns(2)
        cust_key = col1.text_input(t("loy.f_customer_key"), placeholder=t("loy.cust_key_ph"))
        amount   = col2.number_input(t("loy.f_amount"), min_value=0.0, step=50.0)
        desc     = col1.text_input(t("loy.f_desc"), placeholder=t("loy.desc_ph"))
        if st.form_submit_button(t("loy.earn_btn")):
            if cust_key.strip() and amount > 0:
                result = loy.earn_points(cust_key.strip(), amount, desc)
                pts = result.get("earned", 0)
                bal = result.get("balance", 0)
                tier = result.get("tier", "bronze")
                tier_info = loy.TIERS.get(tier, {})
                st.success(
                    "+" + str(pts) + " " + t("loy.pts") +
                    " · " + t("loy.balance") + ": " + str(bal) +
                    " · " + tier_info.get("icon", "") + " " + loyalty_tier(tier)
                )
                st.rerun()

    st.divider()
    st.subheader(t("loy.lookup_title"))
    lookup_key = st.text_input(t("loy.f_lookup"), placeholder=t("loy.cust_key_ph"))
    if lookup_key.strip():
        info = loy.customer_loyalty(lookup_key.strip())
        if info and info.get("exists"):
            tier_info = loy.TIERS.get(info.get("tier","bronze"), {})
            l1, l2, l3 = st.columns(3)
            l1.metric(t("loy.pts"), "{:,}".format(info.get("points",0)))
            l2.metric(t("loy.lifetime"), "{:,}".format(info.get("lifetime_points",0)))
            l3.metric(t("loy.tier"), tier_info.get("icon", "") + " " +
                      loyalty_tier(info.get("tier", "bronze")))
        else:
            st.info(t("loy.cust_not_found"))

with tab_rewards:
    st.subheader(t("loy.rewards_title"))
    for r in loy.REWARDS:
        col1, col2 = st.columns([4,1])
        col1.write(r["icon"] + " **" + r["name"] + "** — " +
                   str(r["points"]) + " " + t("loy.pts"))
        if col2.button(t("loy.redeem_btn") + " " + r["id"],
                       key="redeem_" + r["id"]):
            st.session_state["redeem_target"] = r["id"]

    if st.session_state.get("redeem_target"):
        st.divider()
        st.write(t("loy.redeem_for") + ": " + st.session_state["redeem_target"])
        with st.form("redeem_form"):
            cust_r = st.text_input(t("loy.f_customer_key"))
            if st.form_submit_button(t("loy.confirm_redeem")):
                result = loy.redeem_points(cust_r.strip(),
                                            st.session_state["redeem_target"])
                if result.get("success"):
                    st.success(t("loy.redeemed"))
                    st.session_state["redeem_target"] = None
                else:
                    st.error(result.get("error", t("loy.redeem_fail")))
                st.rerun()

with tab_tiers:
    st.subheader(t("loy.tiers_title"))
    for tier_key, tier_info in loy.TIERS.items():
        tier_html = (
            "<div style='margin:5px 0;padding:8px 12px;border-left:3px solid #2a2a2a'>"
            "<span style='font-size:1.2rem'>" + tier_info["icon"] + "</span>"
            " <b style='color:#d4d0c8'>" + loyalty_tier(tier_key) + "</b>"
            " &nbsp;·&nbsp; <span style='color:#9a9485'>" +
            "{:,}".format(tier_info["min_points"]) + t("loy.pts_min") + "</span>"
            + (" &nbsp;·&nbsp; " + t("loy.discount_pct", pct=str(tier_info["discount_pct"])) if tier_info["discount_pct"] > 0 else "") +
            "</div>"
        )
        st.html(tier_html)
    st.caption(t("loy.points_rate") + ": " + t("loy.points_per_baht"))
