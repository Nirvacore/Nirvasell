"""Regression coverage for creating a pinned note from the Notes page."""
from __future__ import annotations

import runpy
import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import db
import notes


class _Rerun(Exception):
    pass


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Column:
    def metric(self, *_args, **_kwargs):
        return None

    def text_input(self, label, **_kwargs):
        return "Pinned from page" if label == "note.f_title" else ""

    def selectbox(self, _label, options, **_kwargs):
        return options[0]

    def button(self, *_args, **_kwargs):
        return False


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_notes_pin_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path

    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {"lang": "en"}
    fake_streamlit.columns = lambda count: [_Column() for _ in range(count)]
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.subheader = lambda *_args, **_kwargs: None
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.tabs = lambda labels: [_Context() for _ in labels]
    fake_streamlit.segmented_control = lambda *_args, **_kwargs: "all"
    fake_streamlit.form = lambda *_args, **_kwargs: _Context()
    fake_streamlit.text_area = lambda *_args, **_kwargs: "Remember this"
    fake_streamlit.text_input = lambda *_args, **_kwargs: ""
    fake_streamlit.checkbox = lambda *_args, **_kwargs: True
    fake_streamlit.form_submit_button = lambda *_args, **_kwargs: True
    fake_streamlit.success = lambda *_args, **_kwargs: None
    fake_streamlit.rerun = lambda: (_ for _ in ()).throw(_Rerun())

    replacements = {
        "streamlit": fake_streamlit,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "i18n": _module("i18n", t=lambda key: key),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        yield db_path
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_notes_page_persists_pin_selection() -> None:
    page = Path(__file__).parent / "pages" / "G5_📝_Notes.py"

    with isolated_page():
        try:
            runpy.run_path(str(page), run_name="__notes_pin_page_test__")
        except _Rerun:
            pass
        else:
            raise AssertionError("Notes page did not submit its add form")

        rows = notes.all_notes()
        assert len(rows) == 1
        assert rows[0]["title"] == "Pinned from page"
        assert rows[0]["pinned"] == 1


if __name__ == "__main__":
    test_notes_page_persists_pin_selection()
    print("notes page pinned create: 1 passed")
