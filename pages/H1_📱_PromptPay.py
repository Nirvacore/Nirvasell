"""H1 PromptPay QR — generate payment QR codes for customers."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import payments as pm
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
pm.init()
render_sidebar()

st.title(t("pay.title"))
st.caption(t("pay.caption"))

settings = pm.get_settings()
pp_id    = settings.get("promptpay_id","") if settings else ""

tab_qr, tab_settings = st.tabs([t("pay.tab_qr"), t("pay.tab_settings")])

with tab_qr:
    if not pp_id:
        st.warning(t("pay.no_id"))
    else:
        st.info(t("pay.id_display", id=pp_id))
        col1, col2 = st.columns(2)
        amount = col1.number_input(t("pay.f_amount"), min_value=0.0, step=10.0,
                                    value=0.0, help=t("pay.amount_hint"))
        ref    = col2.text_input(t("pay.f_ref"), placeholder=t("common.order_ref_ph"))

        if st.button("📱 " + t("pay.gen_qr"), type="primary"):
            qr_amt = float(amount) if amount > 0 else None
            png = pm.promptpay_qr_png(pp_id, qr_amt)
            if png:
                st.image(png, width=280)
                if qr_amt:
                    st.success("฿{:,.2f}".format(qr_amt) + " · " + ref if ref else "฿{:,.2f}".format(qr_amt))
            else:
                payload = pm.promptpay_payload(pp_id, qr_amt)
                st.code(payload, language=None)
                st.caption(t("pay.install_qrcode"))

        st.divider()
        st.subheader(t("pay.test_amounts"))
        for amt in [50, 100, 200, 500, 1000]:
            cq1, cq2 = st.columns([1,3])
            cq1.write("฿{:,.0f}".format(amt))
            payload_small = pm.promptpay_payload(pp_id, float(amt))
            cq2.code(payload_small[:40] + "...", language=None)

with tab_settings:
    st.subheader(t("pay.settings_title"))
    with st.form("pay_settings_form"):
        new_id   = st.text_input(t("pay.f_id"),
                                  value=pp_id,
                                  placeholder=t("pay.id_ph"))
        shop_name= st.text_input(t("pay.f_shop"),
                                  value=settings.get("shop_name","") if settings else "")
        bank_name= st.text_input(t("pay.f_bank"),
                                  value=settings.get("bank_name","") if settings else "",
                                  placeholder=t("pay.bank_ph"))
        if st.form_submit_button(t("pay.save_btn")):
            pm.set_settings(promptpay_id=new_id.strip(),
                             shop_name=shop_name.strip(),
                             bank_name=bank_name.strip())
            st.success(t("pay.saved"))
            st.rerun()
