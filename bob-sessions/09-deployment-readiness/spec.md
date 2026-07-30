# Bob Session 09 — Deployment Readiness (Path C: Phase 1 + view polish)

**Date:** 2026-07-28
**Author:** Boris (delegated by Kartikey)
**Goal:** Move the Open Production MVP from "62% overall / 72% MVP" to a judge-runnable, deployable submission. Scope = **Phase 1 (critical blockers) + view polish for Guided Flow and Agent Console only**. Out of scope: Director's Canvas, Timeline Editor, Node Graph (Phase 4 / roadmap).

**Outcome target:** 105/105 tests passing clean, every artifact cited in `docs/submission-checklist.md` exists, both MVP views load at `/?view=guided` and `/?view=console` and demonstrate the production-crew model to a judge in under 90 seconds.

---

## Context

The architecture audit (`docs/architecture-audit-report.html`) was conducted against the live repo on 2026-07-28. Findings:

- **62% overall, 72% MVP completion.**
- **105 tests passing** when run with `pytest --basetemp=C:\Temp\pytest-openprod` (verified by Boris). Without that flag, 14 tests fail with `PermissionError` on `.tmp/pytest/pytest-of-karti` — a Windows sandboxing artifact, not a code bug.
- **6 of 12 agents live** in `src/agents/` (CreativeReframing, ConfirmGate, ShotDesigner, CharacterDirector, StoryboardArtist, Reviewer, Editor). The other 6 (EnvironmentArtist, VoiceDirector, SoundDesigner, MusicComposer, Colorist, Publisher) are spec-only.
- **Both MVP UI views are live** at `/?view=guided` (HTML in `src/public_demo/server.py:INDEX_HTML`) and `/?view=console` (HTML in `src/public_demo/server.py:CONSOLE_HTML`) but have gaps vs the spec (see View Polish below).
- **`bob-sessions/`** has 9 directories on disk (01–08 + 08-self-review), satisfying the IBM Challenge ≥7-session rubric.
- **`docs/architecture/architecture.md`** still describes the old PDT research-writing pipeline as the primary shipped system. Judges will read it and be confused. Must be rewritten.

The user (Kartikey) has chosen **Path C** from the audit: Phase 1 critical blockers + view polish only. Everything else (Phase 2 hardening, Phase 3 medium-priority items, Phase 4 roadmap views) is deferred to post-submission.

---

## Phase 1 — Critical blockers (fix in order, verify after each)

### P1.1 — Make the clean test run the default

**Why:** The current `conftest.py` points `TMPDIR` at `.tmp/pytest/`, which collides with the Windows sandbox lock on the same path. 14 tests error out. Audit's recommended fix: route pytest's temp machinery to `C:\Temp\pytest-openprod` so a fresh `pytest` works without flags.

**File:** `D:\IBM Project\Open_Production\conftest.py`

**Required change:** Update `pytest_configure()` to:

1. Use `Path(os.environ.get("PYTEST_BASETEMP") or r"C:\Temp\pytest-openprod")` as the temp root instead of `.tmp/pytest`.
2. Create the directory with `parents=True, exist_ok=True`.
3. Set `TMPDIR`, `TEMP`, `TMP` env vars and `tempfile.tempdir` exactly as today, but pointing at the new root.
4. Fall back to `.tmp/pytest` if `C:\Temp\pytest-openprod` cannot be created (so CI on Linux/Mac still works).

**Verification (must pass before moving on):**
```
cd "D:\IBM Project\Open_Production"
python -m pytest tests/ -q --tb=line
```
Expected: `105 passed`, **no errors**, no `PermissionError`.

### P1.2 — Fix deserialization data loss in `production_service.py`

**Why:** Three fields are silently dropped on every load/save cycle:
- `_dict_to_char` — `visual_anchors=[]` (line where it says `# simplify: anchors restored lazily`)
- `_dict_to_env` — `visual_anchors=[]` (same comment)
- `_dict_to_shot` — `characters=[]`, `version_history=[]` (lines that hardcode empty)
- `_dict_to_brand` — `logos=[]` (line that hardcodes empty)

This silently breaks ConsistencyContract checking after a round-trip and silently drops shot-level character references and generation history.

**File:** `D:\IBM Project\Open_Production\src\service\production_service.py`

**Required change:** Each of the four `_dict_to_*` functions should:

1. Pull the stored list from the dict (e.g., `d.get("visual_anchors", [])`).
2. Reconstruct the typed entity via the existing helpers — e.g., `_ref_to_dict` for refs is the serializer, so deserializing refs needs a small helper or inline reconstruction.

