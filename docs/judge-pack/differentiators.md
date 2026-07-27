# Open Production — Five Differentiators (Evidence)

> Each claim is paired with the file and line that prove it exists in the
> committed codebase today. No forward-looking language.

---

## 01 · Production Document
> `docs/schema/production-document.schema.json:7` — `"required": ["schema_version", "id", "state", "intent", "scenes", "audit_trail"]`
> `docs/schema/production_document.py:316` — `class Production` root dataclass carrying `branches`, `snapshots`, `audit_trail`, `style_tokens`, and `characters` as typed fields
> `src/schema/production_document.py` — runtime mirror of the schema dataclass used by `ProductionService`
> `src/service/production_service.py` — `ProductionService.save()` serializes a `Production` to `production.json`; `ProductionService.apply_event()` returns a new immutable `Production` on each event, making every state diffable
> A single schema-enforced root object captures every creative decision and makes it serializable, diffable, and versionable by construction — not a folder of video files.

---

## 02 · Consistency Contract
> `docs/schema/production_document.py:101` — `class ConsistencyContract` with `visual_anchors`, `required_attributes`, `prohibited_attributes`, and `variance_tolerance: float` as first-class fields
> `docs/schema/production_document.py:118` — `Character.consistency_contract: Optional[ConsistencyContract]`; same type on `Environment` at line 131
> The contract is in the object graph on every character and environment — not a convention buried in a prompt — so the Reviewer agent can gate against it programmatically.

---

## 03 · Production Crew Model
> `src/agents/base.py:9` — `class BaseAgent` with `run(input: dict) -> dict` as the bounded scope contract every specialist agent must honour
> `src/agents/creative_reframing.py:67` — `class CreativeReframing(BaseAgent)` is a concrete specialist with one declared job: return three distinct angles before writing begins
> The codebase ships both the contract and a working specialist, proving the crew pattern rather than a single monolithic assistant.

---

## 04 · Stage Gates
> `src/agents/confirm_gate.py:33` — `class ConfirmSink(Protocol)` with `ask(request) -> ConfirmResponse`; `declined=True` halts the flow at any stage boundary
> `src/validation/gates.py:10` — `EvidenceGate`, `ConsistencyGate`, and `PublicationGate` are sequenced gate classes that write `status: "rejected"` or `status: "accepted"` to the audit trail via `src/audit/recorder.py:23`
> Stage boundaries are not advisory: the ConfirmSink protocol enforces a human decision before proceeding and every verdict is persisted as a structured audit entry.

---

## 05 · Reviewer Agent
> `src/validation/gates.py:ConsistencyContractGate` — `check(contract, result) -> (bool, str)` stops fast on the first required-attribute miss or prohibited-attribute presence; enforced before any generation reaches output
> `src/videos/quality_evaluation.py:16` — `class VisualQualityGate(Transform)` registered as `"video.quality_gate"` via `register_transform`; cannot be skipped without removing it from the registry
> `src/videos/quality_evaluation.py:26` — `apply()` returns `QualityVerdict(passed=score >= self.min_score, ...)` per frame before any output reaches the human
> The gate is fail-closed by construction: a frame only passes if its score clears the threshold, and the gate is registered as a named transform so it sits permanently in the pipeline.

> **Note:** The Agent Console (the UI surface for the director crew) is parked per submission-window scope. The underlying event log is shipped via `ProductionService` (`src/service/production_service.py`); the console UI is an honest deferral.

---

*Evidence extracted from committed source files. All file:line references verified against the current working tree. Phase 1 (ProductionService + dual-artifact demo_flow) and Phase 3 (ConsistencyContractGate) shipped; Agent Console UI deferred post-submission.*
