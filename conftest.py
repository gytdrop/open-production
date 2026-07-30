"""Pytest configuration for the Open Production workspace.

The sandboxed environment used for this project sometimes blocks the default
system temp directory. Point pytest's temp machinery at a writable temp root
so `tmp_path` and related fixtures keep working.

Primary target: ``C:\\Temp\\pytest-openprod`` (writable on Windows sandbox).
Fallback: ``<repo>/.tmp/pytest`` for Linux/macOS or when C:\\Temp is locked.
Override via env var ``PYTEST_BASETEMP`` if you want a different location.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _resolve_temp_root() -> Path:
    """Pick the best available temp root for pytest.

    Order of preference:
    1. ``PYTEST_BASETEMP`` env var (explicit override)
    2. ``C:\\Temp\\pytest-openprod`` (primary Windows target)
    3. ``<repo>/.tmp/pytest`` (fallback if C:\\Temp is unavailable)
    """
    override = os.environ.get("PYTEST_BASETEMP")
    if override:
        root = Path(override)
        try:
            root.mkdir(parents=True, exist_ok=True)
            return root
        except OSError:
            pass  # fall through to default

    primary = Path(r"C:\Temp\pytest-openprod")
    try:
        primary.mkdir(parents=True, exist_ok=True)
        return primary
    except OSError:
        pass

    fallback = Path.cwd() / ".tmp" / "pytest"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def pytest_configure() -> None:
    temp_root = _resolve_temp_root()
    temp_root_str = str(temp_root)
    os.environ["TMPDIR"] = temp_root_str
    os.environ["TEMP"] = temp_root_str
    os.environ["TMP"] = temp_root_str
    tempfile.tempdir = temp_root_str
