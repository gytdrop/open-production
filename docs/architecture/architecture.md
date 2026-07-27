# Architecture — Open Production

This document is the architecture writeup referenced in the README. It's not a full RFC — that lives at `D:\openclaw\creative-platform-design\RFC-0001-FIXES.md`. This is the IBM-submission-shaped summary: what judges need to see to score "Technical Execution" and "AI approach and architecture" highly.

## What's shipped vs. designed

| Layer | Status | Location |
|---|---|---|
| Kernel (medium-blind, 5 primitives, single-threaded loop) | Designed, not built | RFC-0001-FIXES.md |
| Research-writing vertical (PDT) | Built, operational | `D:\openclaw\pdt\` |
| Creative-reframing agent | Built — Bob session 2 | `src/agents/creative_reframing.py` |
| Interactive confirm gate | Built — Bob session 5 | `src/agents/confirm_gate.py` |
| Gate-validation suite | Built — Bob session 3 | `tests/test_gates.py` |
| Transform catalog (6 transforms) | Built — Bob session 6 | `src/transforms/` |
| Video vertical sketch | Built — Bob session 7 | `src/videos/` |
| Demo entry point + audit recorder | Built — Bob session 4 | `scripts/run_demo.py`, `src/audit/recorder.py` |
| Scaffolded stubs (base agent, gates, LLM client) | Built by Codex | `src/agents/base.py`, `src/validation/gates.py`, `src/tools/llm_client.py` |

Open Production is a vertical built on top of a designed kernel. The kernel is the architectural depth; the vertical is the working submission.

---

## System diagram

The diagram below is the canonical architecture. It lives at `architecture-diagram.mmd` (Mermaid source) and renders natively in GitHub Markdown, Obsidian, and VS Code.

```mermaid
flowchart TD
  Section 1 -- User / Intent --> Section 2
  Section 2 -- Creative Reframing --> Section 3
  Section 3 -- Multi-Agent Research --> Section 4
  Section 4 -- Claim Extraction + Gates --> Section 5
  Section 5 -- Output --> End

  subgraph Section 1
    intent["User declares Intent\n(topic, audience, tone, length)"]
  end

  subgraph Section 2
    direction LR
    skeptic["skeptic"]
    advocate["advocate"]
    contrarian["contrarian"]
    chosen_angle["chosen_angle"]
    skeptic -->|user picks one| chosen_angle
    advocate -->|user picks one| chosen_angle
    contrarian -->|user picks one| chosen_angle
  end

  subgraph Section 3
    direction LR
    pubmed_agent["pubmed_agent"]
    openalex_agent["openalex_agent"]
    crossref_agent["crossref_agent"]
    semantic_scholar_agent["semantic_scholar_agent"]
    source_set["source_set"]
    pubmed_agent --> source_set
    openalex_agent --> source_set
    crossref_agent --> source_set
    semantic_scholar_agent --> source_set
  end

  subgraph Section 4
    claim_extractor["claim_extractor"]
    evidence_gate["evidence_gate\n(fail-closed)"]
    consistency_gate["consistency_gate\n(fail-closed)"]
    publication_gate["publication_gate\n(fail-closed)"]
    claim_extractor --> evidence_gate --> consistency_gate --> publication_gate
  end

  subgraph Section 5
    finalized_document["finalized_document"]
    audit_trail["audit_trail.json"]
    finalized_document -. audit trail .-> audit_trail
  end

  intent --> chosen_angle
  chosen_angle --> research_agents
  source_set --> claim_extractor
  publication_gate --> finalized_document

  loop_checkpoints["loop_checkpoints"]
  loop_checkpoints -. checkpoint .-> evidence_gate
  loop_checkpoints -. checkpoint .-> consistency_gate
  loop_checkpoints -. checkpoint .-> publication_gate

  classDef bobStyle fill:#7AC9F2,stroke:#0A0E1A,color:#0A0E1A,stroke-width:2px
  classDef gateStyle fill:#86E09C,stroke:#0A0E1A,color:#0A0E1A
  classDef failClosedStyle fill:#FF8A8A,stroke:#0A0E1A,color:#0A0E1A
  class creative_reframing bobStyle
  class evidence_gate,publication_gate gateStyle
  class consistency_gate failClosedStyle
