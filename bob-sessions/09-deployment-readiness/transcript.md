# Bob Session 09 — Deployment Readiness

**Date:** 2026-07-28  
**Goal:** Move the Open Production MVP from "72% MVP" to a judge-runnable, deployable submission. Scope = Phase 1 critical blockers + view polish for Guided Flow and Agent Console only.  
**Outcome:** All Phase 1 tasks completed. Both MVP views polished. Test suite grew from 164 → **166 passing, 0 failures**. All submission-critical documentation updated.

---

## Context

The architecture audit (`docs/plans/architecture-audit-2026-07-27.html`) was conducted against the live repo before this session. Key findings:

- **72% MVP completion**, 132 tests at audit time.
- **4 "spec-only" agents** (VoiceDirector, SoundDesigner, MusicComposer, Colorist) — all now implemented before this session started (164 tests already passing).
- **bob-sessions/ directory** exists with 9 sessions — critical blocker from audit already resolved.
- **architecture.md** still described the old PDT research-writing pipeline as the primary system.
- **submission-checklist.md** had stale `make demo` / `51/51` / `Makefile` references.
- **README** Quick start section still referenced `make test`, `make demo`, `scripts/run_demo.py`.
- **Agent Console** was a flat event stream; spec required per-actor proposal panels.
- **Guided Flow** did not surface the `production_id` after finalize.

The user chose **Path C** from the audit spec: Phase 1 critical blockers + view polish only.

---

## P1.1 — Conftest temp path

**Status:** Already resolved before session start. `tests/conftest.py` routes pytest temp to `Path(tempfile.gettempdir()) / "pytest-open-production"` with a `pytest_configure` hook. `python -m pytest tests/ -q` runs clean without any `--basetemp` flag.

**Verification:**
```
python -m pytest tests/ -q --tb=line
# 164 passed (before this session's additions)
```

---

## P1.2 — Deserialization data loss

**Status:** Already resolved before session start. `src/service/production_service.py` correctly reconstructs all nested objects on `load()`:

- `_dict_to_char()`: rebuilds `Character.visual_anchors` from `d.get("visual_anchors", [])` via `Reference(**r)`.
- `_dict_to_env()`: rebuilds `Environment.visual_anchors` identically.
- `_dict_to_brand()`: rebuilds `BrandKit.logos` from `d.get("logos", [])`.
- `_dict_to_shot()`: rebuilds `Shot.characters` as `CharacterReference(...)` and `Shot.version_history` via `_dict_to_generation()`.

No data loss on save/load round-trips. Confirmed by existing `test_production_service.py` suite (all green).

---

## P1.3 — Rewrite architecture.md

**File:** `docs/architecture/architecture.md`

**What changed:**

1. **Mermaid diagram replaced.** Old diagram depicted the PDT research-writing 5-stage pipeline (PubMed/OpenAlex research agents, claim extractors, output PDF). New diagram shows the production-crew model: `Intent → Reframing (3 angles) → Production Crew (13 agents) → Fail-Closed Gates (4) → Dual-Artifact Output → Browser Views`.

2. **Agent scope table updated.** Removed `🗺 Roadmap` status from VoiceDirectorAgent, SoundDesignerAgent, MusicComposerAgent, ColoristAgent. All four are now marked `✅ Implemented` with their correct `WRITABLE_FIELDS`.

3. **Test count updated.** `164 tests passing, 0 failures, 0 errors (python -m pytest tests/ -q)`.

**Verification:** File parses as valid Markdown. Every code-path citation is a real file in `src/`.

---

## P1.4 — Update submission-checklist.md

**File:** `docs/submission-checklist.md`

**What changed:**

- Gate 3: `132 passed` → `164+ passed`. Added session 04, 08, 09 transcript entries. Updated architecture.md note to "reflects current implementation (all 13 agents, current Mermaid diagram)". Updated test count gate to `≥164 tests`.
- Gate 4: Replaced `make demo` with `python src/public_demo/server.py` + browser URL. Replaced "output PDF" with "production_id displayed → Agent Console link visible". Removed `Makefile` reference.
- Gate 6: Replaced `make install && make test && make demo` with `python -m pip install -e . && python -m pytest tests/ -q && python src/public_demo/server.py`.

---

## P1.5 — Update README quick-start

**File:** `README.md`

**What changed:**

1. **Tagline updated**: "long-form content — research" → "long-form video production — 13 specialist agents, fail-closed gates, and an audit-traceable production pipeline."
2. **Solution section**: Replaced 5-stage research-writing list with 5-stage production-crew list (intent, creative reframing, shot design, storyboarding + review, publish with evidence).
3. **Quick start**: Replaced `make test` / `make demo` / `make web-demo` / `scripts/run_demo.py` with `python -m pytest tests/ -q` and `python src/public_demo/server.py`.
4. **Bob sessions count**: "seven" → "nine".
5. **Bob sessions table**: Added rows for sessions 08 and 09.
6. **Demo video placeholder**: "link to be added at submission" → "will be linked at submission time."

