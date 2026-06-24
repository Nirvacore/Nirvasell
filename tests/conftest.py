"""Shared fixtures for Nirvasell tests.

Adds the project root to sys.path so that modules can be imported directly.
Mocks heavy dependencies (streamlit, db) that pure-logic modules may pull in
transitively.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Pre-mock streamlit so any transitive `import streamlit` won't blow up
sys.modules.setdefault("streamlit", MagicMock())
