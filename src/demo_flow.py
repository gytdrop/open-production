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
from agents.editor import EditorAgent
from agents.environment_artist import EnvironmentArtistAgent
from agents.moodboard import MoodboardAgent
from agents.publisher import PublisherAgent
from agents.reference_clustering import ReferenceClusteringAgent
from agents.research_agent import ResearchAgent
from agents.shot_planner import ShotPlanningAgent
from audit.recorder import AuditRecorder
from tools.llm_client import ResearchMockLLMClient
from agents.reviewer import ReviewerAgent
from validation.gates import ConsistencyGate, EvidenceGate, PublicationGate
from src.transforms import get_transform, list_transforms
from src.transforms.compose.sequence import SequenceTransform

# Optional ProductionService import (graceful degradation if service module
# was not yet created)
try:
    from service.production_service import ProductionService
    from schema.production_document import (
        Environment,
        IntentDocument,
        MoodSpec,
        Production,
        Reference,
        Scene,
        Shot,
        StyleToken,
        audit_entry_from_gate_decision,
        utc_now_iso,
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


def _run_pipeline_transforms(topic: str, claims: list[dict], source_ids: list[str]) -> dict:
    """Run the registered transforms over pipeline inputs and return a summary dict.

    This wires the transform catalog into actual pipeline execution:
      - text.summary     : produce a brief (â‰¤50-word) truncation of the topic
      - text.word_count  : count words in the original topic
      - filter.dedupe    : deduplicate the source-id pool
      - filter.require_source: annotate each accepted claim with source_required=True
      - compose.sequence : run summaryâ†’word_count as a composed pipeline

    The returned dict is included in the build_demo_report() output under
    ``transform_results`` so callers and tests can inspect the work.
    """
    results: dict = {}

    summary_t = get_transform("text.summary")
    word_count_t = get_transform("text.word_count")
    dedupe_t = get_transform("filter.dedupe")
    require_source_t = get_transform("filter.require_source")

    # 1. Summarise the topic
    topic_summary = summary_t.apply(topic)
    results["topic_summary"] = topic_summary.value

    # 2. Word-count the original topic
    word_count_r = word_count_t.apply(topic)
    results["topic_word_count"] = word_count_r.value

    # 3. Deduplicate source ids
    dedupe_r = dedupe_t.apply(source_ids)
    results["deduped_source_ids"] = dedupe_r.value

    # 4. Tag each claim that already has sources with source_required=True
    tagged_claims = []
    for claim in claims:
        claim_copy = {**claim}
        if claim_copy.get("source_ids"):
            r = require_source_t.apply(claim_copy)
            tagged_claims.append(r.value)
        else:
            tagged_claims.append(claim_copy)
    results["tagged_claims"] = tagged_claims

    # 5. Composed pipeline: summary â†’ word_count (demonstrates SequenceTransform)
    pipeline = SequenceTransform(summary_t, word_count_t)
    pipeline_r = pipeline.apply(topic)
    results["pipeline_word_count"] = pipeline_r.value
    results["pipeline_steps"] = pipeline_r.metadata.get("steps", [])

    # 6. Record which transforms are active in the registry
    results["registered_transforms"] = list_transforms()

    return results


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
    active_claims = claims if claims is not None else FIXTURE_CLAIMS
    active_metadata = metadata if metadata is not None else FIXTURE_METADATA

    # ------------------------------------------------------------------
    # Transform Catalog pass â€” runs registered transforms over raw inputs
    # before gating so the catalog is part of actual pipeline execution.
    # ------------------------------------------------------------------
    all_source_ids_list = sorted({
        sid
        for claim in active_claims
        for sid in (claim.get("source_ids") or [])
        if str(sid).strip()
    })
    transform_results = _run_pipeline_transforms(
        topic=topic,
        claims=active_claims,
        source_ids=all_source_ids_list,
    )

    # ------------------------------------------------------------------
    # Stage 2: Research â€” collect sources and enforce â‰¥3-sources gate.
    # Re-use the already-deduped source id list from the transform pass.
    # ------------------------------------------------------------------
    researcher = ResearchAgent()
    all_source_ids = set(transform_results["deduped_source_ids"])
    research_sources = [{"id": sid} for sid in sorted(all_source_ids)]
    research_result = researcher.run({"operation": "validate", "topic": topic, "sources": research_sources})

    angles = generate_angles(topic, audience, tone)
    angle_ids = {angle["id"] for angle in angles}
    default_angle_id = chosen_angle_id or pick_default_angle_id(topic)
    resolved_angle_id = default_angle_id if default_angle_id in angle_ids else pick_default_angle_id(topic)
    chosen_angle = next((a for a in angles if a["id"] == resolved_angle_id), angles[0])

    resolved_audit_path = audit_path or _session_audit_path(audit_dir)
    recorder = AuditRecorder(path=resolved_audit_path)

    # Optional: build a ProductionService-mirrored trail so we can show two
    # artifacts shipping in the same run â€” the JSONL audit_trail.jsonl (legacy)
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

    # ------------------------------------------------------------------
    # Stage 2: Research write-back â€” persist source ids to Production.references.
    # Mirrors the Stage 3 pattern: construct Reference objects from the validated
    # source ids returned by ResearchAgent and _replace them onto the production.
    # ------------------------------------------------------------------
    if _SERVICE_AVAILABLE and svc is not None and prod is not None:
        try:
            import uuid as _uuid_r
            from dataclasses import replace as _replace
            research_refs = [
                Reference(
                    id=f"ref_{_uuid_r.uuid4().hex[:8]}",
                    kind="text",
                    label=src["id"],
                )
                for src in research_result.get("sources") or []
                if str(src.get("id") or "").strip()
            ]
            if research_refs:
                prod = _replace(prod, references=list(prod.references) + research_refs)
                ae_research = audit_entry_from_gate_decision(
                    gate_name="research_gate",
                    claim_id="research-sources",
                    decision_status=research_result["verdict"],
                    reason=research_result["rationale"],
                    evidence={"source_count": len(research_refs)},
                    actor="demo_flow.research_writeback",
                )
                prod = svc.apply_event(prod, ae_research)
                svc.save(prod)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stage: Environment write-back
    # Run EnvironmentArtistAgent for a demo location and, if ProductionService
    # is available, persist the approved Environment to the Production document.
    # ------------------------------------------------------------------
    env_result: dict = {}
    if _SERVICE_AVAILABLE and svc is not None and prod is not None:
        try:
            env_agent = EnvironmentArtistAgent()
            env_result = env_agent.run({
                "operation": "create",
                "location_name": "Primary Location",
                "location_type": "interior",
                "script_excerpt": topic[:200],
            })
            # Take the first proposal as the approved environment spec
            approved_env_proposal = (env_result.get("proposals") or [{}])[0]
            import uuid as _uuid
            env_id = f"env_{_uuid.uuid4().hex[:8]}"
            new_env = Environment(
                id=env_id,
                name="Primary Location",
                time_of_day_variants=approved_env_proposal.get("time_of_day_variants", []),
                lighting_presets=approved_env_proposal.get("lighting_presets", []),
            )
            from dataclasses import replace as _replace
            prod = _replace(prod, environments=list(prod.environments) + [new_env])
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stage: Shot-planning write-back
    # Run ShotPlanningAgent for a demo scene and, if ProductionService is
    # available, persist the Scene + Shot list to the Production document.
    # ------------------------------------------------------------------
    shot_plan_result: dict = {}
    if _SERVICE_AVAILABLE and svc is not None and prod is not None:
        try:
            planner = ShotPlanningAgent()
            scene_id = f"scene_{prod.id[-8:]}"
            shot_plan_result = planner.run({
                "scene_id": scene_id,
                "scene_type": "dialogue",
                "scene_description": topic[:200],
            })
            planned_shots = []
            for s in shot_plan_result.get("shots", []):
                planned_shots.append(Shot(
                    id=s["shot_id"],
                    scene_id=scene_id,
                    intent=s["intent"],
                    duration_sec=float(s["duration_sec"]),
                ))
            demo_scene = Scene(
                id=scene_id,
                name="Demo Scene",
                shots=planned_shots,
                mood=MoodSpec(emotional_promise=tone),
                location="Primary Location",
            )
            prod = _replace(prod, scenes=list(prod.scenes) + [demo_scene])
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stage 3: References â€” cluster supplied references into style tokens.
    # Seeds three demo references (simulating approved assets) and runs
    # ReferenceClusteringAgent to extract style tokens.  The chosen cluster
    # proposal is persisted as StyleTokens on the Production document.
    # ------------------------------------------------------------------
    ref_cluster_result: dict = {}
    if _SERVICE_AVAILABLE and svc is not None and prod is not None:
        try:
            demo_refs_input = [
                {"id": "ref_demo0001", "kind": "image", "label": "warm golden exterior", "uri": "demo://ref/1"},
                {"id": "ref_demo0002", "kind": "image", "label": "overcast verite documentary", "uri": "demo://ref/2"},
                {"id": "ref_demo0003", "kind": "image", "label": "natural texture organic", "uri": "demo://ref/3"},
            ]
            clusterer = ReferenceClusteringAgent()
            ref_cluster_result = clusterer.run({"operation": "cluster", "references": demo_refs_input})
            # Persist the approved references and the top style-token cluster.
            import uuid as _uuid2
            new_refs = [
                Reference(
                    id=f"ref_{_uuid2.uuid4().hex[:8]}",
                    kind=r["kind"],
                    label=r["label"],
                    uri=r.get("uri"),
                )
                for r in demo_refs_input
            ]
            top_cluster = (ref_cluster_result.get("proposals") or [{}])[0]
            new_style_tokens = [
                StyleToken(
                    id=f"tok_{_uuid2.uuid4().hex[:8]}",
                    name=tok,
                    kind="composite",
                )
                for tok in (top_cluster.get("style_tokens") or [])[:3]
            ]
            prod = _replace(
                prod,
                references=list(prod.references) + new_refs,
                style_tokens=list(prod.style_tokens) + new_style_tokens,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stage 4: Moodboard â€” assemble moodboard proposals from style tokens
    # and lock the chosen mood spec onto the demo scene.
    # ------------------------------------------------------------------
    moodboard_result: dict = {}
    if _SERVICE_AVAILABLE and svc is not None and prod is not None:
        try:
            mb_agent = MoodboardAgent()
            style_token_names = [t.name for t in prod.style_tokens]
            moodboard_result = mb_agent.run({
                "operation": "assemble",
                "scene_id": prod.scenes[0].id if prod.scenes else "scene_demo",
                "style_tokens": style_token_names,
                "emotional_promise": tone,
            })
            # Lock the first proposal as the approved mood.
            chosen_mb = (moodboard_result.get("proposals") or [{}])[0]
            lock_result = mb_agent.run({
                "operation": "lock",
                "scene_id": prod.scenes[0].id if prod.scenes else "scene_demo",
                "chosen_proposal": chosen_mb,
            })
            # Update the demo scene's mood spec with the locked moodboard.
            if prod.scenes:
                locked_mood = lock_result.get("mood_spec", {})
                updated_scenes = list(prod.scenes)
                first_scene = updated_scenes[0]
                from dataclasses import replace as _replace_scene
                updated_scenes[0] = _replace_scene(
                    first_scene,
                    mood=MoodSpec(
                        emotional_promise=locked_mood.get("emotional_promise", tone),
                        tonal_palette=locked_mood.get("tonal_palette", []),
                        references=locked_mood.get("references", []),
                        locked=True,
                    ),
                )
                prod = _replace(prod, scenes=updated_scenes)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stage 12: Timeline â€” EditorAgent proposes 3 cut assemblies;
    # the first approved proposal is committed to the production timeline
    # via ProductionService.commit_editor_proposal().
    # ------------------------------------------------------------------
    editor_result: dict = {}
    if _SERVICE_AVAILABLE and svc is not None and prod is not None and prod.scenes:
        try:
            editor = EditorAgent()
            demo_scene = prod.scenes[0]
            shot_dicts = [{"id": sh.id, "duration_sec": sh.duration_sec} for sh in demo_scene.shots]
            total_dur = sum(sh.duration_sec for sh in demo_scene.shots)
            editor_result = editor.run({
                "scene_id": demo_scene.id,
                "shots": shot_dicts,
                "narrative_intent": tone,
                "target_duration_sec": total_dur,
            })
            chosen_proposal = (editor_result.get("proposals") or [{}])[0]
            if chosen_proposal and "shot_sequence" in chosen_proposal:
                prod = svc.commit_editor_proposal(prod, {
                    "scene_id": demo_scene.id,
                    **chosen_proposal,
                })
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stage 24: Branching â€” create a review branch and take a snapshot.
    # Stage 25: Publishing â€” PublisherAgent generates manifest proposals.
    # Stage 26: Archive â€” ProductionService.archive() records expiry date.
    # ------------------------------------------------------------------
    branch_result: dict = {}
    publish_result: dict = {}
    archive_result: dict = {}
    if _SERVICE_AVAILABLE and svc is not None and prod is not None:
        try:
            # Stage 24: create a review branch + snapshot.
            prod = svc.create_branch(prod, "review-branch")
            prod = svc.snapshot(prod, label="pre-publish-snapshot", taken_by="demo_flow")
            branch_result = {
                "branch_id": prod.branches[-1].id if prod.branches else None,
                "snapshot_id": prod.snapshots[-1].id if prod.snapshots else None,
            }
        except Exception:
            pass

        try:
            # Stage 25: publish manifest proposals.
            publisher = PublisherAgent()
            publish_result = publisher.run({
                "production_id": prod.id,
                "title": prod.title or topic,
                "platforms": ["youtube"],
                "doi": active_metadata.get("doi", ""),
                "authors": active_metadata.get("authors", []),
                "date": active_metadata.get("date", ""),
                "total_duration_sec": (prod.timeline.total_duration_sec if prod.timeline else 0.0),
                "scene_count": len(prod.scenes),
                "shot_count": sum(len(s.shots) for s in prod.scenes),
            })
            # Persist the chosen manifest into Production.metadata.
            chosen_manifest = (publish_result.get("proposals") or [{}])[0].get("manifest") or {}
            if chosen_manifest:
                prod = _replace(
                    prod,
                    metadata={**prod.metadata, "publish_manifest": chosen_manifest},
                )
        except Exception:
            pass

        try:
            # Stage 26: transition to PUBLISHED then archive (best-effort).
            # We use raw state_transition events (no gate enforcement here) because
            # the demo purposely runs without real gate prerequisite data.
            from schema.production_document import AuditEntry as _AE
            def _tx(p, ns):
                return svc.apply_event(p, _AE(
                    id=f"evt_{ns.lower()[:12]}",
                    ts=utc_now_iso(),
                    actor="demo_flow",
                    action_type="state_transition",
                    payload={"next_state": ns},
                ))
            for next_s in ("BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED", "PUBLISHED"):
                if prod.state != next_s:
                    try:
                        prod = _tx(prod, next_s)
                    except Exception:
                        break
            if prod.state == "PUBLISHED":
                prod = svc.archive(prod, actor="demo_flow", retention_days=2555)
                archive_result = {
                    "archived_at": prod.metadata.get("archived_at"),
                    "expires_at": prod.metadata.get("expires_at"),
                }
        except Exception:
            pass

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
    research_entry = {
        "gate_name": "research_gate",
        "claim_id": "research-sources",
        "decision_status": research_result["verdict"],
        "reason": research_result["rationale"],
        "evidence": {
            "source_count": research_result["source_count"],
            "required_count": research_result["required_count"],
            "gate_passed": research_result["gate_passed"],
        },
    }
    recorder.record_gate_decision(**research_entry)
    _mirror(research_entry)

    entry_confirm = {
        "gate_name": "confirm_gate",
        "claim_id": "angle-selection",
        "decision_status": "accepted",
        "reason": f"user picked {chosen_angle['id']}",
        "evidence": {"options": list(ANGLE_IDS), "chosen": chosen_angle["id"]},
    }
    recorder.record_gate_decision(**entry_confirm)
    _mirror(entry_confirm)

    ev_gate = EvidenceGate()
    reviewer = ReviewerAgent()
    accepted = 0
    rejected = 0
    evidence_results: list[dict] = []
    reviewer_results: list[dict] = []
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

        # ReviewerAgent runs on each accepted claim (post-gate, pre-delivery)
        if status == "accepted":
            review = reviewer.run({
                "shot_id": claim["id"],
                "generation_result": {"attributes": claim.get("source_ids", []),
                                      "quality_score": 0.85},
                "production": {"state": "DRAFT", "characters": []},
                "check_types": ["technical_quality", "stage_gate"],
            })
            reviewer_results.append(review)
            review_entry = {
                "gate_name": "reviewer_agent",
                "claim_id": claim["id"],
                "decision_status": review["verdict"],
                "reason": f"score={review['score']:.2f} blocking={review['blocking']}",
                "evidence": {"checks": len(review["checks"])},
            }
            recorder.record_gate_decision(**review_entry)
            _mirror(review_entry)

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
        # ReviewerAgent results (one per accepted claim)
        "reviewer_results": reviewer_results,
        # Stage 2: Research gate result
        "research_result": research_result,
        # Stage 3: Reference clustering write-back result
        "ref_cluster_result": ref_cluster_result,
        # Stage 4: Moodboard write-back result
        "moodboard_result": moodboard_result,
        # Stage 9: Environment write-back result
        "env_result": env_result,
        # Stage 10: Shot-planning write-back result
        "shot_plan_result": shot_plan_result,
        # Stage 12: Timeline / editing write-back result
        "editor_result": editor_result,
        # Stage 24: Branching write-back result
        "branch_result": branch_result,
        # Stage 25: Publishing manifest proposals
        "publish_result": publish_result,
        # Stage 26: Archive retention record
        "archive_result": archive_result,
        # Transform Catalog results (wired into pipeline execution)
        "transform_results": transform_results,
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

# =============================================================================
# Stage-driven pipeline runner (extracted from the fixture-driven flow above)
# =============================================================================

class PauseForHuman(Exception):
    """Raised when the runner reaches the ConfirmGate and no sink is bound.

    The CLI catches this exception and presents the options to the user via a
    ConfirmSink implementation (TtyConfirmSink for interactive use,
    AutoConfirmSink for ``--no-confirm`` CI mode).
    """

    def __init__(self, request):
        self.request = request
        super().__init__("pause_for_human: confirm_gate awaiting user choice")


def _new_event_id() -> str:
    """Mint a fresh ``evt_<12 hex>`` id, matching AuditEntry's id format."""
    import uuid as _uuid
    return "evt_" + _uuid.uuid4().hex[:12]


def _stage_decision_entry(*, actor: str, proposals: list, rationale: str) -> "AuditEntry":
    """Wrap a stage's proposals into a single decision AuditEntry.

    Falls back to a single ``{"summary": ...}`` proposal when an agent returns
    a flat result dict (no ``proposals`` key) so every stage contributes at
    least one proposal row to the audit trail.
    """
    from src.schema.production_document import AuditEntry, utc_now_iso

    rows: list[dict] = []
    for p in proposals or []:
        if isinstance(p, dict):
            rows.append({"rationale": p.get("rationale") or rationale, **p})
        else:
            rows.append({"value": p, "rationale": rationale})
    if not rows:
        rows.append({"summary": "no proposals", "rationale": rationale})
    return AuditEntry(
        id=_new_event_id(),
        ts=utc_now_iso(),
        actor=actor,
        action_type="decision",
        reason=rationale,
        payload={"proposals": rows},
    )


def _stage_no_proposals_entry(*, actor: str, reason: str) -> "AuditEntry":
    """Emit a ``no proposals`` audit event when an agent returns nothing."""
    from src.schema.production_document import AuditEntry, utc_now_iso

    return AuditEntry(
        id=_new_event_id(),
        ts=utc_now_iso(),
        actor=actor,
        action_type="decision",
        reason=reason,
        payload={"proposals": [], "no_proposals": True},
    )


def _gate_entry(*, gate_name: str, claim_id: str, decision_status: str, reason: str,
                evidence: dict | None = None) -> "AuditEntry":
    """Build a gate_decision AuditEntry via the schema's bridge helper."""
    from src.schema.production_document import audit_entry_from_gate_decision

    return audit_entry_from_gate_decision(
        gate_name=gate_name,
        claim_id=claim_id,
        decision_status=decision_status,
        reason=reason,
        evidence=evidence or {},
        actor=f"runner.{gate_name}",
    )


def _safe_apply(svc: "ProductionService", prod: "Production", entry) -> "Production":
    """Apply an event and persist. Always returns a Production (or the input on error)."""
    try:
        new_prod = svc.apply_event(prod, entry)
        svc.save(new_prod)
        return new_prod
    except Exception:
        return prod


def run_pipeline(
    intent_dict: dict,
    out_dir,
    *,
    sink=None,
    llm_client=None,
) -> "Production":
    """Walk Stages 2 -> 22 using ProductionService as the source of truth.

    Args:
        intent_dict: ``{"topic": str, "audience": str, "tone": str, "platform": str}``
        out_dir: directory under which ``productions/prod_<id>/`` will be created
        sink: optional ``ConfirmSink`` to resolve the ConfirmGate inline
        llm_client: optional LLMClient (defaults to ``ResearchMockLLMClient``)

    Returns:
        The final ``Production`` (loaded back from disk to ensure parity).

    Raises:
        PauseForHuman: when the ConfirmGate is reached and ``sink`` is None.

    Notes:
        The runner never raises on a stage that returns empty proposals; it
        emits a ``no proposals`` audit event and proceeds. The hard failure
        path is the ConfirmGate: a declined response (``sink.ask()`` returns
        ``ConfirmResponse.declined=True``) terminates the pipeline with the
        decline recorded as a gate decision.
    """
    from pathlib import Path as _Path
    from src.agents.confirm_gate import ConfirmRequest, ConfirmResponse
    from src.agents.creative_reframing import ANGLE_IDS, CreativeReframing
    from src.schema.production_document import IntentDocument, utc_now_iso
    from src.service.production_service import ProductionService
    from src.validation.gates import (
        ConsistencyContractGate,
        ConsistencyGate,
        EvidenceGate,
        PublicationGate,
    )

    out_dir_path = _Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    topic = str(intent_dict.get("topic") or "Untitled")
    intent = IntentDocument(
        topic=topic,
        audience=intent_dict.get("audience"),
        tone=intent_dict.get("tone"),
        platform=intent_dict.get("platform"),
    )
    svc = ProductionService(storage_dir=out_dir_path)
    prod = svc.init(name=topic[:200] or "Untitled", intent=intent)
    evidence_gate = EvidenceGate()
    consistency_gate = ConsistencyGate()
    contract_gate = ConsistencyContractGate()
    publication_gate = PublicationGate()

    def _commit(actor: str, proposals: list, rationale: str) -> "Production":
        if not proposals:
            entry = _stage_no_proposals_entry(
                actor=actor, reason=f"{actor}: no proposals returned"
            )
        else:
            entry = _stage_decision_entry(actor=actor, proposals=proposals, rationale=rationale)
        return _safe_apply(svc, prod, entry)

    # ---- Stage 2: CreativeReframing -----------------------------------------
    reframer = CreativeReframing(llm=llm_client)
    reframing_result = reframer.run({
        "topic": topic,
        "audience": intent.audience or "educated_lay",
        "tone": intent.tone or "neutral",
    })
    angles = reframing_result.get("angles") or []
    prod = _commit(
        "creative_reframing",
        [{"id": a.get("id"), "name": a.get("name"), "summary": a.get("summary")} for a in angles],
        f"proposed {len(angles)} angles for {topic!r}",
    )

    # ---- ConfirmGate (between Stage 2 and Stage 3) ---------------------------
    request = ConfirmRequest(
        summary="Which angle should guide the write?",
        options=list(ANGLE_IDS),
        default=angles[0]["id"] if angles else ANGLE_IDS[0],
    )
    if sink is None:
        raise PauseForHuman(request)

    response: ConfirmResponse = sink.ask(request)
    chosen_angle_id = response.choice if not response.declined else ""
    confirm_decision = "accepted" if not response.declined else "rejected"
    prod = _safe_apply(
        svc,
        prod,
        _gate_entry(
            gate_name="confirm_gate",
            claim_id=chosen_angle_id or "no-choice",
            decision_status=confirm_decision,
            reason=("user picked " + chosen_angle_id) if not response.declined else "user declined",
            evidence={"options": list(ANGLE_IDS)},
        ),
    )
    if response.declined:
        return svc.load(prod.id)

    # ---- Stage 3: ResearchAgent ---------------------------------------------
    from src.agents.research_agent import ResearchAgent

    researcher = ResearchAgent()
    research_result = researcher.run({
        "operation": "gate",
        "topic": topic,
        "angle": chosen_angle_id,
        "sources": [
            {"id": "pubmed:38001234", "uri": "https://pubmed.ncbi.nlm.nih.gov/38001234/"},
            {"id": "pubmed:38005678", "uri": "https://pubmed.ncbi.nlm.nih.gov/38005678/"},
            {"id": "doi:10.1000/example-2026", "uri": "https://doi.org/10.1000/example-2026"},
        ],
    })
    research_proposals = research_result.get("proposals") or []
    prod = _commit(
        "research_agent",
        [{"angle": a.get("angle_name"), "summary": a.get("summary")} for a in research_proposals],
        f"research: {research_result.get('verdict', 'sources_insufficient')}",
    )
    prod = _safe_apply(
        svc,
        prod,
        _gate_entry(
            gate_name="research_gate",
            claim_id="research-sources",
            decision_status=("accepted" if research_result.get("gate_passed") else "sources_insufficient"),
            reason=research_result.get("rationale", "research gate"),
            evidence={"source_count": research_result.get("source_count", 0)},
        ),
    )

    # ---- Evidence gate (per claim) -------------------------------------------
    claims = [
        {"id": "c1", "fact_id": "efficacy-rate", "conclusion": "high", "source_ids": ["pubmed:38001234"]},
        {"id": "c2", "fact_id": "cost-barrier", "conclusion": "severe", "source_ids": []},
        {"id": "c3", "fact_id": "efficacy-rate", "conclusion": "moderate", "source_ids": ["pubmed:38005678"]},
    ]
    accepted = 0
    rejected = 0
    for claim in claims:
        outcome = evidence_gate.process(claim)
        decision_status = outcome.get("status", "rejected")
        if decision_status == "accepted":
            accepted += 1
        else:
            rejected += 1
        prod = _safe_apply(
            svc,
            prod,
            _gate_entry(
                gate_name="evidence_gate",
                claim_id=claim["id"],
                decision_status=decision_status,
                reason=outcome.get("reason", ""),
                evidence={"source_ids": claim.get("source_ids", [])},
            ),
        )

    # ---- Stage 4: ReferenceClusteringAgent -----------------------------------
    from src.agents.reference_clustering import ReferenceClusteringAgent

    clusterer = ReferenceClusteringAgent()
    cluster_input = {
        "operation": "cluster",
        "references": [
            {"id": "ref_1", "kind": "image", "label": "main ref", "uri": "asset://seed/1"},
            {"id": "ref_2", "kind": "image", "label": "main ref", "uri": "asset://seed/2"},
            {"id": "ref_3", "kind": "image", "label": "main ref", "uri": "asset://seed/3"},
        ],
        "topic": topic,
    }
    cluster_result = clusterer.run(cluster_input)
    cluster_proposals = cluster_result.get("proposals") or []
    prod = _commit(
        "reference_clustering",
        [{"cluster": p.get("cluster"), "size": p.get("size")} for p in cluster_proposals],
        f"reference_clustering: {len(cluster_proposals)} clusters",
    )

    # ---- Stage 5: MoodboardAgent ---------------------------------------------
    from src.agents.moodboard import MoodboardAgent

    moodboard = MoodboardAgent()
    mb_result = moodboard.run({
        "operation": "assemble",
        "scene_id": "scene_demo",
        "style_tokens": ["neutral"],
        "emotional_promise": intent.tone or "neutral",
    })
    mb_proposals = mb_result.get("proposals") or []
    prod = _commit(
        "moodboard",
        [{"emotional_promise": p.get("emotional_promise")} for p in mb_proposals],
        f"moodboard: {len(mb_proposals)} proposals",
    )

    # ---- Stage 6: StoryAgent -------------------------------------------------
    from src.agents.story import StoryAgent

    story = StoryAgent()
    story_result = story.run({
        "operation": "propose",
        "topic": topic,
        "angle": chosen_angle_id,
        "tone": intent.tone or "neutral",
    })
    story_proposals = story_result.get("proposals") or []
    prod = _commit(
        "story",
        [{"structure_name": p.get("structure_name")} for p in story_proposals],
        f"story: {story_proposals[0].get('structure_name') if story_proposals else 'none'}",
    )

    # ---- Stage 7: ScriptAgent -----------------------------------------------
    from src.agents.script import ScriptAgent

    script_agent = ScriptAgent()
    script_result = script_agent.run({
        "operation": "draft",
        "topic": topic,
        "structure_name": (story_proposals[0] or {}).get("structure_name") if story_proposals else "Classical Three-Act",
        "angle": chosen_angle_id,
    })
    script_proposals = script_result.get("proposals") or []
    prod = _commit(
        "script",
        [{"scene_count": p.get("scene_count")} for p in script_proposals],
        f"script: {len(script_proposals)} drafts",
    )

    # ---- Stage 8: ShotDesignerAgent -----------------------------------------
    from src.agents.shot_designer import ShotDesignerAgent

    shot_designer = ShotDesignerAgent()
    sd_result = shot_designer.run({
        "shot_id": "shot_1",
        "shot_intent": f"establish {topic}",
    })
    sd_proposals = sd_result.get("proposals") or []
    prod = _commit(
        "shot_designer",
        [{"label": p.get("label")} for p in sd_proposals],
        f"shot_designer: {len(sd_proposals)} framings",
    )

    # ---- Stage 9: ShotPlanningAgent -----------------------------------------
    from src.agents.shot_planner import ShotPlanningAgent

    shot_planner = ShotPlanningAgent()
    sp_result = shot_planner.run({
        "scene_id": "scene_demo",
        "scene_type": "dialogue",
        "scene_description": topic[:200],
    })
    sp_proposals = sp_result.get("shots") or []
    prod = _commit(
        "shot_planner",
        [{"shot_id": s.get("shot_id"), "intent": s.get("intent")} for s in sp_proposals],
        f"shot_planner: {len(sp_proposals)} shots",
    )

    # ---- Stage 10: CharacterDirectorAgent -----------------------------------
    from src.agents.character_director import CharacterDirectorAgent

    character_director = CharacterDirectorAgent()
    cd_result = character_director.run({
        "operation": "create",
        "script_excerpt": topic[:200],
        "archetype": "protagonist",
    })
    cd_proposals = cd_result.get("proposals") or []
    prod = _commit(
        "character_director",
        [{"visual_description": p.get("visual_description")} for p in cd_proposals],
        f"character_director: {len(cd_proposals)} proposals",
    )

    # ---- Stage 11: StoryboardArtistAgent -------------------------------------
    from src.agents.storyboard_artist import StoryboardArtistAgent

    storyboard_artist = StoryboardArtistAgent()
    sba_result = storyboard_artist.run({
        "shot_id": "shot_1",
        "shot_intent": f"establish {topic}",
    })
    sba_proposals = sba_result.get("proposals") or []
    prod = _commit(
        "storyboard_artist",
        [{"composition_description": p.get("composition_description")} for p in sba_proposals],
        f"storyboard_artist: {len(sba_proposals)} frames",
    )

    # ---- Stage 12: EnvironmentArtistAgent ------------------------------------
    from src.agents.environment_artist import EnvironmentArtistAgent

    environment_artist = EnvironmentArtistAgent()
    ea_result = environment_artist.run({
        "operation": "create",
        "location_name": "Primary Location",
        "location_type": "interior",
        "script_excerpt": topic[:200],
    })
    ea_proposals = ea_result.get("proposals") or []
    prod = _commit(
        "environment_artist",
        [{"name": p.get("name")} for p in ea_proposals],
        f"environment_artist: {len(ea_proposals)} proposals",
    )

    # ---- Stage 13: ReviewerAgent ---------------------------------------------
    from src.agents.reviewer import ReviewerAgent

    reviewer = ReviewerAgent()
    rv_result = reviewer.run({
        "shot_id": "shot_1",
        "generation_result": {
            "id": "gen_demo_001",
            "produced_at": utc_now_iso(),
            "attributes": ["pubmed:38001234"],
            "quality_score": 0.85,
        },
        "production": {"state": prod.state, "characters": []},
        "check_types": ["technical_quality", "stage_gate"],
    })
    prod = _commit(
        "reviewer_agent",
        [{"verdict": rv_result.get("verdict"), "score": rv_result.get("score")}],
        f"reviewer: {rv_result.get('verdict')} (score={rv_result.get('score')})",
    )

    # ---- Stage 14: EditorAgent -----------------------------------------------
    from src.agents.editor import EditorAgent

    editor = EditorAgent()
    ed_result = editor.run({
        "shots": sp_proposals or [{"shot_id": "shot_1", "duration_sec": 3.0}],
        "scene_id": "scene_demo",
    })
    ed_proposals = ed_result.get("proposals") or []
    prod = _commit(
        "editor",
        [{"proposal_label": p.get("label")} for p in ed_proposals],
        f"editor: {len(ed_proposals)} cut assemblies",
    )

    # ---- Consistency gate (after editor / shot planner) ---------------------
    contradictions = consistency_gate.find_contradictions(claims)
    for contra in contradictions:
        prod = _safe_apply(
            svc,
            prod,
            _gate_entry(
                gate_name="consistency_gate",
                claim_id=f"{contra['claim_a']['id']}_{contra['claim_b']['id']}",
                decision_status="contradiction_detected",
                reason=f"fact_id={contra['fact_id']}",
                evidence={"fact_id": contra["fact_id"]},
            ),
        )

    # ---- Stage 15: VoiceDirectorAgent ---------------------------------------
    from src.agents.voice_director import VoiceDirectorAgent

    voice_director = VoiceDirectorAgent()
    vd_result = voice_director.run({
        "script_excerpt": topic[:200],
        "tone": intent.tone or "neutral",
        "audience": intent.audience or "educated_lay",
    })
    vd_proposals = vd_result.get("proposals") or []
    prod = _commit(
        "voice_director",
        [{"voice_direction": p.get("voice_direction")} for p in vd_proposals],
        f"voice_director: {len(vd_proposals)} directions",
    )

    # ---- Stage 16: SoundDesignerAgent ---------------------------------------
    from src.agents.sound_designer import SoundDesignerAgent

    sound_designer = SoundDesignerAgent()
    sdes_result = sound_designer.run({
        "scene_id": "scene_demo",
        "scene_mood": {"emotional_promise": intent.tone or "neutral"},
    })
    sdes_proposals = sdes_result.get("proposals") or []
    prod = _commit(
        "sound_designer",
        [{"sound_palette": p.get("sound_palette")} for p in sdes_proposals],
        f"sound_designer: {len(sdes_proposals)} palettes",
    )

    # ---- Stage 17: MusicComposerAgent ---------------------------------------
    from src.agents.music_composer import MusicComposerAgent

    music_composer = MusicComposerAgent()
    mc_result = music_composer.run({
        "scene_id": "scene_demo",
        "scene_mood": {"emotional_promise": intent.tone or "neutral"},
    })
    mc_proposals = mc_result.get("proposals") or []
    prod = _commit(
        "music_composer",
        [{"music_brief": p.get("music_brief")} for p in mc_proposals],
        f"music_composer: {len(mc_proposals)} briefs",
    )

    # ---- Stage 18: ColoristAgent --------------------------------------------
    from src.agents.colorist import ColoristAgent

    colorist = ColoristAgent()
    cl_result = colorist.run({
        "scene_id": "scene_demo",
        "scene_mood": {"emotional_promise": intent.tone or "neutral"},
    })
    cl_proposals = cl_result.get("proposals") or []
    prod = _commit(
        "colorist",
        [{"color_grade": p.get("name") or p.get("label")} for p in cl_proposals],
        f"colorist: {len(cl_proposals)} grades",
    )

    # ---- Stage 19: AnimationDirectorAgent -----------------------------------
    from src.agents.animation_director import AnimationDirectorAgent

    animation_director = AnimationDirectorAgent()
    ad_result = animation_director.run({
        "shot_id": "shot_1",
        "shot_intent": f"establish {topic}",
    })
    ad_proposals = ad_result.get("proposals") or []
    prod = _commit(
        "animation_director",
        [{"motion_spec": p.get("motion_spec") or p.get("label")} for p in ad_proposals],
        f"animation_director: {len(ad_proposals)} motions",
    )

    # ---- Stage 20: AssetLibraryAgent -----------------------------------------
    # Run with no service backing (test mode) to avoid filesystem deps.
    asset_library_agent = None
    asset_summary = "skipped (no asset library service bound)"
    try:
        from src.service.asset_library_service import AssetLibraryService

        asset_service = AssetLibraryService(storage_dir=str(out_dir_path / "asset_library"))
        from src.agents.asset_library import AssetLibraryAgent

        asset_library_agent = AssetLibraryAgent(asset_service)
        al_result = asset_library_agent.run({
            "operation": "list",
            "category": "image",
        })
        al_proposals = al_result.get("assets") or []
        asset_summary = f"asset_library: {len(al_proposals)} assets"
    except Exception:
        al_proposals = []
    prod = _commit(
        "asset_library",
        [{"sha256": a.get("sha256")} for a in al_proposals],
        asset_summary,
    )

    # ---- Stage 21: GenerationAgent ------------------------------------------
    generation_proposals: list[dict] = []
    try:
        from src.agents.generation import GenerationAgent, MockGenerationPlugin

        generator = GenerationAgent(MockGenerationPlugin())
        gen_result = generator.run({
            "shot_id": "shot_1",
            "prompt": f"establish {topic}",
        })
        generation_proposals = [gen_result.get("generation_result") or {}]
        # Consistency-contract gate
        ok, reason = contract_gate.check(
            {"required_attributes": ["pubmed:38001234"]},
            {"attributes": ["pubmed:38001234"]},
        )
        prod = _safe_apply(
            svc,
            prod,
            _gate_entry(
                gate_name="consistency_contract",
                claim_id="shot_1",
                decision_status="accepted" if ok else "blocked",
                reason=reason,
                evidence={"required": ["pubmed:38001234"]},
            ),
        )
    except Exception:
        pass
    prod = _commit(
        "generation_agent",
        [{"output_uri": g.get("output_uri")} for g in generation_proposals],
        f"generation: {len(generation_proposals)} assets",
    )

    # ---- Stage 22: PublisherAgent -------------------------------------------
    from src.agents.publisher import PublisherAgent

    publisher = PublisherAgent()
    pub_result = publisher.run({
        "production": {
            "id": prod.id,
            "title": topic,
            "metadata": {
                "doi": "10.1000/example-2026",
                "authors": ["Open Production"],
                "date": "2026-07-29",
            },
            "scenes": [],
        },
        "platforms": [intent.platform or "youtube"],
    })
    pub_proposals = pub_result.get("proposals") or []
    prod = _commit(
        "publisher",
        [{"platform": (p.get("manifest") or {}).get("platform")} for p in pub_proposals],
        f"publisher: {len(pub_proposals)} manifests",
    )

    # ---- Publication gate ---------------------------------------------------
    pub_metadata = {
        "doi": "10.1000/example-2026",
        "authors": ["Open Production"],
        "date": "2026-07-29",
    }
    pub_ok, pub_reason = publication_gate.check(pub_metadata)
    prod = _safe_apply(
        svc,
        prod,
        _gate_entry(
            gate_name="publication_gate",
            claim_id="doc-metadata",
            decision_status="publish_ok" if pub_ok else "publish_rejected",
            reason=pub_reason,
            evidence=pub_metadata,
        ),
    )

    return svc.load(prod.id)


if __name__ == "__main__":
    raise SystemExit(0)
