"""Shared demo flow for terminal and browser entry points.

The project already has a working CLI demo. This module factors the reusable
parts into a small shared flow so the browser demo can reuse the same
creative-reframing agent, gates, and audit recorder without duplicating logic.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agents.creative_reframing import ANGLE_IDS, CreativeReframing
from audit.recorder import AuditRecorder
from tools.llm_client import ResearchMockLLMClient
from validation.gates import ConsistencyGate, EvidenceGate, PublicationGate

# Optional ProductionService import (graceful degradation if service module
# was not yet created)
try:
    from service.production_service import ProductionService
    from schema.production_document import (
        IntentDocument,
        Production,
        audit_entry_from_gate_decision,
    )
    _SERVICE_AVAILABLE = True
except ImportError:
    _SERVICE_AVAILABLE = False


FIXTURE_CLAIMS = [
    {
        "id": "c1",
        "fact_id": "efficacy-rate",
        "conclusion": "high",
        "text": "CRISPR achieves >90% efficacy in clinical trials.",
        "source_ids": ["pubmed:38001234"],
    },
    {
        "id": "c2",
        "fact_id": "cost-barrier",
        "conclusion": "severe",
        "text": "Treatment costs exceed $2M per patient.",
        "source_ids": [],
    },
    {
        "id": "c3",
        "fact_id": "efficacy-rate",
        "conclusion": "moderate",
        "text": "CRISPR achieves only ~60% durable efficacy.",
        "source_ids": ["pubmed:38005678"],
    },
]

FIXTURE_METADATA = {
    "doi": "10.1000/demo-2026",
    "authors": ["Alice Smith", "Bob Jones"],
    "date": "2026-07-27",
    "title": "Demo document",
}


def pick_default_angle_id(topic: str) -> str:
    """Deterministically derive a default angle from the topic text."""
    if not topic:
        return ANGLE_IDS[0]
    idx = ord(topic[0].lower()) % len(ANGLE_IDS)
    return ANGLE_IDS[idx]


def generate_angles(topic: str, audience: str = "educated_lay", tone: str = "neutral") -> list[dict]:
    """Return the three creative angles for the given topic."""
    llm = ResearchMockLLMClient()
    agent = CreativeReframing(llm=llm)
    result = agent.run({"topic": topic, "audience": audience, "tone": tone})
    return result["angles"]


def _session_audit_path(out_dir: str) -> str:
    """Build a unique JSONL path for the current demo run."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid4().hex[:8]
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    return str(path / f"audit_{stamp}_{suffix}.jsonl")


