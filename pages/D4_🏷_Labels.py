"""D4 Label Generator — packing slips and shipping address labels."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import label_generator as lg
import shop_settings as ss
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
ss.init()
render_sidebar()

st.title(t("lbl.title"))
st.caption(t("lbl.caption"))

tab_manual, tab_order, tab_bulk = st.tabs([
    t("lbl.tab_manual"), t("lbl.tab_from_order"), t("lbl.tab_bulk")
])

with tab_manual:
    st.subheader(t("lbl.manual_title"))
    style = st.selectbox(t("lbl.style"),
                          list(lg.LABEL_STYLES.keys()),
                          format_func=lambda k: lg.LABEL_STYLES[k])
    with st.form("label_form"):
        col1, col2 = st.columns(2)
        order_id   = col1.text_input(t("lbl.f_order_id"))
        buyer_name = col2.text_input(t("lbl.f_buyer"))
        phone      = col1.text_input(t("lbl.f_phone"))
        carrier    = col2.selectbox(t("lbl.f_carrier"),
                                     ["kerry","flash","j&t","thaipost","best","ninja_van"])
        address    = st.text_area(t("lbl.f_address"), height=80)
        col3, col4 = st.columns(2)
        total_price = col3.number_input(t("lbl.f_total"), min_value=0.0, step=10.0)
        cod_amount  = col4.number_input(t("lbl.f_cod"), min_value=0.0, step=10.0)
        notes       = st.text_input(t("lbl.f_notes"))

        items_raw = st.text_area(t("lbl.f_items"),
                                  placeholder=t("lbl.sku_qty_ph"),
                                  height=60)
        if st.form_submit_button(t("lbl.generate_btn")):
            items = []
            for part in items_raw.split(","):
                part = part.strip()
                if ":" in part:
                    s, q = part.split(":", 1)
                    try:
                        items.append({"sku": s.strip(), "qty": int(q.strip())})
                    except ValueError:
                        items.append({"sku": s.strip(), "qty": 1})
                elif part:
                    items.append({"sku": part, "qty": 1})
            result = lg.generate_label(
                order_id=order_id, buyer_name=buyer_name,
                buyer_phone=phone, buyer_address=address,
                items=items, total_price=total_price,
                cod_amount=cod_amount, tracking="",
                carrier=carrier, notes=notes, style=style,
            )
            st.session_state["label_result"] = result
    if st.session_state.get("label_result"):
        st.subheader(t("lbl.preview"))
        st.code(st.session_state["label_result"], language=None)

with tab_order:
    st.subheader(t("lbl.order_title"))
    order_key = st.text_input(t("lbl.order_id_input"), placeholder=t("lbl.order_id_ph"))
    style2 = st.selectbox(t("lbl.style"), list(lg.LABEL_STYLES.keys()),
                           format_func=lambda k: lg.LABEL_STYLES[k], key="style2")
    if st.button(t("lbl.fetch_btn")) and order_key:
        result2 = lg.from_order(order_key, style=style2)
        st.code(result2, language=None)

with tab_bulk:
    st.subheader(t("lbl.bulk_title"))
    st.caption(t("lbl.bulk_caption"))
    bulk_input = st.text_area(
        t("lbl.bulk_orders"),
        placeholder="order_id,buyer_name,phone,address,total,cod\n1001,สมชาย,0812345678,กรุงเทพ,350,350",
        height=150,
    )
    style3 = st.selectbox(t("lbl.style"), list(lg.LABEL_STYLES.keys()),
                           format_func=lambda k: lg.LABEL_STYLES[k], key="style3")
    if st.button(t("lbl.bulk_btn")) and bulk_input:
        lines = [l.strip() for l in bulk_input.strip().split("\n") if l.strip()]
        if lines and "," in lines[0] and not lines[0][0].isdigit():
            lines = lines[1:]  # skip header
        all_labels = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            while len(parts) < 6:
                parts.append("")
            try:
                label = lg.generate_label(
                    order_id=parts[0], buyer_name=parts[1],
                    buyer_phone=parts[2], buyer_address=parts[3],
                    total_price=float(parts[4] or 0),
                    cod_amount=float(parts[5] or 0),
                    style=style3,
                )
                all_labels.append(label)
            except Exception:
                pass
        if all_labels:
            combined = ("\n" + "=" * 40 + "\n").join(all_labels)
            st.code(combined, language=None)
            st.success(str(len(all_labels)) + t("lbl.bulk_done"))
