"""Regression tests for legacy pages importing ``require_auth`` from auth."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load_auth() -> types.ModuleType:
    """Load auth with a minimal Streamlit stub and no eager auth-gate import."""
    streamlit = types.ModuleType("streamlit")
    streamlit.session_state = {}
    sys.modules["streamlit"] = streamlit
    sys.modules.pop("_auth_gate", None)

    spec = importlib.util.spec_from_file_location("auth", ROOT / "auth.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["auth"] = module
    spec.loader.exec_module(module)
    return module


class RequireAuthCompatibilityTests(unittest.TestCase):
    def tearDown(self) -> None:
        for name in ("auth", "_auth_gate", "streamlit"):
            sys.modules.pop(name, None)

    def test_legacy_import_is_lazy_and_delegates_exact_result(self) -> None:
        auth = _load_auth()
        self.assertNotIn("_auth_gate", sys.modules)

        user = {"id": 7, "role": "user"}
        calls: list[str] = []
        gate = types.ModuleType("_auth_gate")

        def require_auth() -> dict:
            calls.append("require_auth")
            return user

        gate.require_auth = require_auth
        sys.modules["_auth_gate"] = gate

        namespace: dict[str, object] = {}
        exec("from auth import require_auth", namespace)
        self.assertIs(namespace["require_auth"](), user)
        self.assertEqual(calls, ["require_auth"])

    def test_gate_stop_or_error_propagates_without_auth_bypass(self) -> None:
        auth = _load_auth()
        gate = types.ModuleType("_auth_gate")

        class StopExecution(RuntimeError):
            pass

        def stop() -> dict:
            raise StopExecution("login required")

        gate.require_auth = stop
        sys.modules["_auth_gate"] = gate

        with self.assertRaisesRegex(StopExecution, "login required"):
            auth.require_auth()


if __name__ == "__main__":
    unittest.main()