Add a tiny helper `_dict_to_ref(d)` that returns a `Reference(**d)` if all required keys present, else `None`. Use it to rebuild:
- `Character.visual_anchors` from `d.get("visual_anchors", [])` filtered to non-None
- `Environment.visual_anchors` from the same source
- `BrandKit.logos` from `d.get("logos", [])` filtered to non-None
- `Shot.characters` from `d.get("characters", [])` reconstructed via `_dict_to_char_ref` (new tiny helper that returns `CharacterReference(**d)`)
- `Shot.version_history` from `d.get("version_history", [])` reconstructed via `_dict_to_generation` (new tiny helper that returns `GenerationResult(**d)` if non-None else `None`)

Use the field types already defined in `src/schema/production_document.py` — read the file first to confirm field names; do not invent new fields.

**Verification (must pass before moving on):**
```
cd "D:\IBM Project\Open_Production"
python -m pytest tests/test_production_service.py tests/test_view_switching.py tests/test_demo_flow.py tests/test_review.py tests/test_character_director.py tests/test_consistency_violation_fixture.py -q --tb=line
```
Expected: all green. Then run the full suite to confirm no regressions:
```
python -m pytest tests/ -q --tb=line
```
Expected: `105 passed`.

Also add one **new** test in `tests/test_production_service.py` named `test_round_trip_preserves_visual_anchors_and_shot_characters` that:

1. Creates a Production with one Character that has 2 `visual_anchors`, one Environment with 1 `visual_anchor`, one Scene with one Shot that has 1 character reference and 1 entry in `version_history`, and one BrandKit with 1 logo.
2. Calls `service.save(prod)`, then `prod2 = service.load(prod.id)`.
3. Asserts `prod2.characters[0].visual_anchors` has length 2, `prod2.environments[0].visual_anchors` has length 1, `prod2.scenes[0].shots[0].characters` has length 1, `prod2.scenes[0].shots[0].version_history` has length 1, `prod2.brand_kit.logos` has length 1.

This locks the regression.

### P1.3 — Rewrite `docs/architecture/architecture.md`

**Why:** This is the document judges read first for "Technical Execution." Currently it describes the PDT research-writing pipeline as the primary shipped system and does not mention ProductionService, the 6 agents, the browser demo, or `src/public_demo/server.py`. Judges will get the wrong mental model and the architecture credit will be lost.

**File:** `D:\IBM Project\Open_Production\docs\architecture\architecture.md`

**Required change:** Rewrite to reflect the **current shipped state** as of 2026-07-28. Must include:

1. **One-paragraph summary** stating that Open Production is a creative partner for long-form video production (not research writing). Name the two MVP views: Guided Production Flow and Agent Console.
2. **System diagram** — keep the Mermaid diagram in `docs/architecture/architecture-diagram.mmd` if it still parses; if it depicts the old PDT pipeline, replace it with a new one showing: Production Document → ProductionService → 6 agents → 4 gates → Audit Trail → 2 views.
3. **Layered architecture table** with these rows, each pointing to live file paths:
   - Schemas: `src/schema/production_document.py`, `docs/schema/production-document.schema.json`
   - Persistence: `src/service/production_service.py`
   - Audit: `src/audit/recorder.py`
   - Agents (6 live): CreativeReframing, ConfirmGate, ShotDesigner, CharacterDirector, StoryboardArtist, Reviewer, Editor — list each with its `src/agents/<name>.py` path and a one-line role description
   - Gates (4 live): EvidenceGate, ConsistencyGate, ConsistencyContractGate, PublicationGate — `src/validation/gates.py`
   - Browser demo: `src/public_demo/server.py` serving `/?view=guided` and `/?view=console`
4. **Five-primitive model** — keep this section as it documents the kernel philosophy. One sentence each on Source / Transform / Composition / Evaluation / Intent, with concrete code paths.
5. **State machine section** showing the 6 states (DRAFT → BRIEFED → IN_PRODUCTION → IN_REVIEW → APPROVED → PUBLISHED) and that `ProductionService.apply_event` enforces them.
6. **Honest gaps section** listing the 6 unimplemented agents (EnvironmentArtist, VoiceDirector, SoundDesigner, MusicComposer, Colorist, Publisher) as designed but not shipped, with a one-line note each explaining the dataclasses that already exist and the missing agent class.

**Verification:**
- The new file parses as valid Markdown.
- Every code-path citation is real (`Test-Path` each one before committing).
- `docs/architecture/architecture-diagram.mmd` either still parses or is replaced with a new Mermaid diagram under the same filename.

### P1.4 — Update `docs/submission-checklist.md`

**Why:** The checklist still says "51/51 tests" and references PDT paths and a `Makefile` that no longer exists. Judges will fail Gate 3 on the test count alone.