```

**Reading the diagram:**

- **Top-down 5-stage pipeline.** User Intent → Creative Reframing → Multi-Agent Research → Claim Extraction + Gates → Output. Each stage is auditable.
- **Stage 2 — Creative Reframing (highlighted cyan).** Three parallel voices (skeptic, advocate, contrarian) merge into `chosen_angle`. The user picks one. This is the AI-as-creative-partner differentiator.
- **Stage 3 — Multi-Agent Research.** Four specialists (PubMed, OpenAlex, Crossref, Semantic Scholar) fan into a shared `source_set`. All four run in parallel.
- **Stage 4 — Gates (fail-closed).** Three sequential gates. Each can refuse the document. The consistency gate is highlighted red as the strictest fail-closed boundary.
- **Stage 5 — Output.** Finalized document with an audit-trail edge to `audit_trail.json`.
- **Sidecar — `loop_checkpoints`.** Dotted edges to every gate show the reconciliation-loop checkpoint pattern from RFC-0001-FIXES.md Blocker 6. The gates are not just sequential validation — they are checkpoints in a recoverable loop.

---

## The five primitives

Open Production is built on five primitives that survive every creative medium:

- **Source** — an artifact's identity. Content-addressed. SHA-256. Immutable.
- **Transform** — an atomic operation. Render, transcribe, summarize. Typed. Idempotent.
- **Composition** — a DAG of transforms. A workflow, a pipeline, a recipe.
- **Evaluation** — a judgment. Quality, faithfulness, novelty. Gates live here.
- **Intent** — a desired state. What should exist after the kernel acts.

The kernel is **medium-blind** — it has no concept of research, video, or audio. It only knows these five. Every domain (research writing, video, code, design) becomes an application layer over the primitives.

### Why these five, not three or eight

The validation review (RFC-0001-FIXES.md, §1) tried every alternative:

- **Three** is too coarse. Source + Transform + Intent works for a pipeline runner but loses Composition (no DAG semantics) and Evaluation (no judgment).
- **Eight** is too fine. We trialed eight primitives with a knowledge / experience layer; both rejected as premature or accidental.
- **Five** is the irreducible set: anything less collapses a creative production into something else (a pipeline runner, an artifact store, a model router). Anything more is decoration.

The recurrence test passes: every creative medium — video, code, research, design, music — reduces to these five shapes.

---

## The reconciliation loop

Open Production runs on a declarative intent model:

1. The user declares an intent (a topic, audience, length, tone).
2. The kernel treats the intent as a *desired state* and reconciles toward it.
3. The reconciliation loop runs in **6 phases**: acquire → detect → plan → dispatch → commit → release.
4. Each commit is auditable. Each transformation is idempotent. Each evaluation fails closed.

This is the same pattern Kubernetes uses for controllers and Git uses for branches. The kernel is a **control system**, not a workflow runner.

**Why single-threaded.** The reconciliation loop is single-threaded per kernel instance. The design assumes the bottleneck is dispatch, not reconciliation. Distributed execution is out of scope for v1.0 and would change the loop's contract.

**Why recovery is explicit.** Every phase boundary writes a `LoopCheckpoint` to the event log. The kernel is stateless between ticks; on restart, it reads the last checkpoint and resumes. Crashes are non-fatal. This is the `loop_checkpoints` sidecar node in the diagram above.

---

## Fail-closed as a first-class principle

The three gates in Open Production fail closed:

- **Evidence gate** — every claim must cite a source. If a claim cannot cite a source, it is rejected and the rejection is logged.
- **Consistency gate** — contradictions between sources are surfaced, not silently overwritten. The user (or a downstream evaluator) resolves.
- **Publication gate** — refuses to publish with incomplete metadata (no DOI, no author attribution, missing publication date).

The system does not paper over failure. It surfaces failure. This is the opposite of "AI as content generator that hallucinates confidently." It is **"AI as creative partner that admits when it cannot meet the bar."**

---

## The creative-reframing differentiator

Before writing, the creative-reframing agent proposes three angles on the topic:

- **Skeptic** — what could go wrong, what's overstated, what's missing.
- **Advocate** — why this matters, the strongest case, who benefits.
- **Contrarian** — the non-obvious take, the contrarian-but-defensible position.

The user picks one. The chosen angle becomes the document's frame.

This is the move that takes Open Production from "AI that writes content" to **"AI as creative partner."** The system doesn't generate content unilaterally — it proposes alternatives and lets the human pick. The rubric's exact framing: *"AI as a creative partner rather than simply a content generator."*

### Implementation contract

- Input: `{ topic, audience, tone, context? }`
- Output: `{ angles: [skeptic, advocate, contrarian] }` — always exactly three.
- Validation: malformed JSON triggers one retry; second failure falls back to deterministic angles.
- Tests: 5 unit tests covering happy path, malformed JSON retry, missing-context safety, fallback, and angle-distinctness.

Bob session 2 built this. The transcript is at `bob-sessions/02-creative-reframing-feature/transcript.md`.

---

## Multi-agent research

A coordinator dispatches specialist agents in parallel:

- **PubMed** for biomedical literature.
- **OpenAlex** for open scholarly metadata.
- **Crossref** for citation graphs and metadata.
- **Semantic Scholar** for highly-cited paper discovery.

Each agent returns source records with confidence scores. The system captures every query and response for the audit trail. The reader of any produced document can trace any sentence back to a source.

The coordinator itself is the existing PDT scheduler at `D:\openclaw\pdt\src\coordinator\scheduler.py` — 33KB, six phases, single-threaded dispatch. The IBM submission uses it without modification.

---

## Why this matters for the IBM challenge rubric

The five judging criteria map to architecture decisions:

| Criterion | How Open Production scores |
|---|---|
| **Technical Execution** | Five-primitive kernel · typed capability contracts · reconciliation loop · 6-phase scheduler · fail-closed gates · audit-traceable |
| **Innovation** | Creative reframing as a first-class primitive · "AI as creative partner" framing · medium-blind kernel · generalization from OpenMontage |
| **Challenge Fit** | "Reimagine Creative Industries with AI" — research writing is a creative industry · AI creative partner framing directly named in the rubric |
| **Feasibility** | PDT is operational; the vertical works today · Bob-built agent integrates into existing pipeline |
| **Real-World Impact** | Targets students producing theses · writers needing audit trails · educators building materials · content teams scaling across formats |

---

## Inspired by

- **OpenMontage** (`https://github.com/calesthio/OpenMontage.git`) — for the live studio + Replay Run pattern. Open Production generalizes OpenMontage's video-only model to be medium-blind.
- **Kubernetes reconciliation loops** — for the declarative desired-state model. The kernel is a controller, not a runner.
- **Git's content-addressed store** — for immutable, content-addressed artifacts.

