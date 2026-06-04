"""Import products + images from the reseller/ scraper DB (power-user feature).

This page is intentionally separate from the main Upload flow — most customers
will never see it. It's for power-users who run the private reseller/ scraper
alongside nirva and want one-click sync.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import bridge_reseller as br
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from _components import page_header

db.init()
st.set_page_config(page_title="nirva · Import", page_icon="🔌", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="🔌", title=t("import.title"), subtitle=t("import.caption"))

# Path picker (default = sibling reseller/ dir)
default_path = br.default_reseller_db()
path_str = st.text_input(t("import.db_path"), str(default_path))
reseller_db = Path(path_str)

info = br.inspect(reseller_db)

if not info["exists"]:
    st.warning(t("import.not_found", path=info["path"]))
    st.markdown(t("import.howto"))
    st.stop()

# Show what we're about to import
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("import.stat_products"), info["products"])
c2.metric(t("import.stat_with_images"), info["products_with_images"])
c3.metric(t("import.stat_uploaded"), info["images_uploaded"])
c4.metric(t("import.stat_last_scrape"), (info["last_scrape"] or "—")[:16])

if info["sources"]:
    import suppliers as _sup
    st.caption(" · ".join(
        f"{_sup.display(k)}: {v}" for k, v in info["sources"].items()
    ))

markup = st.session_state.get("markup", 15)
round_to = st.session_state.get("round_to", 10)

st.divider()
c1, c2 = st.columns([3, 1])
with c1:
    st.caption(t("import.markup_info", markup=markup, round_to=round_to))
with c2:
    if st.button(t("import.run"), type="primary", width='stretch'):
        with st.spinner(t("import.running")):
            n = br.import_into_nirva(reseller_db, markup, round_to)
        st.success(t("import.done", n=n))
        st.balloons()
