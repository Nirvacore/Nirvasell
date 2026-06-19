"""E6 Quick Replies — pre-written answer templates for LINE/FB daily questions."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import quick_replies as qr
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
qr.init()
render_sidebar()

st.title(t("qrep.title"))
st.caption(t("qrep.caption"))

all_replies = qr.all_replies()
total = len(all_replies)
used_today = sum(1 for r in all_replies if (r.get("last_used") or "")[:10] ==
                 __import__("datetime").datetime.now().strftime("%Y-%m-%d"))
cats = qr.categories()

c1, c2, c3 = st.columns(3)
c1.metric(t("qrep.kpi_total"), total)
c2.metric(t("qrep.kpi_categories"), len(cats))
c3.metric(t("qrep.kpi_used_today"), used_today)

st.divider()

tab_browse, tab_add = st.tabs([t("qrep.tab_browse"), t("qrep.tab_add")])

with tab_browse:
    cat_filter = st.selectbox(
        t("qrep.cat_filter"),
        ["all"] + cats,
        format_func=lambda c: t("qrep.all_cats") if c=="all" else c,
    )
    replies = qr.all_replies(category=cat_filter if cat_filter != "all" else None)
    q = st.text_input(t("qrep.search"), placeholder=t("qrep.search_ph"))
    if q.strip():
        q_lower = q.lower()
        replies = [r for r in replies if
                   q_lower in (r["title"]+""+r["body"]).lower()]
    if not replies:
        st.info(t("qrep.empty"))
    for r in replies:
        rendered = qr.render(r["body"])
        with st.expander("**" + r["title"] + "**" +
                          " · " + r["category"] +
                          " · " + t("qrep.used_times") + " " + str(r["use_count"])):
            st.code(rendered, language=None)
            col1, col2, col3 = st.columns([2,1,1])
            if col1.button("📋 " + t("qrep.copy_btn"), key="qcopy_" + str(r["id"])):
                qr.bump_use(r["id"])
                st.toast(t("qrep.copied") + ": " + rendered[:60])
                st.rerun()

            if "qr_edit_" + str(r["id"]) not in st.session_state:
                st.session_state["qr_edit_" + str(r["id"])] = False

            if col2.button(t("qrep.edit_btn"), key="qedit_" + str(r["id"])):
                st.session_state["qr_edit_" + str(r["id"])] = True
            if col3.button(t("qrep.del_btn"), key="qdel_" + str(r["id"])):
                qr.delete(r["id"])
                st.rerun()

            if st.session_state.get("qr_edit_" + str(r["id"])):
                with st.form("edit_qr_" + str(r["id"])):
                    new_title = st.text_input(t("qrep.f_title"), value=r["title"])
                    new_body  = st.text_area(t("qrep.f_body"), value=r["body"], height=100)
                    new_cat   = st.text_input(t("qrep.f_category"), value=r["category"])
                    if st.form_submit_button(t("qrep.save_btn")):
                        qr.update(r["id"], title=new_title, body=new_body, category=new_cat)
                        st.session_state["qr_edit_" + str(r["id"])] = False
                        st.rerun()

with tab_add:
    st.subheader(t("qrep.add_title"))
    with st.form("add_qr_form"):
        col1, col2 = st.columns(2)
        title    = col1.text_input(t("qrep.f_title"), placeholder=t("qrep.title_ph"))
        category = col2.text_input(t("qrep.f_category"),
                                    placeholder=t("qrep.cat_ph"))
        body     = st.text_area(t("qrep.f_body"), height=120,
                                 placeholder=t("qrep.body_ph"))
        st.caption(t("qrep.vars_hint"))
        if st.form_submit_button(t("qrep.add_btn")):
            if title.strip() and body.strip():
                qr.add(title=title.strip(), body=body.strip(),
                       category=category.strip() or "general")
                st.success(t("qrep.added"))
                st.rerun()

    st.divider()
    st.subheader(t("qrep.vars_title"))
    var_html = (
        "<div style='font-size:0.83rem;color:#9a9485'>"
        "<b style='color:#d4d0c8'>{shop_name}</b> — " + t("qrep.var_desc_shop_name") + "<br>"
        "<b style='color:#d4d0c8'>{shipping_cost}</b> — " + t("qrep.var_desc_shipping_cost") + "<br>"
        "<b style='color:#d4d0c8'>{prep_days}</b> — " + t("qrep.var_desc_prep_days") + "<br>"
        "<b style='color:#d4d0c8'>{bank_name}</b> — " + t("qrep.var_desc_bank_name") + "<br>"
        "<b style='color:#d4d0c8'>{promptpay}</b> — " + t("qrep.var_desc_promptpay") + "<br>"
        "</div>"
    )
    st.html(var_html)
