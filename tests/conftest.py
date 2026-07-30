"""Pytest config: sys.path + shared fixtures."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure ``src`` is importable when running ``pytest`` from the repo root.
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402  (after sys.path tweak)

# ---------------------------------------------------------------------------
# Redirect pytest's tmp_path to the system temp dir so we never hit the
# locked .tmp/pytest/pytest-of-<user> directory under the repo root on
# Windows. This must be set before any collection happens.
# ---------------------------------------------------------------------------
_SYSTEM_TEMP = Path(tempfile.gettempdir()) / "pytest-open-production"
_SYSTEM_TEMP.mkdir(parents=True, exist_ok=True)


def pytest_configure(config):
    """Point pytest's built-in tmp_path base at the system temp dir."""
    # Only override if not already set by the caller (e.g. --basetemp flag).
    if not config.option.__dict__.get("basetemp"):
        config.option.basetemp = str(_SYSTEM_TEMP)


@pytest.fixture
def mock_llm_response() -> str:
    """A fixed, valid JSON string the creative_reframing tests can parse."""
    return (
        '{"headline": "AI reframes X", "angle": "optimistic", '
        '"sources": ["s1", "s2"]}'
    )