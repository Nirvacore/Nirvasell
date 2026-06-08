"""Bulk Photo Studio — drop 1-50 product photos → AI removes background
+ centers subject + standardizes to square 1080×1080 → download all as ZIP.

Replaces ~30 minutes of Photoshop work with a 1-minute one-screen workflow.
The "Shopee/Lazada-ready" output meets every Thai marketplace's image
guideline: square ratio, neutral background, subject centered with padding."""
from __future__ import annotations
import io
import sys
import zipfile
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import image_utils as iu
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, toast, friendly_error
from i18n import t

st.set_page_config(page_title="nirva.sell · Photo Studio",
                   page_icon="📷", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📷", title=t("studio.title"), subtitle=t("studio.caption"))


# ---- Upload + settings ------------------------------------------------

cU, cS = st.columns([3, 2])
with cU:
    uploaded = st.file_uploader(
        t("studio.drop_label"),
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help=t("studio.drop_help"),
    )

with cS:
    size = st.selectbox(
        t("studio.output_size"),
        [800, 1080, 1200, 1500, 2000],
        index=1,
        format_func=lambda n: f"{n}×{n}",
    )
    bg = st.selectbox(
        t("studio.bg_color"),
        ["white", "cream", "black"],
        format_func=lambda k: {"white": "⚪ ขาว (แนะนำ)",
                                "cream": "🤎 ครีม", "black": "⚫ ดำ"}.get(k, k),
    )
    padding_pct = st.slider(
        t("studio.padding"),
        0, 20, 6, 1, format="%d%%",
        help=t("studio.padding_help"),
    )


if not uploaded:
    st.markdown(
        f"<div style='margin-top:20px;padding:24px 28px;background:#fbf9f3;"
        f"border:0.5px solid rgba(40,30,20,0.07);border-radius:14px;"
        f"max-width:680px'>"
        f"<div style='font-family:Cormorant Garamond,serif;font-size:1.2rem;"
        f"font-weight:500;color:#1c1c1c;margin-bottom:8px'>"
        f"💡 {t('studio.how_title')}</div>"
        f"<div style='color:#3d3d3d;font-size:14px;line-height:1.7'>"
        f"{t('studio.how_body')}</div></div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ---- Process all -------------------------------------------------------

st.markdown(f"### {t('studio.processing', n=len(uploaded))}")

prog = st.progress(0, text=t("studio.starting"))
results: list[tuple[str, bytes, bytes]] = []   # (filename, original, processed)
errors: list[tuple[str, str]] = []

for i, up in enumerate(uploaded, 1):
    prog.progress((i - 1) / len(uploaded), text=f"{i}/{len(uploaded)} · {up.name}")
    try:
        raw = up.getvalue()
        processed = iu.studio_process(
            raw, size=int(size), bg=bg, padding=padding_pct / 100,
        )
        results.append((up.name, raw, processed))
    except Exception as e:
        errors.append((up.name, f"{type(e).__name__}: {e}"))

prog.progress(1.0, text=t("studio.done", n=len(results)))
prog.empty()

if errors:
    st.warning(t("studio.errors_n", n=len(errors)))
    for fname, err in errors:
        st.text(f"  • {fname}: {err}")


# ---- Preview grid + ZIP download --------------------------------------

if results:
    # ZIP first (sticky at top)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, (orig_name, _orig, processed) in enumerate(results, 1):
            stem = Path(orig_name).stem
            z.writestr(f"{i:02d}_{stem}_studio.jpg", processed)
    zip_buf.seek(0)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    cZ1, cZ2 = st.columns([2, 1])
    with cZ1:
        st.markdown(
            f"<div style='background:rgba(77,108,92,0.06);border:0.5px solid "
            f"rgba(77,108,92,0.20);border-radius:10px;padding:14px 16px;"
            f"font-size:14px'>"
            f"✓ {t('studio.ready', n=len(results), size=size)}</div>",
            unsafe_allow_html=True,
        )
    with cZ2:
        st.download_button(
            f"⬇ {t('studio.download_zip')}",
            data=zip_buf.getvalue(),
            file_name=f"nirva_photos_{stamp}.zip",
            mime="application/zip",
            type="primary",
            width="stretch",
        )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown(f"#### {t('studio.preview')}")
    st.caption(t("studio.preview_hint"))

    # 4-column grid of before/after pairs
    cols_per_row = 4
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j >= len(results):
                break
            fname, orig, processed = results[i + j]
            with cols[j]:
                st.markdown(
                    f"<div style='font-size:11px;text-transform:uppercase;"
                    f"letter-spacing:0.10em;color:#7a7569;margin-bottom:6px'>"
                    f"{fname[:24]}{'…' if len(fname) > 24 else ''}</div>",
                    unsafe_allow_html=True,
                )
                cA, cB = st.columns(2)
                with cA:
                    st.image(orig, caption=t("studio.before"), width='stretch')
                with cB:
                    st.image(processed, caption=t("studio.after"), width='stretch')
                # Per-file download
                stem = Path(fname).stem
                st.download_button(
                    f"⬇ {stem}_studio.jpg",
                    data=processed,
                    file_name=f"{stem}_studio.jpg",
                    mime="image/jpeg",
                    key=f"_dl_{i+j}",
                    type="tertiary",
                    width="stretch",
                )

    # Event log
    try:
        import events
        events.log(
            category="ai", severity="success",
            title=f"📷 Photo Studio: {len(results)} images processed",
            body=f"Output {size}×{size} px · bg={bg}",
        )
    except Exception:
        pass


st.divider()
st.caption(t("studio.disclaimer"))