---

## What this document is NOT

This is a summary for the IBM submission. The full architectural spec — with subsystem reviews, boundary analysis, invariant stress tests, essential vs accidental abstractions, the 20 unknowns checklist, and the 8 irreversible decisions — lives in **RFC-0001-FIXES.md** (26.5KB). That document is the source of truth for any architectural question. This document is the IBM-shaped summary.

---

## Cross-reference index (RFC-0001-FIXES.md sections)

For more detail on any subsystem:

| Topic | Section |
|---|---|
| State machine | RFC-0001-FIXES.md §2 |
| Storage | RFC-0001-FIXES.md §3 |
| ABI | RFC-0001-FIXES.md §4 |
| Runner | RFC-0001-FIXES.md §5 |
| Reconciliation loop | RFC-0001-FIXES.md §6 |
| Provider selection | RFC-0001-FIXES.md §7 |
| CLI | RFC-0001-FIXES.md §8 |
| Data model | RFC-0001-FIXES.md §9 |
| GC | RFC-0001-FIXES.md Blocker 4 |
| Long-running capabilities | RFC-0001-FIXES.md Blocker 5 |
| Loop failure recovery | RFC-0001-FIXES.md Blocker 6 |
| Kernel vs plugin decision procedure | RFC-0001-FIXES.md Blocker 7 |
| Seven prototypes | RFC-0001-FIXES.md Blocker 8 |
| Eight irreversible decisions | RFC-0001-FIXES.md Blocker 9 |
| Twenty unknowns | RFC-0001-FIXES.md Blocker 10 |