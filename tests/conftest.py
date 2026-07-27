"""Pytest config: sys.path + shared fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure ``src`` is importable when running ``pytest`` from the repo root.
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402  (after sys.path tweak)


@pytest.fixture
def mock_llm_response() -> str:
    """A fixed, valid JSON string the creative_reframing tests can parse."""
    return (
        '{"headline": "AI reframes X", "angle": "optimistic", '
        '"sources": ["s1", "s2"]}'
    )