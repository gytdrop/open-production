# Guided Flow + Agent Console Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Two front-end pages — Guided Flow and Agent Console — that read/write a shared `Production` state via `ProductionService`, with a view-switcher that preserves state on toggle.

**Architecture:** Same backend, two HTML pages. `ProductionService` (Python) holds `production.json` + `audit.jsonl` on disk. Both pages call `/api/production/<id>/...` endpoints that the existing `src/public_demo/server.py` HTTP server already serves. View-switching is a `<a href="?view=…">` link on both pages; the server reads `?view=` and renders the right HTML, preserving `production_id` across the link.

**Tech Stack:** Python 3.11 stdlib (http.server, json) for the backend. No new dependencies. Plain HTML + a tiny inline `<script>` for the views; no JS framework. Existing 51 tests + ~8 new ones for the service + 3 for view-switching.

---

## Global rules (apply to every task)

- **51/51 test floor.** Never go below. Every change ships with a green test run.
- **No new dependencies.** Stdlib only for Python. Vanilla HTML/CSS/JS for the front-end.
- **Backward compatible:** `build_demo_report()`'s public API stays unchanged. Only internals learn about `Production`.
- **One phase at a time.** Don't start Phase 2 until Phase 1 tests are green.
- **Heartbeat.** At every phase boundary + every ~30 min, print `[HEARTBEAT hh:mm] phase=X/Y | tests=… | DONE=… | PENDING=… | BLOCKER=… | next=…` in chat.

---

## Phase 1 — ProductionService implementation

### Task 1.1: `src/service/__init__.py`

**Files:**
- Create: `src/service/__init__.py`

**Step 1:** Verify file does not already exist.

```bash
test ! -f 'D:/IBM Project/Open_Production/src/service/__init__.py'
echo $?   # expect 0
```

**Step 2:** Write the package init. Re-exports `ProductionService`, `ProductionNotFound`, `StorageError`, `append_audit_entry`.

**Step 3:** Verify Python imports cleanly.

```bash
cd 'D:/IBM Project/Open_Production'
python -c "from src.service import ProductionService, ProductionNotFound"
```

Expected: no output, exit 0.

### Task 1.2: `src/service/production_service.py`

**Files:**
- Create: `src/service/production_service.py`

**Step 1: Write the failing test** — `tests/test_production_service.py` covering:
- `init(name)` creates a directory + production.json + empty audit.jsonl
- `load(id)` round-trips what `save()` wrote
- `apply_event()` never mutates input
- `log(id)` returns entries filtered by action_type
- `status(id)` returns the full Production JSON

**Step 2: Run test to verify it fails** — `pytest tests/test_production_service.py -v`. Expected: ImportError.

**Step 3: Write minimal implementation.**

```python
class ProductionNotFound(LookupError): ...
class StorageError(RuntimeError): ...

@dataclass(frozen=True)
class ProductionService:
    storage_dir: Path
    def init(self, name, studio_id=None) -> Production:
        pid = "prod_" + uuid.uuid4().hex[:12]
        prod = Production(id=pid, state="DRAFT", ...)
        (self.storage_dir / pid).mkdir(...)
        self.save(prod)
        return prod
    def save(self, prod) -> Production:
        # atomic write temp + rename; append to journal
        ...
    def load(self, production_id) -> Production:
        ...
    def apply_event(self, prod, entry) -> Production:
        # pure: returns new Production
        ...
    def status(self, production_id) -> dict:
        prod = self.load(production_id)
        return prod_to_dict(prod)
    def log(self, production_id, since=None, action_type=None) -> list[dict]:
        ...
```

**Step 4: Run tests** — `pytest tests/test_production_service.py -v`. Expected: green.

**Step 5: Run full suite** — `pytest tests/ -q`. Expected: 51 + new passed.

### Task 1.3: Wire `src/demo_flow.py` to use the service

**Files:**
- Modify: `src/demo_flow.py`
- Test: `tests/test_demo_flow.py` (existing — must still pass)

**Step 1:** In `build_demo_report()`, instantiate `ProductionService(storage_dir=...)` once.
**Step 2:** Replace the bare `AuditRecorder(...)` with `service.apply_event(...)` + `service.save(...)` calls.
**Step 3:** Public return shape stays the same (`{...}"audit_path": ..., "audit_entries": ...}`).
**Step 4:** Run `pytest tests/ -q`. Expected: all green, including `test_demo_flow.py`.

### Task 1.4: Phase 1 exit gate

