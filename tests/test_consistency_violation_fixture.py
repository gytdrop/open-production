"""Test that the ConsistencyContract violation fixture is regenerable.

Runs ``examples/generate_consistency_violation_fixture.py`` via subprocess and
asserts the output artefacts have the expected shape and content.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "generate_consistency_violation_fixture.py"
AUDIT_PATH = ROOT / "output" / "consistency_violation" / "consistency_violation_audit.jsonl"


def test_fixture_script_is_runnable():
    """The fixture script must run without errors and produce the audit JSONL."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"Script exited with {result.returncode}:\n{result.stderr}"
    )
    assert AUDIT_PATH.exists(), "JSONL audit file was not created"


def test_fixture_audit_has_three_entries():
    """The generated JSONL must have at least 3 entries (gen-001 pass, gen-002 violation, summary)."""
    lines = AUDIT_PATH.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    assert len(entries) >= 3, f"Expected ≥3 entries, got {len(entries)}"


def test_fixture_second_entry_is_contract_violated():
    """Entry 2 (gen-002) must have decision_status 'contract_violated' and name red_scarf."""
    lines = AUDIT_PATH.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    second = entries[1]
    assert second["decision_status"] == "contract_violated", (
        f"Expected 'contract_violated', got {second['decision_status']!r}"
    )
    assert "red_scarf" in second["reason"], (
        f"Expected reason to name 'red_scarf', got: {second['reason']!r}"
    )
