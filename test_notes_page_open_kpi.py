"""Regression coverage for the Notes page open-note KPI."""
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


class _TabsReached(Exception):
    pass


class _MetricColumn:
    def __init__(self, metrics: list[tuple[str, object]]):
        self._metrics = metrics

    def metric(self, label, value, **_kwargs):
        self._metrics.append((label, value))


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page(metrics: list[tuple[str, object]]):
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_notes_kpi_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path

    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {"lang": "en"}
    fake_streamlit.columns = lambda count: [
        _MetricColumn(metrics) for _ in range(count)
    ]
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.subheader = lambda *_args, **_kwargs: None
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.tabs = (
        lambda _labels: (_ for _ in ()).throw(_TabsReached())
    )

    replacements = {
        "streamlit": fake_streamlit,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    cached_i18n = sys.modules.pop("i18n", None)
    sys.modules.update(replacements)
    try:
        notes.init()
        notes.add("Follow up with buyer")
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        sys.modules.pop("i18n", None)
        if cached_i18n is not None:
            sys.modules["i18n"] = cached_i18n
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_notes_page_shows_open_note_count() -> None:
    metrics: list[tuple[str, object]] = []
    page = Path(__file__).parent / "pages" / "G5_📝_Notes.py"

    with isolated_page(metrics):
        try:
            runpy.run_path(str(page), run_name="__notes_page_test__")
        except _TabsReached:
            pass
        else:
            raise AssertionError("Notes page did not reach its tabs")

    actual_values = [value for _label, value in metrics]
    assert actual_values == [1, 1, 0], actual_values


if __name__ == "__main__":
    test_notes_page_shows_open_note_count()
    print("notes page open KPI: 1 passed")
