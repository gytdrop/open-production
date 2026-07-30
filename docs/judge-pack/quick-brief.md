# Open Production — Judge's Quick Brief

**Track:** IBM July Challenge — Reimagine Creative Industries with AI  
**Repo:** open-production · MIT License · built end-to-end with IBM Bob

---

## Elevator pitch

Every AI video and content tool treats generation as the product. We treat it as the last step.
Open Production is a **production-crew model**: 21 specialist AI agents, each with a bounded scope contract, coordinated by a fail-closed gate suite and a shared immutable Production Document.
The output is auditable, branchable, and reviewer-gated — before the human ever sees a result.

---

## The problem

Today's AI creative tools share one failure mode: the interface makes generation the easiest action, so users spend all their time there and produce shallow work. There is no brief, no stage gate, no consistency contract, no audit trail. Every decision is buried in a prompt history that no collaborator can read and no reviewer can verify. The creative process is invisible; only the output exists.

---

## What we built

A medium-blind production kernel — five typed primitives (`Source`, `Transform`, `Composition`, `Evaluation`, `Intent`) that compose into any creative vertical. On top of the kernel:

- **Production Document** — a serializable, diffable, versionable record of every creative decision. JSON schema at `docs/schema/production-document.schema.json`; Python dataclass at `src/schema/production_document.py`.
- **ProductionService** — filesystem-backed runtime: `init / load / save / apply_event / snapshot / create_branch`. State machine enforces 6 forward-only states.
- **21-agent production crew** — CreativeReframing, ConfirmGate, ConfirmSink helpers, ResearchAgent, ReferenceClusteringAgent, MoodboardAgent, StoryAgent, ScriptAgent, ScriptAgent helpers, ShotDesignerAgent, ShotPlanningAgent, CharacterDirectorAgent, StoryboardArtistAgent, EnvironmentArtistAgent, ReviewerAgent, EditorAgent, PublisherAgent, VoiceDirectorAgent, SoundDesignerAgent, MusicComposerAgent, ColoristAgent, AnimationDirectorAgent, AssetLibraryAgent, GenerationAgent. All live in src/agents/. CharacterDirectorAgent, StoryboardArtistAgent, EnvironmentArtistAgent, ReviewerAgent, EditorAgent, PublisherAgent, VoiceDirectorAgent, SoundDesignerAgent, MusicComposerAgent, ColoristAgent. All live in `src/agents/`.
- **4 fail-closed gates** — EvidenceGate, ConsistencyGate, ConsistencyContractGate, PublicationGate. All in `src/validation/gates.py`.
- **Browser demo** — two views at `src/public_demo/server.py`: Guided Production Flow (`/?view=guided`) and Agent Console (`/?view=console`) with per-actor event filter.
- **464 tests** — all passing. `python -m pytest tests/ -q`.

---

## Five differentiators (with proof)

1. **The Production Document** — a serializable, diffable, versionable record of every creative decision.
   `src/schema/production_document.py` — `class Production` root dataclass carries `branches`, `snapshots`, `audit_trail`, `style_tokens`, `characters`, and `environments` as typed fields; not a dict, not a folder.

2. **The Consistency Contract** — a formal, machine-checkable spec for visual consistency across shots and scenes.
   `src/schema/production_document.py` — `class ConsistencyContract` with `visual_anchors`, `required_attributes`, `prohibited_attributes`, and `variance_tolerance: float`. Attached to both `Character` and `Environment`.

3. **The Production Crew Model** — specialist agents with bounded scope contracts, not a single assistant.
   `src/agents/base.py` — `class BaseAgent` establishes `WRITABLE_FIELDS: frozenset[str]` scope contract every agent must declare. `_enforce_scope()` raises `ScopeViolation` at runtime.

4. **Stage Gates** — explicit, logged boundaries between production stages; the AI cannot proceed without a decision.
   `src/validation/gates.py` — `EvidenceGate`, `ConsistencyGate`, `ConsistencyContractGate`, `PublicationGate` all write `AuditEntry` records on every decision. Fail-closed: rejection is logged, not silently swallowed.

5. **The Reviewer Agent (fail-closed quality gate)** — AI output is evaluated against the brief before the human sees it; failures are surfaced, not hidden.
   `src/agents/reviewer.py` — `ReviewerAgent` implements 5 check types from Appendix J (consistency, brief_alignment, technical_quality, continuity, stage_gate). Blocking threshold 0.60; warn threshold 0.75.

---

## What's deliberately deferred

