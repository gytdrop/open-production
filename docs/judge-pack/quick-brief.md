# Open Production — Judge's Quick Brief

**Track:** IBM July Challenge — Reimagine Creative Industries with AI
**Repo:** open-production · MIT License · built end-to-end with IBM Bob

---

## Elevator pitch

Every AI video and content tool treats generation as the product. We treat it as the last step.
Open Production is a production-process engine: a medium-blind kernel plus two working verticals (research writing, video primitives) built on the same five primitives.
The output is auditable, branchable, and reviewer-gated — before the human ever sees a result.

---

## The problem

Today's AI creative tools share one failure mode: the interface makes generation the easiest action, so users spend all their time there and produce shallow work. There is no brief, no stage gate, no consistency contract, no audit trail. Every decision is buried in a prompt history that no collaborator can read and no reviewer can verify. The creative process is invisible; only the output exists.

---

## What we built

A medium-blind production kernel — five typed primitives (`Transform`, `Sequence`, `Filter`, `Registry`, `TransformResult`) that compose into any creative vertical. On top of the kernel: a research-writing vertical (creative reframing → multi-source research → evidence gate → contradiction detection → publication gate) running end-to-end with a JSONL audit trail, and a video-vertical proof (`ShotComposition`, `FrameRenderTransform`, `VisualQualityGate`) showing the kernel generalises beyond text. The schema layer (`docs/schema/production-document.schema.json`, `docs/schema/production_document.py`) defines the canonical `Production` document — serializable, diffable, branchable. The CLI bridge design (`docs/architecture/cli-bridge-design.md`) specifies the `ProductionService` runtime that sits between the CLI surface and the storage layer; it is designed and spec'd, not yet implemented.

---

## Five differentiators (with proof)

1. **The Production Document** — a serializable, diffable, versionable record of every creative decision.
   `docs/schema/production-document.schema.json:7` — `"required": ["schema_version","id","state","intent","scenes","audit_trail"]` locks the full decision record as non-optional.
   `docs/schema/production_document.py:316` — `class Production` root dataclass carries `branches`, `snapshots`, `audit_trail`, `style_tokens`, and `characters` as typed fields; not a dict, not a folder.

2. **The Consistency Contract** — a formal, machine-checkable spec for visual consistency across shots and scenes.
   `docs/schema/production_document.py:101` — `class ConsistencyContract` with `visual_anchors`, `required_attributes`, `prohibited_attributes`, and `variance_tolerance: float` as first-class fields.
   `docs/schema/production_document.py:118` — `Character.consistency_contract: Optional[ConsistencyContract]`; line 131 attaches the same type to `Environment`. The contract is in the object graph, not in a prompt.

3. **The Production Crew Model** — specialist agents with bounded scope contracts, not a single assistant.
   `src/agents/base.py:9` — `class BaseAgent` establishes the `run(input: dict) -> dict` scope contract every agent must honour; no agent can exceed its declared surface.
   `src/agents/creative_reframing.py:67` — `class CreativeReframing(BaseAgent)` is one specialist with one job: return three distinct angles before writing begins. The crew pattern is demonstrated, not just described.

4. **Stage Gates** — explicit, human-approved boundaries between production stages; the AI cannot proceed without a decision.
   `src/agents/confirm_gate.py:33` — `class ConfirmSink(Protocol)` with `ask(request) -> ConfirmResponse`: every stage transition must pass through this protocol; `declined=True` halts the flow.
   `src/validation/gates.py:10` — `EvidenceGate`, `ConsistencyGate`, and `PublicationGate` are sequenced gate classes that write `status: "rejected"` or `status: "accepted"` to the audit trail via `src/audit/recorder.py:23`.

5. **The Reviewer Agent (fail-closed quality gate)** — AI output is evaluated against the brief before the human sees it; failures are never surfaced.
   `src/videos/quality_evaluation.py:16` — `class VisualQualityGate(Transform)` registered as `"video.quality_gate"` via `register_transform`; cannot be bypassed without removing it from the registry.
   `src/videos/quality_evaluation.py:26` — `apply()` returns `QualityVerdict(passed=score >= self.min_score, ...)` per frame; the gate is fail-closed by construction, not by convention.

---

## What's deliberately deferred

