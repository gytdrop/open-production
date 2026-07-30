# Open Production

> **AI as a creative partner for long-form video production — 21 specialist agents, fail-closed gates, and an audit-traceable production pipeline.**

An open-source multi-agent production crew for video and creative content. The primary vertical is long-form video production; research writing is an earlier experimental vertical that proved out the kernel primitives. Built with **IBM Bob** as the primary development tool.

🪷 **July 2026 — IBM AI Builders Challenge: Reimagine Creative Industries with AI**

---

## Problem statement

Creative industries are bottlenecked by production. Research, fact-checking, citation, structure, evaluation, and packaging are slow, expensive, and easy to do badly. Today's AI tools help with drafting text — but they don't help with the *creative process*: exploring angles, surfacing contradictions, evaluating quality, or auditing sources.

Creators burn hours on the seams between tools. Researchers re-do the same literature review. Writers publish claims they can't trace back to sources. Educators build materials late at night because the production loop is too long.

The bottleneck is not imagination. It is the distance between *intent* and *finished artifact*.

## Solution

**Open Production** is a creative partner that guides a production from a single intent through a crew of 21 specialist AI agents to a published, audit-traceable result. It runs five stages:

1. **Intent declaration.** You tell the system what you want — topic, audience, tone, platform.
2. **Creative reframing.** An agent proposes three creative angles — *skeptic*, *advocate*, *contrarian*. You pick one. The chosen angle becomes the production's frame.
3. **Shot design.** ShotDesignerAgent proposes three camera + lighting combinations per shot, each tied to the scene's emotional intent.
4. **Storyboarding + review.** StoryboardArtistAgent generates ASCII blocking diagrams; ReviewerAgent runs all 5 checks from Appendix J and gates delivery.
5. **Publish with evidence.** PublisherAgent generates three manifest proposals; PublicationGate checks readiness before anything is treated as publishable.

The user's role is to **declare intent, react to the gates, and make creative choices** — not to wrangle tools.

### What's novel

- **Evaluation as a first-class citizen.** Every claim passes through evidence, consistency, and publication gates. The system fails closed if a claim is unsupported. This is unusual for LLM-based writing tools — most hallucinate; Open Production audits.
- **Creative reframing.** Before writing, the system proposes three creative angles on the topic. The writer picks one. This is "AI as creative partner," not "AI as content generator" — the rubric's exact framing.
- **Audit trail by default.** Every artifact is reproducible from its inputs. The system captures which sources were queried, which claims made it through, which were rejected, and why. A reader can trace any sentence back to a source.
- **Designed to generalize.** The architecture is medium-blind: video, audio, code, design are plugin surfaces. The first vertical is research writing; the second is video.

## AI approach and architecture

Open Production is built on five primitives that survive every creative medium:

- **Source** — an artifact's identity. Content-addressed. SHA-256. Immutable.
- **Transform** — an atomic operation. Render, transcribe, summarize. Typed. Idempotent.
- **Composition** — a DAG of transforms. A workflow, a pipeline, a recipe.
- **Evaluation** — a judgment. Quality, faithfulness, novelty. Gates live here.
- **Intent** — a desired state. What should exist after the kernel acts.

The kernel is medium-blind — it knows nothing about research, video, or audio. It only knows these five. Each application (research writing, video production, code review) is a plugin layer.

The architecture is governed by a single-threaded **reconciliation loop** with six phases: acquire, detect, plan, dispatch, commit, release. The loop is declarative: you declare a desired state, the kernel reconciles it to actual state. The log is append-only; every commit is auditable.

The eight irreversible design decisions are locked in `docs/architecture/architecture.md` and the source-of-truth spec at `D:\openclaw\creative-platform-design\RFC-0001-FIXES.md`.

The submission's working code (in `src/`) is Bob-built and Codex-scaffolded:

- `src/agents/creative_reframing.py` — the Bob-built creative-reframing agent (189 lines).
- `src/validation/gates.py` — the three fail-closed gate classes.
- `src/audit/recorder.py` — Bob-built audit trail recorder (50 lines, thread-safe).
- `src/tools/llm_client.py` — MockLLMClient for deterministic demos.
- `scripts/run_demo.py` — Bob-built end-to-end entry point.
- `examples/generate_audit_fixture.py` — Codex-built audit fixture generator.

