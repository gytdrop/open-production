# Open Production — Project Page Draft (IBM AI Builders Challenge)

> Paste each section into the corresponding field on the platform submission page at:
> `https://aibuilderschallenge-bobhub.bemyapp.com/#/projects`

---

## Project name

**Open Production**

## Tagline (one line)

*AI as a creative partner for long-form content — research, ideation, evaluation, and audit-traceable output.*

## Challenge track

**July Challenge — Reimagine Creative Industries with AI**

---

## Section 1 — Project summary (max 200 words)

Open Production is an open-source multi-agent system that turns a creator's intent into a finished, citable document — an essay, a research report, a teaching brief, a presentation. It works in five stages:

1. **Intent declaration.** The user gives the system a topic, audience, length, and tone. It treats the goal as a *declared state* and reconciles toward it.
2. **Creative reframing.** Before writing begins, an agent proposes three angles on the topic — *skeptic*, *advocate*, *contrarian*. The user picks one. The chosen angle becomes the document's frame.
3. **Multi-agent research.** Specialist agents query four live academic sources in parallel: PubMed, OpenAlex, Crossref, and Semantic Scholar. The system captures queries, responses, and source confidence for the audit trail.
4. **Claim extraction with evidence gates.** Every claim extracted from the literature must cite a source. The evidence gate fails closed if any claim is unsupported. Contradictions between sources are surfaced, not silently overwritten.
5. **Publication gating.** The system refuses to publish a document whose sources can't be traced.

The user's role is to declare intent, react to the gates, and make creative choices. The system's role is to do the work the user shouldn't have to.

**Built with IBM Bob.** Bob explored the existing scheduler codebase and proposed a hardening refactor. Bob then designed and implemented the *creative-reframing* agent. Bob also authored and ran the test suite that proves the gates work. Seven Bob session transcripts are preserved in `bob-sessions/` as the audit trail.

---

## Section 2 — Problem

Creative industries are bottlenecked by production. Research, fact-checking, citation, structure, evaluation, and packaging are slow, expensive, and easy to do badly. Today's AI tools help with drafting text — but they don't help with the *creative process*: exploring angles, surfacing contradictions, evaluating quality, or auditing sources.

The cost of this bottleneck falls on:

- **Students** producing theses and literature reviews under deadline pressure.
- **Journalists and writers** who need audit trails they can stand behind.
- **Educators** building teaching materials late at night.
- **Marketing and content teams** producing large volumes across formats.

In every case, the failure mode is the same: a sentence is written that can't be traced to a source, a claim is made that contradicts another claim, a deadline forces a cut-and-paste shortcut that becomes a real-world cost.

---

## Section 3 — Solution

Open Production runs five stages. The first four are the production pipeline; the fifth is the differentiator that takes Open Production from "AI that writes content" to **"AI as creative partner."**

### Stage 1 — Intent declaration

The user declares:

- A topic (e.g., *"CRISPR for sickle cell disease, recent advances"*).
- An audience (researchers / educated lay / students).
- A length and a tone.
- An optional creative brief.

### Stage 2 — Creative reframing (the differentiator)

The **creative-reframing agent** proposes three angles on the topic:

- **Skeptic** — what could go wrong, what's overstated, what's missing.
- **Advocate** — why this matters, the strongest case, who benefits.
- **Contrarian** — the non-obvious take, the contrarian-but-defensible position.

The user picks one. The chosen angle becomes the document's frame. This is the move that aligns with the rubric's exact framing: *"AI as a creative partner rather than simply a content generator."*

The agent validates its output: malformed LLM responses trigger a single retry; second failure falls back to a deterministic set of angles derived from the input. The system never publishes without all three angles available.

### Stage 3 — Multi-agent research

A coordinator dispatches specialist agents in parallel:

- A **PubMed agent** for biomedical literature.
- An **OpenAlex agent** for open scholarly metadata.
- A **Crossref agent** for citation graphs and metadata.
- A **Semantic Scholar agent** for highly-cited paper discovery.

Each agent returns source records with confidence scores. The system captures every query and response for the audit trail.

### Stage 4 — Claim extraction with evidence gates

Claim-extraction agents read the source set and propose atomic claims. Each claim must:

- Be a single declarative sentence.
- Cite at least one source by ID.
- Include a confidence score.
- Be attributable to a specific page or section of the source.

