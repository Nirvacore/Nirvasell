"""Regression coverage for rendering canonical Loyalty reward names."""
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


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page(rendered: list[str]):
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_loyalty_rewards_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path

    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {"lang": "th"}
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda count: [_Context() for _ in range(count)]
    fake_streamlit.divider = lambda: None
    fake_streamlit.markdown = (
        lambda body, **_kwargs: rendered.append(body)
    )
    fake_streamlit.form = lambda *_args, **_kwargs: _Context()
    fake_streamlit.selectbox = lambda _label, options, **_kwargs: options[0]
    fake_streamlit.text_input = lambda *_args, **_kwargs: ""
    fake_streamlit.number_input = lambda *_args, **_kwargs: 0.0
    fake_streamlit.form_submit_button = lambda *_args, **_kwargs: False
    fake_streamlit.info = lambda *_args, **_kwargs: None

    replacements = {
        "streamlit": fake_streamlit,
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
            toast=lambda *_args, **_kwargs: None,
        ),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    cached_loyalty = sys.modules.pop("loyalty", None)
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        sys.modules.pop("loyalty", None)
        if cached_loyalty is not None:
            sys.modules["loyalty"] = cached_loyalty
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_loyalty_page_renders_all_canonical_reward_names() -> None:
    rendered: list[str] = []
    page = Path(__file__).parent / "pages" / "A5_🎖_Loyalty.py"

    with isolated_page(rendered):
        runpy.run_path(str(page), run_name="__loyalty_rewards_page_test__")

    reward_cards = "\n".join(rendered)
    for reward_name in (
        "ส่งฟรี",
        "ส่วนลด 5%",
        "ส่วนลด 10%",
        "ของแถม",
        "จัดส่งด่วน",
    ):
        assert reward_name in reward_cards


if __name__ == "__main__":
    test_loyalty_page_renders_all_canonical_reward_names()
    print("loyalty page reward names: 1 passed")