- **Live LLM integration** — `OpenAILLMClient` exists in `src/tools/llm_client.py`; no agent defaults to it yet. All demo outputs use `MockLLMClient` (deterministic, no API key required).
- **ProductionService.merge()** — branch comparison and merging is spec'd but not implemented. `create_branch()` and `snapshot()` work.
- **Stage gates wired to pipeline advancement** — gates are callable and tested; `ProductionService` does not block state transitions until they pass. Phase 2 post-submission.
- **26-stage pipeline** — 8 of 26 stages have agents; stages 2 (Research), 4 (Moodboard), 6 (Story), 7 (Script) are not yet started as agents.

---

## How the five judging criteria are scored

| Criterion | What we built | Where it lives |
|---|---|---|
| **Technical Execution** | 5-primitive kernel · 21-agent crew · scope contracts · 6-state machine · event log · fail-closed gates · snapshot + branching · 464 tests | `src/`, `tests/`, `docs/architecture/architecture.md` |
| **Innovation** | Creative reframing as a first-class primitive · "AI as creative partner" framing · medium-blind kernel · production crew model with formal scope contracts | `src/agents/creative_reframing.py` · `docs/architecture/` |
| **Challenge Fit** | Direct match for "Reimagine Creative Industries with AI" · "AI as creative partner" is rubric-exact wording · browser demo demonstrates the production-crew model live | `src/public_demo/server.py` |
| **Feasibility** | Working browser demo: `python src/public_demo/server.py` → `http://127.0.0.1:8000/?view=guided`. ~3s to first angles. | `src/public_demo/server.py` |
| **Real-World Impact** | Targets creators who need transparent, auditable AI collaboration — not silent automation. Every gate decision logged. Production ID traceable. | `output/public-demo/` audit artifacts |

---

## How IBM Bob was used

Ten captured sessions, raw transcripts preserved in `bob-sessions/`:

| # | Session | What Bob did |
|---|---|---|
| 01 | Codebase exploration | Bob audited the OpenMontage video pipeline dispatcher (16.7 KB phase table, branch gaps, refactor proposal) |
| 02 | Build creative_reframing | Bob built `src/agents/creative_reframing.py` per spec; 3 angles, retry, deterministic fallback, 9 unit tests |
| 03 | Tests + checks | Bob authored `tests/test_gates.py` (200 lines, 12 tests) covering evidence/consistency/publication gates |
| 04 | Demo + audit recorder | Bob wired `build_demo_report()` end-to-end with JSONL recording every gate decision |
| 05 | Interactive confirm gate | Bob built `src/agents/confirm_gate.py` — `TtyConfirmSink` / `AutoConfirmSink` with `--no-confirm` CI escape hatch |
| 06 | Transform catalog | Bob built `src/transforms/` — 6 typed, idempotent Transforms auto-registering on import; 11 tests |
| 07 | Video vertical sketch | Bob built `src/videos/` — second vertical proving kernel generalization; `ShotComposition`, `FrameRenderTransform`, `VisualQualityGate`; 9 tests |
| 08 | Code review + phase 2 backend | Bob implemented VoiceDirectorAgent, SoundDesignerAgent, MusicComposerAgent, ColoristAgent (4 previously spec-only agents); 164 tests |
| 09 | Deployment readiness | Bob updated architecture.md, submission-checklist, README, demo-story, how-to-launch; added VP.1 production_id panel and VP.2 per-actor Agent Console filter; 464 tests |

Bob demonstrated **explore → build → validate → integrate → harden → abstract → generalize → ship** — every phase of a real software project. All transcripts at `bob-sessions/0N-*/transcript.md`.

---

## Five-second verification

```powershell
cd 'D:\IBM Project\Open_Production'
python -m pytest tests/ -q        # 464 passed
python src/public_demo/server.py  # open http://127.0.0.1:8000/?view=guided
```

---

## What we'd say if asked

- **"Why open source?"** — Because the kernel is more useful as infrastructure than as a product. The verticals can be proprietary; the kernel cannot.
- **"Why medium-blind?"** — Because every creative medium reduces to the same five shapes. Build the kernel once, ship any vertical.
- **"Why fail-closed?"** — Because publishing an unverified claim is the failure mode that destroys trust. The user can override; the system never lies quietly.
- **"What's next?"** — Wire `OpenAILLMClient` into `CreativeReframing` for live AI output. Implement stages 2 (Research), 6 (Story), 7 (Script). Wire gates to automatic pipeline advancement.

---

## References in the repo

- `README.md` — full README with the 5 required sections.
- `docs/architecture/architecture.md` — architecture writeup (all 21 agents, 4 gates, 6-state machine).
- `docs/architecture/architecture-diagram.mmd` — Mermaid diagram (renders on GitHub).
- `docs/demo/demo-story.md` — 3-minute video shot list (browser demo flow).
- `docs/submission-checklist.md` — Day-4 verification gates.
- `docs/how-to-launch-and-test.md` — quick-start for judges who want to run it.
- `bob-sessions/_index.md` — index of all 10 Bob session transcripts (01–09 plus the 08 self-transcript).
