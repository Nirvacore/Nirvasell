"""F7 Voucher Studio — design, manage, and export promo codes."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import vouchers as vc
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

_VOUCHER_TYPES = {
    "percent": "vou.type_percent",
    "fixed": "vou.type_fixed",
    "shipping": "vou.type_shipping",
}

apply_theme()
require_auth()
vc.init()
render_sidebar()

st.title(t("vou.title"))
st.caption(t("vou.caption"))

all_v = vc.all_vouchers()
active_v = [v for v in all_v if v["status"] == "active"]
c1, c2 = st.columns(2)
c1.metric(t("vou.kpi_total"), len(all_v))
c2.metric(t("vou.kpi_active"), len(active_v))

st.divider()
tab_all, tab_create, tab_templates = st.tabs([
    t("vou.tab_all"), t("vou.tab_create"), t("vou.tab_templates")
])

with tab_all:
    vouchers = vc.all_vouchers()
    if not vouchers:
        st.info(t("vou.empty"))
    for v in vouchers:
        disc_str = (str(int(v["discount_value"])) + ("%" if v["discount_type"]=="percent" else " ฿")
                    if v["discount_type"] != "shipping" else t("vou.free_shipping"))
        status_icon = "✅" if v["status"]=="active" else "⏸"
        label = "**" + v["code"] + "** · " + disc_str + " · " + v["label"] + " · " + status_icon
        with st.expander(label):
            col1, col2 = st.columns(2)
            col1.write(t("vou.min_spend") + ": ฿" + str(v["min_spend"] or 0))
            col2.write(t("vou.platforms") + ": " + (v.get("platforms") or "all"))
            col1.write(t("vou.starts") + ": " + (v.get("starts_at") or "—"))
            col2.write(t("vou.expires") + ": " + (v.get("expires_at") or "—"))
            col_c, col_d = st.columns(2)
            if v["status"] == "active":
                if col_c.button(t("vou.pause_btn"), key="vp_" + str(v["id"])):
                    vc.pause(v["id"]); st.rerun()
            else:
                if col_c.button(t("vou.resume_btn"), key="vr_" + str(v["id"])):
                    vc.resume(v["id"]); st.rerun()
            if col_d.button(t("vou.delete_btn"), key="vd_" + str(v["id"])):
                vc.delete(v["id"]); st.rerun()

with tab_create:
    st.subheader(t("vou.create_title"))
    with st.form("voucher_form"):
        col1, col2 = st.columns(2)
        code      = col1.text_input(t("vou.f_code"), placeholder=t("vou.code_ph"))
        label_v   = col2.text_input(t("vou.f_label"), placeholder=t("vou.label_ph"))
        col3, col4 = st.columns(2)
        dtype     = col3.selectbox(t("vou.f_type"),
                                    ["percent","fixed","shipping"],
                                    format_func=lambda d: t(_VOUCHER_TYPES[d]))
        dvalue    = col4.number_input(t("vou.f_value"), min_value=0.0, step=5.0)
        col5, col6 = st.columns(2)
        min_spend = col5.number_input(t("vou.f_min_spend"), min_value=0.0, step=50.0)
        max_uses  = col6.number_input(t("vou.f_max_uses"), min_value=0, step=10)
        col7, col8 = st.columns(2)
        starts    = col7.text_input(t("vou.f_start"), placeholder=t("common.date_ph"))
        expires   = col8.text_input(t("vou.f_expires"), placeholder=t("common.date_ph"))
        platforms = st.multiselect(t("vou.f_platforms"),
                                    ["shopee","lazada","tiktok_shop","facebook","line"])
        if st.form_submit_button(t("vou.create_btn")):
            if code.strip():
                ok, msg = vc.add(code=code.strip(), label=label_v,
                                  discount_type=dtype, discount_value=dvalue,
                                  min_spend=min_spend, max_uses=int(max_uses),
                                  starts_at=starts, expires_at=expires,
                                  platforms=platforms)
                if ok:
                    st.success(t("vou.created"))
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    st.subheader(t("vou.suggest_title"))
    sel_tmpl = st.selectbox(t("vou.sel_template"),
                              list(vc.TEMPLATES.keys()),
                              format_func=lambda k: vc.TEMPLATES[k]["icon"] + " " + vc.TEMPLATES[k]["label"])
    if sel_tmpl:
        suggested_code = vc.suggest_code(sel_tmpl)
        tmpl = vc.TEMPLATES[sel_tmpl]
        s = tmpl["suggested"]
        disc_str = (str(s["discount_value"]) + ("%" if s["discount_type"]=="percent" else " ฿"))
        st.write(t("vou.suggest_code") + ": **" + suggested_code + "**")
        st.write(t("vou.suggest_discount") + ": " + disc_str)
        st.write(t("vou.suggest_min") + ": ฿" + str(s["min_spend"]))
        st.write(t("vou.suggest_duration") + ": " + str(s["duration_days"]) + t("vou.days"))
        if st.button(t("vou.use_template")):
            from datetime import datetime, timedelta
            start_s = datetime.now().strftime("%Y-%m-%d")
            end_s   = (datetime.now() + timedelta(days=s["duration_days"])).strftime("%Y-%m-%d")
            vc.add(code=suggested_code, label=tmpl["label"],
                    discount_type=s["discount_type"], discount_value=s["discount_value"],
                    min_spend=s["min_spend"], starts_at=start_s, expires_at=end_s)
            st.success(t("vou.created"))
            st.rerun()

with tab_templates:
    st.subheader(t("vou.festival_calendar"))
    for key, tmpl in vc.TEMPLATES.items():
        s = tmpl["suggested"]
        disc_str = (str(s["discount_value"]) + ("%" if s["discount_type"]=="percent" else " ฿"))
        row_html = (
            "<div style='margin:4px 0;font-size:0.84rem'>"
            "<span style='width:28px;display:inline-block'>" + tmpl["icon"] + "</span>"
            "<b style='color:#d4d0c8;width:220px;display:inline-block'>" + tmpl["label"] + "</b>"
            "<span style='color:#9a9485'>" + disc_str +
            (t("vou.min_spend_line", amount=str(s["min_spend"])) if s["min_spend"] > 0 else "") +
            " · " + str(s["duration_days"]) + t("vou.days") + "</span>"
            "</div>"
        )
        st.html(row_html)