- **`ProductionService` runtime** — designed and spec'd in `docs/architecture/cli-bridge-design.md`; not implemented. The CLI bridge (`op init / brief / decide / gate / snapshot / branch`) exists as a design doc only.
- **Live Reviewer agent in the video pipeline** — `VisualQualityGate` runs mock scoring (`score = 0.85`); real visual quality analysis is flagged `# Replace with real visual quality analysis in v0.2` at `src/videos/quality_evaluation.py:30`.
- **User research interviews** — the protocol is written and ready (`docs/research/user-research-plan.md`); the four persona interviews (Sam, Jordan, Alex, Morgan) are scheduled post-submission window.

---

## How the five judging criteria are scored

| Criterion | What we built | Where it lives |
|---|---|---|
| **Technical Execution** | 5-primitive kernel · 6-phase scheduler · fail-closed gates · 51 unit tests passing · content-addressed design · video vertical proof | `src/`, `tests/`, `docs/architecture/architecture.md` |
| **Innovation** | Creative reframing as a first-class primitive · "AI as creative partner" framing · medium-blind kernel · generalizes OpenMontage | `src/agents/creative_reframing.py` · `docs/architecture/` |
| **Challenge Fit** | Direct match for "Reimagine Creative Industries with AI" · "AI as creative partner" is rubric-exact wording | `project-page/project-page.md` §3 |
| **Feasibility** | Working prototype: `python scripts/run_demo.py --topic "..."` → 3 angles + audit trail in JSONL. ~30 sec end-to-end. | `scripts/run_demo.py` |
| **Real-World Impact** | Targets students producing theses · writers needing audit trails · educators · content teams | README §Problem statement |

---

## How IBM Bob was used

Seven captured sessions, raw transcripts preserved:

| # | Session | What Bob did |
|---|---|---|
| 01 | Codebase exploration | Bob audited the OpenMontage video pipeline dispatcher (16.7 KB phase table, branch coverage gaps, refactor proposal) |
| 02 | Build creative_reframing | Bob built `src/agents/creative_reframing.py` (189 lines) per spec; takes a topic and returns 3 angles |
| 03 | Tests + checks | Bob authored `tests/test_gates.py` (200 lines, 12 tests) covering evidence/consistency/publication gates |
| 04 | Demo + audit recorder | Bob wired `scripts/run_demo.py` end-to-end with `audit_trail.jsonl` recording every gate decision |
| 05 | Interactive confirm gate | Bob built `src/agents/confirm_gate.py` — `TtyConfirmSink` / `AutoConfirmSink` with `--no-confirm` CI escape hatch |
| 06 | Transform catalog | Bob built `src/transforms/` — 6 typed, idempotent Transforms auto-registering on import; 11 tests |
| 07 | Video vertical sketch | Bob built `src/videos/` — second vertical proving kernel generalization; `ShotComposition`, `FrameRenderTransform`, `VisualQualityGate`; 9 tests |

Bob demonstrated **explore → build → validate → integrate → harden → abstract → generalize** — every phase of a real software project. All transcripts at `bob-sessions/0N-*/transcript.md`.

---

## Five-second verification

```bash
git clone <repo-url>
cd open-production
make install
make test     # 51/51 passing
make demo     # prints 3 angles, writes audit_trail.jsonl, exits 0
```

---

## What we'd say if asked

- **"Why open source?"** — Because the kernel is more useful as infrastructure than as a product. The verticals can be proprietary; the kernel cannot.
- **"Why medium-blind?"** — Because every creative medium reduces to the same five shapes. Build the kernel once, ship any vertical.
- **"Why fail-closed?"** — Because publishing an unverified claim is the failure mode that destroys trust. The user can override; the system never lies quietly.
- **"What's next?"** — Video and code verticals on the same primitives. The kernel is the foundation.

---

## References in the repo

- `README.md` — full README with the 5 required sections.
- `docs/architecture/architecture.md` — architecture writeup.
- `docs/architecture/architecture-diagram.mmd` — Mermaid diagram (renders on GitHub).
- `docs/demo/demo-story.md` — 3-minute video shot list.
- `project-page/project-page.md` — full Project Page copy.
- `docs/submission-checklist.md` — Day-4 verification gates.
- `docs/how-to-launch-and-test.md` — quick-start for judges who want to run it.
- `bob-sessions/_index.md` — index of all Bob transcripts.
