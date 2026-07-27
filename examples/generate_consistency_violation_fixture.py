"""Generate a ConsistencyContract violation fixture for Open Production.

Scenario: Character "Elena" (char-elena) has a contract requiring
["red_scarf", "silver_locket"].

  gen-001: attributes = ["red_scarf", "silver_locket"] → PASS
  gen-002: attributes = ["silver_locket"]              → BLOCKED (red_scarf missing)

Writes two output files to ``output/consistency_violation/``:

  production.json                     – static record of the scenario
  consistency_violation_audit.jsonl   – 3-entry audit trail:
                                        entry 1: gen-001 passed
                                        entry 2: gen-002 contract_violated
                                        entry 3: production_blocked summary

Usage: python examples/generate_consistency_violation_fixture.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation.gates import ConsistencyContractGate  # noqa: E402

# ---------------------------------------------------------------------------
# Scenario data
# ---------------------------------------------------------------------------

CONTRACT = {
    "subject_id": "char-elena",
    "required_attributes": ["red_scarf", "silver_locket"],
    "prohibited_attributes": [],
    "variance_tolerance": 0.15,
}

GENERATIONS = [
    {
        "id": "gen-001",
        "subject_id": "char-elena",
        "attributes": ["red_scarf", "silver_locket", "dark_coat"],
        "description": "Elena in her winter coat, red scarf wrapped twice, locket visible.",
    },
    {
        "id": "gen-002",
        "subject_id": "char-elena",
        "attributes": ["silver_locket", "dark_coat"],
        "description": "Elena in her winter coat, locket at neck — red scarf not generated.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    out_dir = ROOT / "output" / "consistency_violation"
    out_dir.mkdir(parents=True, exist_ok=True)

    gate = ConsistencyContractGate()
    audit_entries: list[dict] = []
    production_blocked = False

    for gen in GENERATIONS:
        ok, reason = gate.check(CONTRACT, gen)
        if ok:
            status = "contract_passed"
        else:
            status = "contract_violated"
            production_blocked = True

        audit_entries.append(
            {
                "ts": _now(),
                "gate_name": "consistency_contract_gate",
                "generation_id": gen["id"],
                "subject_id": gen["subject_id"],
                "decision_status": status,
                "reason": reason,
                "attributes_checked": gen["attributes"],
                "required_attributes": CONTRACT["required_attributes"],
            }
        )

    # Final summary entry (entry 3 of 3)
    audit_entries.append(
        {
            "ts": _now(),
            "gate_name": "consistency_contract_gate",
            "generation_id": "production_summary",
            "subject_id": "char-elena",
            "decision_status": "production_blocked" if production_blocked else "production_approved",
            "reason": (
                "One or more generations violated the ConsistencyContract — "
                "production blocked until contract is satisfied."
                if production_blocked
                else "All generations passed the ConsistencyContract."
            ),
            "attributes_checked": [],
            "required_attributes": CONTRACT["required_attributes"],
        }
    )

    # Write JSONL audit trail
    audit_path = out_dir / "consistency_violation_audit.jsonl"
    with open(audit_path, "w", encoding="utf-8") as fh:
        for entry in audit_entries:
            fh.write(json.dumps(entry) + "\n")

    # Write static production.json record
    production_record = {
        "scenario": "consistency_contract_violation",
        "contract": CONTRACT,
        "generations": GENERATIONS,
        "audit_path": str(audit_path),
        "production_blocked": production_blocked,
        "generated_at": _now(),
    }
    prod_path = out_dir / "production.json"
    prod_path.write_text(json.dumps(production_record, indent=2), encoding="utf-8")

    sep = chr(0xB7)
    print(f"audit trail: {audit_path} {sep} {len(audit_entries)} entries")
    print(f"production record: {prod_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
