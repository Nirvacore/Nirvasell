"""Vision intake — drop product photos, Claude Vision auto-fills product data.

Workflow:
  1. Drop 1-N images
  2. Each image → Claude Vision extracts name/brand/specs/est_price
  3. User fills in actual cost
  4. Save into nirva DB (or send to Workspace for AI content generation)
"""
from __future__ import annotations
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import vision as vision_mod
import parser as parser_mod
import onboarding
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from _components import page_header

db.init()
st.set_page_config(page_title="nirva · Vision", page_icon="📸", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📸", title=t("vision.title"), subtitle=t("vision.caption"))
onboarding.tip("vision")

api_key = st.session_state.get("api_key", "")
markup = st.session_state.get("markup", 15)
round_to = st.session_state.get("round_to", 10)

if not api_key:
    st.warning(t("generate.api_warn"))
    st.stop()


# ----- Upload images -------------------------------------------------------

files = st.file_uploader(
    t("vision.drop_label"),
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

# Save uploaded images to disk so we can reference them later.
IMAGES_DIR = Path(__file__).parent.parent / "data" / "uploaded_images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# ----- Process images via Claude Vision -----------------------------------

if files:
    if st.session_state.get("vision_processed_n") != len(files):
        st.session_state["vision_processed_n"] = len(files)
        st.session_state["vision_results"] = []

        progress = st.progress(0, text=t("vision.processing"))
        for i, f in enumerate(files):
            try:
                raw = f.getvalue()
                # Save image to disk
                ext = Path(f.name).suffix or ".jpg"
                local_name = f"vision_{uuid.uuid4().hex[:8]}{ext}"
                local_path = IMAGES_DIR / local_name
                local_path.write_bytes(raw)

                # Vision extract
                data = vision_mod.extract_one(raw, f.name, api_key=api_key)
                data["filename"] = f.name
                data["image_path"] = str(local_path)
                # Generate a SKU if not present
                data["sku"] = f"VIS-{uuid.uuid4().hex[:8].upper()}"
                st.session_state["vision_results"].append(data)
            except Exception as e:
                st.session_state["vision_results"].append({
                    "filename": f.name,
                    "error": f"{type(e).__name__}: {e}",
                })
            progress.progress((i + 1) / len(files), text=f"{i+1}/{len(files)}")
        progress.empty()


# ----- Review + edit + save ------------------------------------------------

results: list[dict] = st.session_state.get("vision_results", [])
if not results:
    if files:
        st.info("…")
    else:
        st.markdown(t("vision.empty_help"))
    st.stop()

st.divider()
st.subheader(t("vision.review_title"))

# Editable preview, one card per image
to_save: list[dict] = []
for i, r in enumerate(results):
    if "error" in r:
        with st.expander(f"⚠ {r.get('filename', '?')}"):
            st.error(r["error"])
        continue

    label = r.get("name") or r.get("filename") or "?"
    confidence = r.get("confidence", 0)
    conf_emoji = "🟢" if confidence >= 0.8 else ("🟡" if confidence >= 0.5 else "🔴")
    with st.expander(f"{conf_emoji} {label[:90]} (confidence {confidence:.0%})", expanded=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            st.image(r["image_path"], width='stretch')
            st.caption(r.get("notes") or "")

        with c2:
            cc1, cc2 = st.columns(2)
            sku = cc1.text_input(t("upload.field.sku"), r["sku"], key=f"sku_{i}")
            brand = cc2.text_input(t("upload.field.brand"), r.get("brand", ""), key=f"brand_{i}")

            name = st.text_input(
                t("upload.field.name").rstrip(" *"),
                r.get("name", ""),
                key=f"name_{i}",
            )
            specs = st.text_area(
                t("upload.field.specs"),
                r.get("specs", ""),
                key=f"specs_{i}",
                height=80,
            )

            cc3, cc4, cc5 = st.columns(3)
            category = cc3.text_input(
                t("upload.field.category"),
                r.get("category", ""),
                key=f"cat_{i}",
            )
            cost_default = int(r.get("estimated_thb") or 0)
            cost = cc4.number_input(
                t("upload.field.cost"),
                min_value=0,
                value=cost_default,
                step=10,
                key=f"cost_{i}",
            )
            sell = parser_mod.markup_price(cost, markup, round_to) if cost else 0
            cc5.metric(t("common.sell"), f"฿{sell:,}" if sell else "—")

            if sku and name and cost > 0:
                to_save.append({
                    "sku": sku,
                    "name": name,
                    "brand": brand,
                    "category": category,
                    "cost_price": cost,
                    "sell_price": sell,
                    "specs": specs,
                    "image_url": r["image_path"],
                })

st.divider()
cc1, cc2 = st.columns([1, 3])
with cc1:
    if st.button(
        t("vision.save_all", n=len(to_save)),
        type="primary",
        width='stretch',
        disabled=not to_save,
    ):
        df = pd.DataFrame(to_save)
        batch_id = db.create_batch(f"vision-{len(df)}-photos", len(df))
        n = db.upsert_products(df, batch_id)
        st.success(t("vision.saved", n=n))
        st.session_state["vision_results"] = []
        st.session_state["vision_processed_n"] = 0
        st.balloons()
with cc2:
    st.caption(t("vision.save_hint"))
