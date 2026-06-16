"""Compatibility shim — pages import `from theme import apply_theme`."""
from _theme import apply as apply_theme

__all__ = ["apply_theme"]