**File:** `D:\IBM Project\Open_Production\docs\submission-checklist.md`

**Required change:**

1. **Test count line:** replace every "51/51" with "105/105".
2. **Gate 3 checklist** — replace the PDT-path bullets with these exact bullets (and only these):
   - `bob-sessions/01-codebase-exploration/transcript.md` exists
   - `bob-sessions/02-creative-reframing-feature/transcript.md` exists with `src/agents/creative_reframing.py`
   - `bob-sessions/03-tests-and-checks/transcript.md` exists with `tests/test_gates.py`
   - `bob-sessions/04-demo-and-audit/transcript.md` exists
   - `bob-sessions/05-confirm-gate/transcript.md` exists
   - `bob-sessions/06-transform-catalog/transcript.md` exists
   - `bob-sessions/07-video-vertical/transcript.md` exists
   - `bob-sessions/08-code-review/transcript.md` exists
   - `bob-sessions/09-deployment-readiness/transcript.md` exists (this session)
   - `docs/architecture/architecture.md` exists and reflects current implementation
   - `docs/architecture/architecture-diagram.mmd` parses
   - `docs/demo/demo-story.md` exists
   - `make test` runs and passes (105/105). If a Makefile does not exist, document the equivalent: `python -m pytest tests/ -q`.
3. **Gate 4** — replace the demo path. The current path references `scripts/run_demo.py` (PDT research writing). Replace with the browser demo: `python src/public_demo/server.py` then open `http://127.0.0.1:8000/?view=guided`.
4. **Remove or update any reference to `Makefile`** that no longer exists; replace with explicit `python -m pytest tests/ -q` and `python src/public_demo/server.py` commands.

**Verification:** Re-read the file top-to-bottom. No reference to "PDT" or "research writing" or "51/51" should remain. The two MVP views are named correctly.

### P1.5 — Verify README quick-start

**Why:** The current README describes the PDT research-writing system. Judges cloning the repo will follow the quick-start and find that `make demo` does not run the browser demo, and the README's claims about agents do not match the codebase.

**File:** `D:\IBM Project\Open_Production\README.md`

**Required change:** Update the following sections **in place** without rewriting the whole file (the file structure is good):

1. **Problem statement** (top): one sentence acknowledging the system serves video production as the primary vertical, with research writing as an earlier experimental vertical. Three sentences max.
2. **Solution** section: replace the five-stage research-writing list with a five-stage **production** list:
   1. Intent declaration (topic, audience, tone, duration)
   2. Creative reframing — three angles (skeptic / advocate / contrarian); user picks
   3. Shot design — three camera+lighting proposals per shot
   4. Storyboarding — ASCII blocking diagrams per shot
   5. Review — ReviewerAgent runs all 5 checks from Appendix J; verdict gates delivery
3. **Quick start** code block: replace the `make demo` / `make web-demo` / `scripts/run_demo.py` lines with the actual commands:
   - `python -m pip install -e .` (install)
   - `python -m pytest tests/ -q` (run tests — expect 105/105)
   - `python src/public_demo/server.py` (start browser demo on `http://127.0.0.1:8000`)
   - Then open `http://127.0.0.1:8000/?view=guided` for Guided Production Flow and `http://127.0.0.1:8000/?view=console` for Agent Console
4. **How IBM Bob was used** section: add a row 8 entry to the bob-sessions index table referencing `bob-sessions/08-code-review/transcript.md` (it exists, was omitted from the table).

**Verification:** Re-read the README. No reference to `scripts/run_demo.py`, `make demo`, `make web-demo`, or "PDT" should remain in the Quick start section.

### P1.6 — Verify `bob-sessions/` is committed

**Why:** Already verified on 2026-07-28 — 9 directories exist. Bob's only job here is to confirm the structure and add `09-deployment-readiness/transcript.md` once P1.1–P1.5 are done. No code change.

---

## View polish — make Guided Flow and Agent Console judge-runnable

### VP.1 — Guided Flow: surface production_id after creation

**Why:** The audit noted "no production_id display in UI after creation." A judge who finalizes a production in Guided Flow currently has no on-screen cue about what production_id to use when opening the Agent Console.

**File:** `D:\IBM Project\Open_Production\src\public_demo\server.py`

**Required change:** In the `INDEX_HTML` constant (Guided Flow HTML), after the existing `/api/finalize` POST handler in JavaScript, when the response includes a `production_id`:

1. Display the production_id in a clearly visible panel (use the existing styling tokens — find what the file already uses for `.result`, `.audit-trail`, or similar blocks and follow that pattern).
2. Provide a clickable link that navigates to `/?view=console&production_id=<id>` so the judge can jump straight to the Agent Console.
3. Preserve the existing download-audit-trail button behavior.

