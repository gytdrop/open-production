# Inspiration Notes — Open Production

How the patterns from four inspiration repos informed Open Production's design. **Patterns only. No code imported.** Each pattern below is what we *generalized* into our medium-blind kernel — not what we copied.

---

## Inspiration map

| Repo | What we took | What we left behind | Where it lives in Open Production |
|---|---|---|---|
| OpenMontage (calesthio) | The "live studio" pattern; Replay Run; provider scoring with audit trail | Video-only architecture | `docs/architecture/architecture.md` §"Inspired by"; `bob-sessions/01-codebase-exploration/transcript.md` (Bob audited the actual dispatcher loop) |
| claude-code-video-toolkit (digitalsamba) | The "skill catalog + command surface" pattern; template-driven projects | Claude Code dependency; specific toolchain | `docs/roadmap/v0.2-video.md` (planned) |
| hyperframes-motion-director (geekjourneyx) | The brief-confirm-produce two-phase flow | Chinese-first defaults; HyperFrames dependency | Stage 2 (Creative Reframing) — same gate shape |
| video-shotcraft (Vincentwei1021) | The "named motion primitive" pattern (shot cards); aesthetic QA criteria | Remotion dependency; 161 specific styles | `docs/roadmap/v0.2-video.md` (planned shot primitive library) |

---

## Pattern 1 — Live studio + Replay Run (OpenMontage)

**Source pattern:** OpenMontage's Backlot UI surfaces production state in real time. Each project on disk has a live board that fills as the pipeline runs. When a run completes, REPLAY RUN lets you scrub the whole production from its timestamps.

**What we generalized:** A medium-blind "live state" view. The kernel's Mermaid diagram (in `docs/architecture/architecture-diagram.mmd`) shows this — five stages light up as the pipeline runs, gates fire visibly, and `audit_trail.jsonl` is the replayable timeline.

**Why it's important:** Judges score on Feasibility. A "live state" view + audit-trail replay is the difference between "demo" and "production-traceable system."

**Concrete evidence in Open Production:**
- `src/audit/recorder.py` — Bob-built audit recorder, 50 lines, thread-safe.
- `scripts/run_demo.py` — Bob-built demo entry point that writes audit_trail.jsonl on every gate decision.
- `examples/output/audit_trail.jsonl` — 8 entries showing live gate firings (3 evidence_gate, 1 consistency_gate, 1 publication_gate).

---

## Pattern 2 — Skill catalog + command surface (claude-code-video-toolkit)

**Source pattern:** The toolkit exposes skills (markdown files describing capabilities like Remotion, ElevenLabs, Flux) and commands (`/video`, `/setup`, `/scene-review`). The agent reads the catalog and orchestrates.

**What we generalized:** Our Capability contracts — typed, versioned, self-describing. Plugins declare capabilities in `manifest.json`-style descriptors. The kernel invokes them through the typed ABI (3 surfaces: Capability, Application, Annotation).

**Why it's important:** This is how the kernel stays extensible without bloating. Each new vertical adds skills, not kernel features.

**Concrete evidence in Open Production:**
- `src/agents/base.py` — base agent class (Bob session 4 scaffold).
- `src/agents/creative_reframing.py` — the Bob-built creative_reframing agent implements the Capability pattern.
- `src/validation/gates.py` — the three gate classes are also Capabilities (EvidenceGate, ConsistencyGate, PublicationGate).

---

## Pattern 3 — Brief → confirm → produce (hyperframes-motion-director)

**Source pattern:** The skill explicitly stops after creating `BRIEF_DESIGN_PROPOSAL.md` and waits for human confirmation before producing assets. This is the **AI-as-creative-partner** pattern in its most explicit form.

**What we generalized:** Stage 2 (Creative Reframing) in Open Production's 5-stage pipeline. The `creative_reframing` agent proposes three angles (skeptic, advocate, contrarian). The user picks one. *Then* the system produces. The system doesn't generate content unilaterally.

**Why it's important:** This is the rubric's exact framing: *"How can AI act as a creative partner rather than simply a content generator?"* The hyperframes-motion-director pattern is the explicit answer. We cite it.

