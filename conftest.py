"""Pytest configuration for the Open Production workspace.

The sandboxed environment used for this project sometimes blocks the default
system temp directory. Point pytest's temp machinery at the repo's writable
scratch space so `tmp_path` and related fixtures keep working.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def pytest_configure() -> None:
    temp_root = Path.cwd() / ".tmp" / "pytest"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_root_str = str(temp_root)
    os.environ["TMPDIR"] = temp_root_str
    os.environ["TEMP"] = temp_root_str
    os.environ["TMP"] = temp_root_str
    tempfile.tempdir = temp_root_str

