"""Three small validation gates exercised by ``tests/test_gates.py``.

Each gate is a plain class — no external deps, no I/O.
"""
from __future__ import annotations

from typing import Optional


class EvidenceGate:
    """Accept claims that cite at least one source; reject otherwise."""

    def process(self, claim: dict) -> dict:
        source_ids = claim.get("source_ids") or []
        if not source_ids:
            return {**claim, "status": "rejected", "reason": "no source_ids"}
        return {**claim, "status": "accepted", "reason": "has sources"}


class ConsistencyGate:
    """Find pairs of claims that disagree on the same fact."""

    def find_contradictions(self, claims: list[dict]) -> list[dict]:
        contradictions: list[dict] = []
        for i, a in enumerate(claims):
            for b in claims[i + 1 :]:
                if a.get("fact_id") and a.get("fact_id") == b.get("fact_id"):
                    if a.get("conclusion") != b.get("conclusion"):
                        contradictions.append(
                            {
                                "fact_id": a["fact_id"],
                                "claim_a": a,
                                "claim_b": b,
                            }
                        )
        return contradictions


class PublicationGate:
    """Block publication when required metadata fields are missing."""

    REQUIRED = ("doi", "authors", "date")

    def check(self, metadata: dict) -> tuple[bool, str]:
        for field in self.REQUIRED:
            if not metadata.get(field):
                return False, f"missing {field}"
        return True, "ok"


class ConsistencyContractGate:
    """Stop-fast check of a GenerationResult against a ConsistencyContract."""

    def check(self, contract: dict, result: dict) -> tuple[bool, str]:
        required = contract.get("required_attributes") or []
        prohibited = contract.get("prohibited_attributes") or []
        result_attrs = set(result.get("attributes") or [])
        # stop-fast: first missing required
        for attr in required:
            if attr not in result_attrs:
                tol = contract.get("variance_tolerance", 0.15)
                if tol <= 0.10:
                    return (
                        False,
                        f"missing required_attribute: {attr} "
                        f"(variance_tolerance={tol}; "
                        f"partial match '{attr}' rejected)",
                    )
                return (False, f"missing required_attribute: {attr}")
        # then prohibited
        for attr in prohibited:
            if attr in result_attrs:
                return (False, f"prohibited_attribute present: {attr}")
        return (True, "ok")