**Concrete evidence in Open Production:**
- `src/agents/creative_reframing.py` (189 lines, Bob-built) — proposes 3 angles, validates, falls back on failure.
- `tests/test_creative_reframing.py` (9 tests) — covers happy path, malformed retry, missing-context, fallback, angle-distinctness.
- The demo video shot list at `docs/demo/demo-story.md` — at 1:05–1:45, judges see the user *picking* an angle.

---

## Pattern 4 — Named motion primitives (video-shotcraft)

**Source pattern:** A catalog of 104 named shot recipes (e.g., `deck-deal-flyin`, `row-embed`, `spotlight-hero-card`) with documented motion techniques (timing, easing, choreography). The agent picks from the catalog by name.

**What we generalized:** The concept of *named primitives* generalizes beyond video. In Open Production's medium-blind framework, a Transform is a named, typed, idempotent operation. Future verticals will define Transform libraries (e.g., `flux-image-generate`, `tts-synthesize`, `remotion-compose`).

**Why it's important:** It shows our kernel can absorb the "named primitive" pattern without modification. v0.2 video vertical would slot in.

**Concrete evidence in Open Production:**
- `docs/architecture/architecture.md` §"The five primitives" — Transform is one of the five.
- `src/agents/creative_reframing.py` — itself a named, typed Transform.
- `docs/roadmap/v0.2-video.md` — planned (Boris's auto-queue, not built).

---

## What we did NOT take from these repos

- **Specific toolchains** (Remotion, ElevenLabs, Flux, Qwen3-TTS, ACE-Step). Our v0.1 ships with MockLLMClient only. v0.2 would integrate.
- **Specific UI components** (Backlot, HyperFrames). Our demo is a CLI run with JSONL output. v0.2 would add UI.
- **Specific aesthetics** (Ink Press paper-ink-amber style). Our v0.1 doesn't ship aesthetics; that's a v0.2 vertical concern.
- **Specific domain defaults** (Chinese-first, 9:16 vertical). Our kernel is medium-blind by design.
- **Specific rendering paths** (Remotion render concurrency flags). Our v0.1 doesn't render video at all.

---

## Why these patterns but not their code

Three architectural reasons:

1. **Medium-blind constraint.** Our kernel knows nothing about video, image, audio, or any creative medium. Importing Remotion or HyperFrames violates this constraint.
2. **Deadline.** 5 days. Importing 4 repos is days of work, all of it regression risk.
3. **Rubric scoring.** The rubric scores Innovation, Challenge Fit, Feasibility, Technical Execution, Real-World Impact. We score well on all five without code imports. Imports don't move the needle; they might break tests.

---

## What's left for the judges to see

- **Bob's 16.7 KB audit of OpenMontage** (`bob-sessions/01-codebase-exploration/transcript.md`) — proof we engaged with the inspiration at the source-code level, not just marketing-level.
- **The Mermaid architecture diagram** (`docs/architecture/architecture-diagram.mmd`) — visual proof that the five-primitive kernel is real and demoable.
- **The audit trail** (`audit_trail.jsonl` after running `make demo`) — proof the system is production-traceable, not a slide.
- **The brief-confirm-produce flow** in the demo video at 1:05–1:45 — proof of AI-as-creative-partner, with explicit citation to the hyperframes-motion-director pattern.

---

## References in this doc

- OpenMontage: `https://github.com/calesthio/OpenMontage.git`
- claude-code-video-toolkit: `https://github.com/digitalsamba/claude-code-video-toolkit`
- hyperframes-motion-director: `https://github.com/geekjourneyx/hyperframes-motion-director`
- video-shotcraft: `https://github.com/Vincentwei1021/video-shotcraft`
- RFC-0001-FIXES.md: `D:\openclaw\creative-platform-design\RFC-0001-FIXES.md`
- Open Production architecture doc: `docs/architecture/architecture.md`
- Bob session 1 transcript: `bob-sessions/01-codebase-exploration/transcript.md`