**Verification:** Add a new test in `tests/test_view_switching.py` named `test_guided_flow_surfaces_production_id_in_response_and_link` that:
1. POSTs to `/api/finalize` with a valid topic payload.
2. Asserts the response contains `production_id` (already true — locked).
3. Fetches the Guided Flow HTML (`/?view=guided`) and asserts it contains the substring `"production_id"` or `"productionId"` referenced in the new panel.
4. Fetches the Agent Console for the new production_id and asserts it returns 200 with non-empty body.

### VP.2 — Agent Console: per-agent proposal panels

**Why:** The audit noted the Agent Console is currently a flat audit-event log stream. The wireframe (`docs/wireframes/04-agent-console.svg`) calls for per-agent panels showing proposals with approve/adjust controls. Wireframe-readiness needs at minimum a section that breaks the audit log into per-actor panels.

**File:** `D:\IBM Project\Open_Production\src\public_demo\server.py`

**Required change:** In the `CONSOLE_HTML` constant (Agent Console HTML), replace the flat event list rendering with a **two-pane layout**:

- **Left rail (220 px):** a list of actor names that have appeared in the audit log, each with a count badge. Click an actor to filter the right pane.
- **Right pane:** the existing audit-event list, but filtered to the selected actor when one is selected.

This is a client-side filter, not a new API. Use vanilla JavaScript — no new dependencies. Style with the existing design tokens in the file.

**Verification:** Add a new test in `tests/test_view_switching.py` named `test_agent_console_supports_per_actor_filter` that:
1. Creates a production, runs the demo flow (or directly writes 3+ audit entries with different actors via `ProductionService.apply_event`).
2. Fetches the Console HTML and asserts the new left-rail structure is present (search for an element with a `data-test-actor-panel` attribute or similar marker you add).
3. Asserts that the audit log endpoint returns ≥3 entries (the data source for the filter still works).

### VP.3 — README "Demo video" link

**Why:** README has `[link to be added at submission]` placeholder. If the demo video URL is known, fill it in; if not, change the line to "Demo video will be linked at submission time." Either is fine.

**File:** `D:\IBM Project\Open_Production\README.md`

**Required change:** One line edit in the "Demo video" section.

---

## Out of scope (do not touch)

- Director's Canvas view (`/?view=canvas` stub in `server.py`)
- Timeline Editor
- Node Graph
- The 6 missing agents (EnvironmentArtist, VoiceDirector, SoundDesigner, MusicComposer, Colorist, Publisher)
- `ProductionService.snapshot()` and `merge()` methods
- WRITABLE_FIELDS runtime enforcement in BaseAgent
- State-transition direction enforcement in `apply_event`
- Stale build plan markers in `docs/plans/2026-07-27-build-implementation-plan.md`
- Real LLM client (only `MockLLMClient` exists today)
- Any change to `workspace.py` / `workspace.html` (orphaned — leave alone)

---

## Required artifacts at end of session

When P1.1–P1.5 and VP.1–VP.3 are complete, write `bob-sessions/09-deployment-readiness/transcript.md` containing:

1. **Header** (matching the format of session 08) — date, goal, outcome summary.
2. **Section per task** — what file changed, what the diff is (file paths + line ranges), what the verification command returned.
3. **Final test run output** at the end — full `pytest tests/ -q` output, expected `105 passed` (with the new round-trip test making it 106 passed or more).
4. **Final file inventory** — `git status` (if a git repo is initialized) or `Get-ChildItem -Recurse | Measure-Object` summary noting new/modified files.

Append a row to `bob-sessions/_index.md` for session 09 with a one-paragraph outcome summary.

---

## Verification commands Bob must run before declaring success

```
cd "D:\IBM Project\Open_Production"

# 1. Conftest change works without flags
python -m pytest tests/ -q --tb=line

# 2. Deserialization round-trip works
python -m pytest tests/test_production_service.py -q --tb=line

# 3. View tests pass
python -m pytest tests/test_view_switching.py tests/test_demo_flow.py -q --tb=line

# 4. The browser server starts cleanly
python src/public_demo/server.py &
sleep 2
curl -s http://127.0.0.1:8000/healthz
curl -s "http://127.0.0.1:8000/?view=guided" | head -50
curl -s "http://127.0.0.1:8000/?view=console" | head -50

# 5. README and submission checklist still read sensibly
Get-Content README.md | Select-String -Pattern "PDT|make demo|51/51"
# (should return no matches)
```

All five must pass before writing the transcript.

---

*Spec author: Boris (delegated by Kartikey) — 2026-07-28 15:56 IST — Path C from `docs/architecture-audit-report.html`.*