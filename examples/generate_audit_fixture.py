"""Generate a deterministic audit-trail fixture for the Open Production demo.

Runs CreativeReframing + the three validation gates against a fixed topic and
writes one JSON line per decision to ``examples/output/audit_trail.jsonl``.
Produces at least 6 entries: 3 from creative_reframing (one per angle) and
3 from the validation gates (3 evidence-gate decisions on the fixture claims).
Stdlib only. Re-runs truncate the audit trail cleanly.

Usage: python examples/generate_audit_fixture.py
"""
from __future__ import annotations

import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from audit.recorder import AuditRecorder
except ImportError:  # Fallback inline recorder if src/audit/recorder.py is absent.
    class AuditRecorder:  # type: ignore[no-redef]
        def __init__(self, path: str = "audit_trail.jsonl") -> None:
            self.path = path
            self._lock = threading.Lock()
            Path(path).write_text("", encoding="utf-8")

        def record_gate_decision(self, gate_name, claim_id, decision_status,
                                 reason="", evidence=None) -> None:
            entry = {"ts": datetime.now(timezone.utc).isoformat(),
                     "gate_name": gate_name, "claim_id": claim_id,
                     "decision_status": decision_status, "reason": reason,
                     "evidence": evidence}
            with self._lock:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry) + "\n")

        def entries(self):
            text = Path(self.path).read_text(encoding="utf-8")
            return [json.loads(line) for line in text.splitlines() if line.strip()]

from agents.creative_reframing import CreativeReframing  # noqa: E402
from tools.llm_client import MockLLMClient              # noqa: E402
from validation.gates import (                          # noqa: E402
    ConsistencyGate, EvidenceGate, PublicationGate)

TOPIC = "CRISPR for sickle cell disease"
CLAIMS = [
    {"id": "c1", "fact_id": "efficacy", "conclusion": "high",
     "text": "CRISPR >90% efficacy in trials.", "source_ids": ["pubmed:38001234"]},
    {"id": "c2", "fact_id": "cost", "conclusion": "severe",
     "text": "Treatment costs exceed $2M.", "source_ids": []},
    {"id": "c3", "fact_id": "efficacy", "conclusion": "moderate",
     "text": "Only ~60% durable efficacy.", "source_ids": ["pubmed:38005678"]},
]
META = {"doi": "10.1000/open-production-demo",
        "authors": ["A. Smith", "B. Jones"],
        "date": "2026-07-27"}


def main() -> int:
    out = Path(__file__).resolve().parent / "output" / "audit_trail.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    rec = AuditRecorder(path=str(out))

    # 1. creative_reframing -- one entry per angle proposed.
    angles = CreativeReframing(llm=MockLLMClient()).run({"topic": TOPIC})["angles"]
    for a in angles:
        rec.record_gate_decision(
            gate_name="creative_reframing", claim_id=a["id"],
            decision_status="angle_proposed", reason=a.get("summary", ""),
            evidence={"risk_focus": a.get("risk_focus", "")})

    # 2. evidence gate -- one entry per claim.
    ev = EvidenceGate()
    for c in CLAIMS:
        p = ev.process(dict(c))
        rec.record_gate_decision(
            gate_name="evidence_gate", claim_id=c["id"],
            decision_status=p.get("status", "rejected"),
            reason=p.get("reason", ""),
            evidence={"source_ids": c.get("source_ids", [])})

    # 3. consistency gate -- one entry per detected contradiction.
    for c in ConsistencyGate().find_contradictions(CLAIMS):
        rec.record_gate_decision(
            gate_name="consistency_gate",
            claim_id=f"{c['claim_a']['id']}_{c['claim_b']['id']}",
            decision_status="contradiction_detected",
            reason=f"fact_id={c['fact_id']}", evidence={"fact_id": c["fact_id"]})

    # 4. publication gate -- one entry for document metadata.
    pub_ok, pub_reason = PublicationGate().check(META)
    rec.record_gate_decision(
        gate_name="publication_gate", claim_id="doc-metadata",
        decision_status="publish_ok" if pub_ok else "publish_rejected",
        reason=pub_reason, evidence=META)

    # Use middle-dot separator per spec ("audit trail: ... . N entries").
    sep = chr(0xB7)
    print(f"audit trail: {out} {sep} {len(rec.entries())} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
