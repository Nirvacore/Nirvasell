"""D6 Settings — shop profile and system configuration."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import shop_settings as ss
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import platform_name, carrier_name
from sidebar import render_sidebar

apply_theme()
require_auth()
ss.init()
render_sidebar()

st.title(t("set.title"))
st.caption(t("set.caption"))

tab_shop, tab_defaults, tab_about = st.tabs([
    t("set.tab_shop"), t("set.tab_defaults"), t("set.tab_about")
])

with tab_shop:
    st.subheader(t("set.shop_title"))
    current = ss.get_all()
    with st.form("shop_profile_form"):
        name    = st.text_input(t("set.f_name"), value=current.get("shop_name",""))
        phone   = st.text_input(t("set.f_phone"), value=current.get("shop_phone",""))
        address = st.text_area(t("set.f_address"), value=current.get("shop_address",""),
                               height=80)
        col1, col2 = st.columns(2)
        line_id = col1.text_input(t("set.f_line"), value=current.get("shop_line",""))
        fb      = col2.text_input(t("set.f_facebook"), value=current.get("shop_facebook",""))
        tax_id  = st.text_input(t("set.f_tax_id"), value=current.get("shop_tax_id",""))
        if st.form_submit_button(t("set.save_shop")):
            ss.set_many({
                "shop_name": name,
                "shop_phone": phone,
                "shop_address": address,
                "shop_line": line_id,
                "shop_facebook": fb,
                "shop_tax_id": tax_id,
            })
            st.success(t("set.saved"))
            st.rerun()

with tab_defaults:
    st.subheader(t("set.defaults_title"))
    current = ss.get_all()
    with st.form("defaults_form"):
        col1, col2 = st.columns(2)
        carrier = col1.selectbox(
            t("set.f_carrier"),
            ["kerry","flash","j&t","thaipost","best","ninja_van","other"],
            index=["kerry","flash","j&t","thaipost","best","ninja_van","other"].index(
                current.get("default_carrier","kerry")
            ) if current.get("default_carrier","kerry") in
                ["kerry","flash","j&t","thaipost","best","ninja_van","other"] else 0,
            format_func=carrier_name,
        )
        platform = col2.selectbox(
            t("set.f_platform"),
            ["shopee","lazada","tiktok_shop","facebook","line","direct"],
            index=["shopee","lazada","tiktok_shop","facebook","line","direct"].index(
                current.get("default_platform","shopee")
            ) if current.get("default_platform","shopee") in
                ["shopee","lazada","tiktok_shop","facebook","line","direct"] else 0,
            format_func=platform_name,
        )
        low_stock = col1.number_input(
            t("set.f_low_stock"), min_value=1, max_value=100,
            value=int(current.get("low_stock_threshold","5") or 5),
        )
        vat_default = col2.checkbox(
            t("set.f_vat"),
            value=(current.get("default_vat","false") == "true"),
        )
        order_prefix = col1.text_input(
            t("set.f_order_prefix"),
            value=current.get("order_prefix","ORD"),
        )
        if st.form_submit_button(t("set.save_defaults")):
            ss.set_many({
                "default_carrier": carrier,
                "default_platform": platform,
                "low_stock_threshold": str(low_stock),
                "default_vat": "true" if vat_default else "false",
                "order_prefix": order_prefix,
            })
            st.success(t("set.saved"))
            st.rerun()

with tab_about:
    st.subheader(t("set.about_title"))
    about_html = (
        "<div style='font-size:0.9rem;line-height:1.8'>"
        "<strong>" + t("set.about_version") + "</strong><br>"
        + t("set.about_tagline") + "<br><br>"
        "<strong>" + t("set.about_pages_line") + "</strong><br>"
        "<strong>" + t("set.about_db_line") + "</strong><br>"
        "<strong>" + t("set.about_platforms_line") + "</strong><br>"
        "</div>"
    )
    st.html(about_html)
    st.divider()
    st.subheader(t("set.data_title"))
    db_path_parts = __file__.split(os.sep)
    db_info = "data/users/{user_id}.db"
    st.code(db_info, language=None)
    st.caption(t("set.data_caption"))