def build_demo_report(
    topic: str,
    audience: str = "educated_lay",
    tone: str = "neutral",
    chosen_angle_id: str | None = None,
    audit_path: str | None = None,
    audit_dir: str = "output/public-demo",
    claims: list[dict] | None = None,
    metadata: dict | None = None,
) -> dict:
    """Run the full demo flow and return a browser-friendly report.

    The returned dict is designed to be serialized to JSON directly.
    """
    angles = generate_angles(topic, audience, tone)
    angle_ids = {angle["id"] for angle in angles}
    default_angle_id = chosen_angle_id or pick_default_angle_id(topic)
    resolved_angle_id = default_angle_id if default_angle_id in angle_ids else pick_default_angle_id(topic)
    chosen_angle = next((a for a in angles if a["id"] == resolved_angle_id), angles[0])

    resolved_audit_path = audit_path or _session_audit_path(audit_dir)
    recorder = AuditRecorder(path=resolved_audit_path)

    # Optional: build a ProductionService-mirrored trail so we can show two
    # artifacts shipping in the same run — the JSONL audit_trail.jsonl (legacy)
    # AND the production.json + audit.jsonl pair (new, per ACT-8).
    #
    # Both are kept in sync by routing every recorder.record_gate_decision()
    # through a mirror that ALSO calls service.apply_event(...).
    service_trail: list[dict] = []
    if _SERVICE_AVAILABLE:
        try:
            from pathlib import Path
            storage_dir = Path(resolved_audit_path).resolve().parent
            svc = ProductionService(storage_dir=storage_dir)
            prod = svc.init(
                name=topic[:80],
                intent=IntentDocument(topic=topic, audience=audience, tone=tone),
            )
        except Exception:
            # Service is best-effort during the demo run.
            svc = None
            prod = None
    else:
        svc = None
        prod = None

    def _mirror(entry: dict) -> None:
        """Best-effort: also push the entry into the Production service trail."""
        nonlocal prod
        if svc is None or prod is None:
            return
        try:
            ae = audit_entry_from_gate_decision(
                gate_name=entry["gate_name"],
                claim_id=entry["claim_id"],
                decision_status=entry["decision_status"],
                reason=entry.get("reason", ""),
                evidence=entry.get("evidence"),
                actor="demo_flow.build_demo_report",
            )
            new_prod = svc.apply_event(prod, ae)
            # Update the locally-bound Production so subsequent events see the
            # updated state.
            prod = new_prod
            service_trail.append(_audit_entry_to_dict_local(ae))
        except Exception:
            pass

    # --- gate decisions (legacy path + new mirror) ---
    entry_confirm = {
        "gate_name": "confirm_gate",
        "claim_id": "angle-selection",
        "decision_status": "accepted",
        "reason": f"user picked {chosen_angle['id']}",
        "evidence": {"options": list(ANGLE_IDS), "chosen": chosen_angle["id"]},
    }
    recorder.record_gate_decision(**entry_confirm)
    _mirror(entry_confirm)

    active_claims = claims if claims is not None else FIXTURE_CLAIMS
    active_metadata = metadata if metadata is not None else FIXTURE_METADATA

    ev_gate = EvidenceGate()
    accepted = 0
    rejected = 0
    evidence_results: list[dict] = []
    for claim in active_claims:
        processed = ev_gate.process(claim)
        status = processed["status"]
        if status == "accepted":
            accepted += 1
        else:
            rejected += 1
        evidence_results.append(processed)
        entry = {
            "gate_name": "evidence_gate",
            "claim_id": claim["id"],
            "decision_status": status,
            "reason": processed.get("reason", ""),
            "evidence": {"source_ids": claim.get("source_ids", [])},
        }
        recorder.record_gate_decision(**entry)
        _mirror(entry)

    cons_gate = ConsistencyGate()
    contradictions = cons_gate.find_contradictions(active_claims)
    contradiction_rows: list[dict] = []
    for contra in contradictions:
        row = {
            "gate_name": "consistency_gate",
            "claim_id": f"{contra['claim_a']['id']}_{contra['claim_b']['id']}",
            "decision_status": "contradiction_detected",
            "reason": f"fact_id={contra['fact_id']}",
            "evidence": {"fact_id": contra["fact_id"]},
        }
        contradiction_rows.append(row)
        recorder.record_gate_decision(**row)
        _mirror(row)

    pub_gate = PublicationGate()
    pub_ok, pub_reason = pub_gate.check(active_metadata)
    publication_row = {
        "gate_name": "publication_gate",
        "claim_id": "doc-metadata",
        "decision_status": "publish_ok" if pub_ok else "publish_rejected",
        "reason": pub_reason,
        "evidence": active_metadata,
    }
    recorder.record_gate_decision(**publication_row)
    _mirror(publication_row)

    # Persist the new ProductionService state if we built one.
    if svc is not None and prod is not None:
        try:
            svc.save(prod)
        except Exception:
            pass

    summary = (
        f"3 angles proposed | user picked {chosen_angle['id']} | "
        f"{accepted} claims accepted | {rejected} claims rejected | "
        f"{len(contradictions)} contradictions detected | audit trail: {resolved_audit_path}"
    )

    return {
        "topic": topic,
        "audience": audience,
        "tone": tone,
        "angles": angles,
        "chosen_angle": chosen_angle,
        "accepted_claims": accepted,
        "rejected_claims": rejected,
        "contradictions": contradictions,
        "evidence_results": evidence_results,
        "publication_result": publication_row,
        "summary": summary,
        "audit_path": resolved_audit_path,
        "audit_entries": recorder.entries(),
        # New: dual-artifact trail (per ACT-8). Empty list if service path
        # wasn't reachable. Both shapes are JSON-serializable.
        "production_id": (prod.id if prod is not None else None),
        "service_trail_entries": service_trail,
    }


def _audit_entry_to_dict_local(ae) -> dict:
    """Tiny shim: AuditEntry -> JSON dict, mirroring _audit_entry_to_dict
    in src/service/production_service.py but inlined so this module stays
    a single-file, import-light helper for the demo path."""
    return {
        "id": ae.id,
        "ts": ae.ts,
        "actor": ae.actor,
        "action_type": ae.action_type,
        "gate_name": ae.gate_name,
        "claim_id": ae.claim_id,
        "decision_status": ae.decision_status,
        "reason": ae.reason,
        "evidence": ae.evidence,
        "payload": ae.payload,
        "state_before": ae.state_before,
        "state_after": ae.state_after,
    }