**Tests:** `pytest tests/ -q` last line = `59 passed` (51 original + 8 new) or higher. Zero regressions.
**Files on disk:** `src/service/__init__.py`, `src/service/production_service.py`, `tests/test_production_service.py`.
**Heartbeat:** "Phase 1 done. 59 passed. Moving to Phase 2."

---

## Phase 2 — Guided Flow + Agent Console front-ends

### Task 2.1: Read current `src/public_demo/server.py`

Find the existing HTML template + route layout. Do NOT rewrite from scratch — refactor.

### Task 2.2: Add `?view=` route handling

**Files:**
- Modify: `src/public_demo/server.py`

When the request path is `/`, read `?view=`:
- `view=guided` (default) → render Guided Flow page
- `view=console` → render Agent Console page

Both pages receive `production_id` from the URL, render a status bar pulling from `/api/production/<id>/status`, and link to the other view.

### Task 2.3: Guided Flow page (`?view=guided`)

Features on the page:
- Title input (becomes `prod.title`)
- Topic textarea (becomes `prod.intent.topic`)
- "Generate 3 angles" button → POST `/api/production/<id>/brief`
- Show 3 angle cards once they're in
- "Pick angle 1/2/3" buttons → POST `/api/production/<id>/decide`
- Link at the top: "Switch to Agent Console →" → `?view=console`

No animations, no client-side framework, no CSS framework. Plain HTML.

### Task 2.4: Agent Console page (`?view=console`)

Features on the page:
- Top: "current production" header
- Audit-event log (last 20 entries) loaded from `/api/production/<id>/log`
- Sections: recent events, branches, locked decisions
- Footer: view-switcher link to Guided Flow

### Task 2.5: View-switching test

**Files:**
- Create: `tests/test_view_switching.py`

Covers:
- Open `/?view=guided&production_id=…` → returns 200, contains "Guided Flow"
- Open `/?view=console&production_id=…` → returns 200, contains "Agent Console"
- Same `production_id` carries across the link in both directions
- After a `decide` event on Guided Flow, the Agent Console `/status` reflects the new state

### Task 2.6: Phase 2 exit gate

**Tests:** `pytest tests/ -q` last line = `62 passed` (or higher). Zero regressions.
**Files on disk:** `src/public_demo/server.py` modified, both view pages reachable, view-switcher works in browser.

---

## Phase 3 — ConsistencyContract enforcement

### Task 3.1: Add `consistency_contract_check()` to `src/validation/gates.py`

**Files:**
- Modify: `src/validation/gates.py`
- Create: `tests/test_consistency_contract.py`

Wire the new check into the demo's review pipeline. Demonstrate a fixture that fails the check (missing `required_attribute`).

### Task 3.2: Generate a fixture the user can run

`examples/generate_consistency_violation_fixture.py` — produces a sample production.json + audit.jsonl pair demonstrating failure.

### Task 3.3: Phase 3 exit gate

**Tests:** `pytest tests/ -q` last line = `65 passed` (or higher). ConsistencyContract enforcement real.

---

## Phase 4 — Differentiation copy + Bob transcript + finalize

### Task 4.1: 5-paragraph differentiators doc

`docs/judge-pack/differentiators.md` — pairs each differentiator with file:line.

### Task 4.2: Bob session 8 (code-review transcript)

Hand the Bob Prompt A from #1898 to Bob. Print the resulting transcript under `bob-sessions/08-code-review/`.

### Task 4.3: Wireframes → PNG renders

Use the browser tool to take a screenshot of each wireframe SVG.

### Task 4.4: Final `pytest tests/ -q` and submit

---

## Risks & mitigations

- **ProductionService write patterns diverge from existing `AuditRecorder`.** Both write JSONL. New service writes both `production.json` AND `audit.jsonl`. Existing `record_gate_decision()` should be re-routed through the service. Compatibility helper: `audit_entry_from_gate_decision()` in `docs/schema/production_document.py` is already imported-ready.
- **HTML pages add weight to `src/public_demo/server.py`.** Move them to separate files: `src/public_demo/guided_flow.html` and `src/public_demo/agent_console.html`. Load via `Path(...).read_text()`.
- **Test count creep.** Keep test additions bounded. Phase 1 adds ≤8, Phase 2 adds ≤3, Phase 3 adds ≤3, Phase 4 adds none.

---

## Honest scope cuts

I am **not** building in this window:
- The Node Graph view
- Timeline Editor view
- Director's Canvas view (rendered; the wireframe exists)
- Real ConsistencyContract UI editor
- Branch / merge / snapshot beyond stub
- Multi-user collab
- Touching the video vertical beyond what's already there

Anything not in this plan is for after Friday.

---

*Plan written 2026-07-27 · deadline Fri 2026-07-31 11:59 PM ET*