PDT (`D:\openclaw\pdt\`) is the inspiration codebase for the multi-agent research pattern; it is not part of the submission artifact itself.

### System diagram

See `docs/architecture/architecture-diagram.mmd` (Mermaid source) — renders natively in GitHub Markdown, Obsidian, and VS Code.

The diagram shows the five-stage pipeline with three fail-closed gates, the creative-reframing differentiator (Stage 2), the multi-agent research fan-out (Stage 3), and the reconciliation-loop checkpoint sidecar.

## Selected challenge theme

**July Challenge — Reimagine Creative Industries with AI.**

We chose this track because Open Production sits exactly at the seam the challenge names: **AI as a creative partner, not a content generator**. The rubric asks for "how can AI act as a creative partner rather than simply a content generator?" — that's the question the system is designed to answer.

The solution areas we align with:
- **AI creative partners** — Open Production proposes three angles per topic and lets the writer pick.
- **Storytelling and content creation tools** — research writing is the creative work we ship first.
- **Personalized creative assistants** — gates adapt to the user's quality requirements.
- **AI-powered design and visual concept tools** — the kernel is designed to generalize to image and video.

## How IBM Bob was used

IBM Bob is the primary development tool for this project. Bob was used in nine captured sessions:

1. **Codebase exploration.** Bob read the OpenMontage video pipeline dispatcher (`tools/video/video_compose.py` + `video_stitch.py`) and produced a 16.7 KB audit with a phase table, branch coverage gaps, top-3 severity ranking, and a hardening refactor proposal. The transcript is at `bob-sessions/01-codebase-exploration/transcript.md`. This session was **read-only** — Bob analyzed the inspiration codebase to ground the design in real production patterns.
2. **Build the creative-reframing agent.** Bob designed and implemented `src/agents/creative_reframing.py` (189 lines) from the spec in `bob-sessions/02-creative-reframing-feature/spec.md`. The implementation inherits from `BaseAgent`, uses the existing LLM client wrapper, validates output with one retry + deterministic fallback, and includes 9 unit tests. The transcript is at `bob-sessions/02-creative-reframing-feature/transcript.md`.
3. **Tests and gate-validation checks.** Bob authored the gate-validation suite in `tests/test_gates.py` (200 lines, 12 tests) covering the evidence_gate, consistency_gate, and publication_gate with mocked external APIs. Bob also hardened the creative_reframing test suite. The transcript is at `bob-sessions/03-tests-and-checks/transcript.md` and the run log is at `bob-sessions/03-tests-and-checks/check-log.md`.
4. **Demo entry point + audit recorder.** Bob wired `creative_reframing` + the three gates into `scripts/run_demo.py` and built `src/audit/recorder.py` (50 lines, thread-safe) plus 5 audit-recorder tests. The demo now runs end-to-end with `audit_trail.jsonl` recording every gate decision. The transcript is at `bob-sessions/04-demo-and-audit/transcript.md`.
5. **Interactive confirm gate.** Bob built `src/agents/confirm_gate.py` — a `ConfirmSink` Protocol with `TtyConfirmSink` (interactive) and `AutoConfirmSink` (CI / `--no-confirm`) implementations, wiring the "AI as creative partner" moment between Stage 2 and Stage 3. The transcript is at `bob-sessions/05-confirm-gate/transcript.md`.
6. **Transform catalog.** Bob built the `src/transforms/` package — 6 named, typed, idempotent Transforms across `text/`, `filter/`, and `compose/` subpackages, all auto-registering on import, proving the kernel's Transform primitive is real and testable. The transcript is at `bob-sessions/06-transform-catalog/transcript.md`.
7. **Video vertical sketch.** Bob built `src/videos/` — a second vertical on the same five primitives proving the kernel generalizes beyond research writing: `ShotComposition`, `FrameRenderTransform`, `VisualQualityGate`, and a `render_video()` CLI. The transcript is at `bob-sessions/07-video-vertical/transcript.md`.

The nine sessions demonstrate IBM Bob used for **exploration, implementation, validation, integration, hardening, abstraction, and generalization** — every phase of a real software project. The transcripts are not curated highlights — they are the actual working sessions, captured for the judges.

### Bob sessions index

| Session | Purpose | Folder |
|---|---|---|
| 01 | Codebase exploration (OpenMontage dispatcher audit) | `bob-sessions/01-codebase-exploration/` |
| 02 | Build the creative-reframing agent | `bob-sessions/02-creative-reframing-feature/` |
| 03 | Tests and gate-validation checks | `bob-sessions/03-tests-and-checks/` |
| 04 | Demo entry point + audit recorder | `bob-sessions/04-demo-and-audit/` |
| 05 | Interactive confirm gate | `bob-sessions/05-confirm-gate/` |
| 06 | Transform catalog | `bob-sessions/06-transform-catalog/` |
| 07 | Video vertical sketch | `bob-sessions/07-video-vertical/` |
| 08 | Code review + phase 2 backend | `bob-sessions/08-code-review/` |
| 09 | Deployment readiness (Phase 1 + view polish) | `bob-sessions/09-deployment-readiness/` |

See `bob-sessions/_index.md` for a compact index. Every Bob session in this repo opens with a short header describing the goal, the prompt, and the outcome. The Bob-issued code is committed alongside the human-issued context.

## Quick start

**One-liner** — install dependencies and verify everything works:

```bash
git clone https://github.com/kartikeyapophali/open-production.git && cd open-production && python -m pip install -e . && python -m pytest tests/ -q
```

Then start the browser demo (no API key required):

```bash
python src/public_demo/server.py
# Open http://127.0.0.1:8000/?view=guided   ← Guided Production Flow
# Open http://127.0.0.1:8000/?view=console  ← Agent Console
```

The browser demo runs end-to-end without any API keys. The Guided Flow creates a production and writes a dual-artifact audit trail (`production.json` + `audit.jsonl`). The Agent Console reads the same production and auto-refreshes every 5 seconds.

For a worked-example audit trail, see `output/public-demo/` (written by each demo run). For a full walkthrough, see `docs/how-to-launch-and-test.md`.

## Concurrency limits

The demo server and `ProductionService` are designed for **single-user, single-process** demos. The following guarantees and limits apply:

- **Within one Python process**, `ProductionService.save()` and `load()` are serialized by a per-instance `threading.RLock`. Double-clicks on **Finalize**, two React tabs sharing the same `ProductionService`, and Python threads calling `save()` concurrently from the same process will all serialize cleanly. For load-modify-save transactions, wrap the sequence in `with svc.transaction():` so the lock is held across the whole check-then-act operation. See `tests/test_concurrent_save.py` for the proof (8 threads, 25 saves each, no lost updates, no `PermissionError`).
- **Across Python processes**, the story is different. Two separate `python src/public_demo/server.py` instances writing to the same `output/productions/` directory will race on atomic `os.replace` and on Windows can raise `[WinError 5] Access is denied`. The `_safe_replace()` helper retries transient failures, but for a real deployment you need cross-process locking (e.g. `msvcrt.locking` on Windows, `fcntl.flock` on POSIX) or a single-writer pattern (e.g. a queue worker).
- **The HTTP server** is `ThreadingHTTPServer` so multiple browser tabs within one process get correct per-instance locking. For real production traffic, run behind a WSGI/ASGI server (gunicorn / uvicorn) with multiple workers and front it with a reverse proxy that adds auth and rate limiting.
- **No authentication, no rate limiting.** The server accepts any request from any origin (`*`). Do not expose `localhost:8000` to the public internet without a reverse proxy that adds auth and rate limiting.

## Demo video

A 3-minute walkthrough will be linked at submission time.

The video follows the shot list in `docs/demo/demo-story.md`. It shows: intent declaration, creative reframing, multi-agent research, evidence gate firing, contradiction resolution, publication gate, and the audit trail in `audit_trail.jsonl`. The shot list is mapped to all five judging criteria.

A judge's one-pager is at `docs/judge-pack/quick-brief.md`.

## Team and submission

| | |
|---|---|
| **Team** | Kartikey (engineering) · Boris (architecture & design) |
| **Track** | IBM AI Builders Challenge — July 2026: Reimagine Creative Industries with AI |
| **GitHub** | [github.com/kartikeyapophali/open-production](https://github.com/kartikeyapophali/open-production) |
| **Demo video** | To be linked at submission time (see `docs/demo/demo-story.md` for the shot list) |
| **Platform page** | [aibuilderschallenge-bobhub.bemyapp.com](https://aibuilderschallenge-bobhub.bemyapp.com/#/projects) — linked at submission time |
| **SkillsBuild cert** | `bob-sessions/certificates/skillsbuild-cert.pdf` |
| **License** | MIT |

## Project page

The submission page on the IBM AI Builders Challenge platform will be linked at submission time.

## What's next

The kernel is the foundation. The first vertical we're shipping is research writing. The next verticals are video and code — both fall out of the same primitives. The roadmap is in `docs/architecture/architecture.md`.

## License

MIT — open source, build on it.

## Acknowledgments

Built with IBM Bob as the primary development tool. Architecture influences include OpenMontage (calesthio), K8s reconciliation loops, and Git's content-addressed store. Author: Kartikey. Architecture & design: Boris.