The **evidence gate** fails closed. If a claim cannot cite a source, the system rejects it and logs the rejection. Hallucinations are not silently dropped — they are surfaced for review.

### Stage 5 — Contradiction detection and publication gating

A **consistency gate** runs across the claim set:

- Two claims about the same fact with different conclusions trigger a contradiction.
- The system surfaces both and asks the user to resolve — it does not pick a winner.
- A **publication gate** refuses to publish with incomplete metadata (no DOI, no author attribution, missing publication date).

---

## Section 4 — AI approach and architecture

### Approach

Open Production runs a declarative intent model on top of an append-only event log. The kernel reconciles the declared intent against the actual state of the project's artifacts. Each commit is auditable. Each transformation is idempotent. Each evaluation fails closed.

The architecture is built on five primitives that survive every creative medium:

- **Source.** An artifact's identity. Content-addressed. SHA-256. Immutable.
- **Transform.** An atomic operation. Render, transcribe, summarize. Typed. Idempotent.
- **Composition.** A DAG of transforms. A workflow, a pipeline, a recipe.
- **Evaluation.** A judgment. Quality, faithfulness, novelty. Gates live here.
- **Intent.** A desired state. What should exist after the kernel acts.

### Why this matters for AI

- **The medium-blind constraint** means the same architecture that powers research writing also powers video, audio, and code. Once the kernel is in place, every domain becomes an *application* — a plugin layer over the primitives.
- **The fail-closed constraint** means the system is auditable. Every claim traces back to a source. Every contradiction is surfaced, not silently overwritten.
- **The single-threaded reconciliation loop** means the system is reproducible. Given the same inputs and intents, the same output. Deterministic enough to test.

### System diagram

See `README.md` for the full diagram. Short version: kernel (medium-blind, 5 primitives, reconciliation loop) → research-writing vertical (PubMed, OpenAlex, Crossref, Semantic Scholar, evidence gate, consistency gate, publication gate) → output document with audit trail.

### Tradeoffs and limitations

- **Latency.** Research queries are sequential to respect rate limits. A typical run takes 30–90 seconds.
- **Cost.** Each agent run involves 4–12 LLM calls. At gpt-4o-mini pricing, a typical 1500-word document costs $0.10–$0.30 in inference.
- **Coverage.** Sources are limited to four academic APIs.
- **Languages.** English only at launch. Multilingual support is a 2.0 feature.

### Inspired by

- OpenMontage (`https://github.com/calesthio/OpenMontage.git`) — for the live studio + Replay Run pattern.
- K8s reconciliation loops — for the declarative desired-state model.
- Git's content-addressed store — for immutable, content-addressed artifacts.

---

## Section 5 — How IBM Bob was used (the audit trail)

IBM Bob was the primary development tool for Open Production. Bob was used in seven concrete, captured sessions. The transcripts are the **audit trail** — judges can review exactly what Bob did and how the human drove it.

### Session 1 — Codebase exploration

Bob read `D:\openclaw\pdt\src\coordinator\scheduler.py` (the existing multi-agent scheduler) and identified branch coverage gaps in the dispatcher loop. The proposed hardening refactor is in `bob-sessions/01-codebase-exploration/refactor-proposal.md`. The full transcript is in `bob-sessions/01-codebase-exploration/transcript.md`. This session was **read-only** — Bob analyzed, the human did not apply changes during this session.

### Session 2 — Build the creative-reframing feature

Bob designed and implemented `src/agents/creative_reframing.py` from the spec in `bob-sessions/02-creative-reframing-feature/spec.md`. The agent takes a topic + audience + tone and returns three creative angles (skeptic / advocate / contrarian) in a strict JSON shape. The implementation:

- Inherits from the existing `BaseAgent` class.
- Uses the existing LLM client wrapper (model-agnostic).
- Validates output and retries once on malformed JSON.
- Falls back to a deterministic angle set on second failure.
- Includes 9 unit tests covering happy path, malformed JSON retry, missing-context safety, fallback, and angle-distinctness.

The full transcript is in `bob-sessions/02-creative-reframing-feature/transcript.md`.

### Session 3 — Tests and gate-validation checks

Bob authored and ran the test suite for the creative-reframing feature and the gate-validation suite for the publication pipeline. Two test files:

- `tests/test_creative_reframing.py` — hardened in session 3 (9 tests total).
- `tests/test_gates.py` — new in session 3, covering evidence_gate, consistency_gate, and publication_gate with mocked external APIs.