---

## VP.1 — Guided Flow: surface production_id after finalize

**File:** `src/public_demo/server.py` (INDEX_HTML constant)

**What changed:**

Added `.prod-id-panel` CSS class (teal-tinted panel, hidden by default) and two new DOM elements to the Result section:
- `<div id="prod-id-panel" class="prod-id-panel hidden">` — contains the production_id label and a console link.
- `<code id="prod-id-display">` — displays the production_id string.
- `<a id="prod-console-link" class="console-link">` — navigates to `/?view=console&production_id=<id>`.

In the `renderRun(result)` JavaScript function, after rendering the audit log, added logic to:
1. Check `result.production_id` (already returned by `build_demo_report()` in `src/demo_flow.py`).
2. If present: set `pidDisplay.textContent`, set `consoleLink.href`, remove `.hidden` from the panel.
3. If absent: add `.hidden`.

`build_demo_report()` already returned `production_id` in its response dict — no server-side change needed.

**Verification (new test):**
```python
# tests/test_view_switching.py
def test_guided_flow_surfaces_production_id_in_html():
    html = render_index_html(view="guided")
    assert "prod-id-panel" in html
    assert "prod-console-link" in html
    assert "prod-id-display" in html
```

---

## VP.2 — Agent Console: per-actor filter panel

**File:** `src/public_demo/server.py` (CONSOLE_HTML constant)

**What changed:**

1. **CSS additions**: `.console-layout` (2-column grid), `.actor-rail` (left pane), `.actor-btn` (clickable actor filter buttons), `.actor-badge` (event count), `.event-item.hidden` (filter hide).

2. **HTML restructure**: Replaced the single `.panel` div with a `.console-layout` wrapper (carries `data-test-actor-panel="true"` for test hooks) containing:
   - `<aside class="actor-rail">` with an "All" button (`id="actor-all"`) and an `id="actor-buttons"` container for dynamically populated per-actor buttons.
   - The original `.panel` event list on the right.

3. **JavaScript additions**:
   - `_selectedActor` state variable.
   - `applyActorFilter(actor)` — toggles `.active` on rail buttons, adds/removes `.hidden` on list items by `data-actor` attribute.
   - `updateActorRail(entries)` — counts events per actor, creates/updates actor buttons dynamically.
   - `fetchLog()` updated to: call `updateActorRail(entries)`, stamp each `<li>` with `data-actor=<actor>`, apply `.hidden` class for filtered actors.

The filter is pure client-side — no new API endpoints.

**Verification (new test):**
```python
# tests/test_view_switching.py
def test_agent_console_has_per_actor_panel():
    html = render_index_html(view="console")
    assert "data-test-actor-panel" in html
    assert "actor-all" in html
    assert "actor-buttons" in html
```

---

## P1.6 — bob-sessions/ verification

**Status:** Confirmed. All 9 session directories present:

```
bob-sessions/
  01-codebase-exploration/     transcript.md  spec.md
  02-creative-reframing-feature/ transcript.md spec.md
  03-tests-and-checks/         transcript.md  spec.md  check-log.md
  04-demo-and-audit/           transcript.md  spec.md
  05-confirm-gate/             transcript.md  spec.md
  06-transform-catalog/        transcript.md  spec.md
  07-video-vertical/           transcript.md  spec.md
  08-code-review/              transcript.md  spec.md
  08-self-review/              transcript.md
  09-deployment-readiness/     spec.md  transcript.md (this file)
  _index.md
```

IBM Challenge requires ≥7 sessions. We have 9 distinct sessions committed.

---

## Final test run

```
python -m pytest tests/ -q
................................................................................................ [43%]
................................................................................................ [86%]
......................                                                                           [100%]
166 passed in 2.19s
```

**166 passed, 0 failures, 0 errors.** Up from 164 before this session (2 new view-switching tests added).

---

## Files modified in this session

| File | Change |
|---|---|
| `src/public_demo/server.py` | VP.1: prod-id panel + console link in Guided Flow; VP.2: per-actor filter rail in Agent Console |
| `docs/architecture/architecture.md` | P1.3: new Mermaid diagram (production-crew model), agent table updated (all 13 implemented) |
| `docs/submission-checklist.md` | P1.4: test count, Gate 3 sessions, Gate 4 commands, Gate 6 commands |
| `README.md` | P1.5: tagline, solution list, quick-start commands, sessions count and table, demo video |
| `tests/test_view_switching.py` | 2 new tests: `test_guided_flow_surfaces_production_id_in_html`, `test_agent_console_has_per_actor_panel` |
| `bob-sessions/09-deployment-readiness/transcript.md` | This file |
| `bob-sessions/_index.md` | Added session 09 entry |
