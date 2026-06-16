"""Compatibility shim — pages import `from sidebar import render_sidebar`."""
from _sidebar import render as render_sidebar

__all__ = ["render_sidebar"]