The pytest run output is in `bob-sessions/03-tests-and-checks/check-log.md`. The transcript is in `bob-sessions/03-tests-and-checks/transcript.md`. Any bugs Bob flagged are documented as `Bob flagged:` comments in the test file.

### Session 4 — Demo entry point + audit recorder

Bob wired `CreativeReframing` + the three gates into `scripts/run_demo.py` and built `src/audit/recorder.py` (50 lines, thread-safe). The demo now runs end-to-end with `audit_trail.jsonl` recording every gate decision. The transcript is in `bob-sessions/04-demo-and-audit/transcript.md`.

### Session 5 — Interactive confirm gate

Bob built `src/agents/confirm_gate.py` — a `ConfirmSink` Protocol with `TtyConfirmSink` (interactive) and `AutoConfirmSink` (CI/`--no-confirm`) implementations. This wires the "AI as creative partner" moment: the user picks an angle before the gate pipeline fires. 5 tests in `tests/test_confirm_gate.py`. The transcript is in `bob-sessions/05-confirm-gate/transcript.md`.

### Session 6 — Transform catalog

Bob built the `src/transforms/` package — the kernel's Transform primitive made concrete. 6 named, typed, idempotent Transforms across `text/`, `filter/`, and `compose/` subpackages, all auto-registering on import. 11 tests in `tests/test_transforms.py`. The transcript is in `bob-sessions/06-transform-catalog/transcript.md`.

### Session 7 — Video vertical sketch

Bob built `src/videos/` — a second vertical on the same five primitives proving the kernel generalizes beyond research writing. Includes `ShotComposition`, `FrameRenderTransform`, `VisualQualityGate`, and a `render_video()` CLI. 9 tests in `tests/test_videos.py`. Final test total: **51/51 passing**. The transcript is in `bob-sessions/07-video-vertical/transcript.md`.

### Why this matters

The seven sessions demonstrate that IBM Bob was used for **exploration, implementation, validation, integration, hardening, abstraction, and generalization** — every phase of a real software project. The transcripts are not curated highlights — they are the actual working sessions, captured for the judges.

### Bob sessions index

| Session | Purpose | Folder |
|---|---|---|
| 01 | Codebase exploration of `coordinator/scheduler.py` | `bob-sessions/01-codebase-exploration/` |
| 02 | Build the creative-reframing agent | `bob-sessions/02-creative-reframing-feature/` |
| 03 | Tests and gate-validation checks | `bob-sessions/03-tests-and-checks/` |
| 04 | Demo entry point + audit recorder | `bob-sessions/04-demo-and-audit/` |
| 05 | Interactive confirm gate | `bob-sessions/05-confirm-gate/` |
| 06 | Transform catalog | `bob-sessions/06-transform-catalog/` |
| 07 | Video vertical sketch | `bob-sessions/07-video-vertical/` |

---

## Section 6 — Demo video link

To be added at submission.

The video is ≤ 3 minutes (cap: 3:00), uploaded as unlisted on YouTube, then switched to public before submission. The video follows the demo story in `docs/demo/demo-story.md` and hits all five judging criteria.

---

## Section 7 — GitHub repository link

To be added at submission.

The public repository contains `src/`, `tests/`, `bob-sessions/`, `docs/`, `README.md`, and a `Makefile` with a `make demo` entry point.

---

## Section 8 — Team details

**Team size:** 1 (solo).

**Team member 1:**
- Name: Kartikey
- Email: (the one used to register)
- Role: Project lead, IBM Bob driver, video presenter
- SkillsBuild course completed: *"How IBM Bob and AI Tools Are Changing the Way Solutions Are Built"*
- SkillsBuild certificate uploaded: yes

---

## Section 9 — Additional notes

### Project maturity

Open Production is at v0.1 (alpha). The research-writing vertical is functional. The video vertical skeleton is also implemented in `src/videos/` (Bob session 7) — it proves the kernel generalizes. The next verticals (code, design) are designed in `docs/architecture/` but not implemented in this submission.

### What was *not* done

- The Wild Card track was considered for August submission. Not pursued for July.
- Distributed kernels (Phase 8 in the roadmap) are out of scope.
- Multi-language support is out of scope.

### Acknowledgments

Architecture: Boris (project architect).
Implementation: Kartikey + IBM Bob.
Inspiration: OpenMontage (calesthio), K8s reconciliation loops, Git's content-addressed store.

### License

MIT.