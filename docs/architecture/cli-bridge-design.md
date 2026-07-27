# ACT-8 · CLI Bridge — Design Doc

> Design the API bridge from the existing CLI backend (`src/demo_flow.py`) to the production state model (`docs/schema/production-document.schema.json`).

**Status:** ACT-8 design draft · 2026-07-27
**Owner:** Engineering
**Inputs:** `src/demo_flow.py`, `src/audit/recorder.py`, `src/public_demo/server.py`, `docs/schema/production-document.schema.json`, `docs/principles.md`

---

## 1 · Why this bridge exists

Today, `src/demo_flow.py:build_demo_report()` runs the full research-vertical flow as a single function. It writes a JSONL audit trail and returns a JSON-serializable dict. There's no persistent production object — each call is one-shot.

That's fine for a demo. It's wrong for a product. The full plan (Section 9 of `open-production-plan.md`) defines a hierarchical Studio → Production → Scene → Shot → Frame state machine. Bridging means:

1. Give the demo a real `Production` object to write into (instead of just JSONL).
2. Expose the production state via a CLI surface.
3. Mirror the same surface over HTTP so the browser demo uses the same backend.

The schema (`docs/schema/production-document.schema.json`) is the canonical wire format. This bridge is the runtime.

---

## 2 · Target architecture (3-tier)

```
┌──────────────────────────────────────────────────────────┐
│  Tier 1 — CLI surface (`bin/op` or `python -m open_production.cli`) │
│  Subcommands: init, brief, decide, gate, status, log,    │
│  export, review, snapshot, branch                         │
└──────────────────────────────────────────────────────────┘
                          │ (JSON over stdin/stdout)
┌──────────────────────────────────────────────────────────┐
│  Tier 2 — ProductionService (in `src/service/`)           │
│  Loads Production, applies events, persists to disk,     │
│  emits JSON-shaped dicts for the CLI to render            │
└──────────────────────────────────────────────────────────┘
                          │ (Python objects)
┌──────────────────────────────────────────────────────────┐
│  Tier 3 — Storage                                         │
│  - `<id>.production.json`   — current Production state    │
│  - `<id>.audit.jsonl`       — append-only event log       │
│  - `<id>.snapshots/*.json`  — content-addressed snapshots │
└──────────────────────────────────────────────────────────┘
```

The HTTP bridge is a thin shim over `ProductionService` — same Python surface, same JSON wire format.

---

## 3 · Command surface

These map to the open-production-plan.md "Production Operations" requirements. Each command is `op <verb> [args]` or `POST /v1/<verb>`.

### `op init <name> [--studio <studio_id>]`

Create a new Production in `DRAFT` state. Emits `init` AuditEntry.

```json
{
  "production": { "id": "prod_abc12345", "state": "DRAFT", "title": "Brand film Q3" },
  "next": "brief"
}
```

### `op brief <production_id> --topic "..." [--audience ...] [--tone ...]`

Generate 3 creative angles for the production's intent. Persists intent + the proposal into the production. Emits `decision` AuditEntry slot for the upcoming user choice.

```json
{
  "production_id": "prod_abc12345",
  "topic": "AI in creative industries",
  "angles": [
    {"id": "angle_1", "headline": "...", "why_it_matters": "..."},
    {"id": "angle_2", "headline": "...", "why_it_matters": "..."},
    {"id": "angle_3", "headline": "...", "why_it_matters": "..."}
  ],
  "next": "decide"
}
```

### `op decide <production_id> --choice <angle_id>`

User picks an angle. Emits `decision` + `gate_decision` AuditEntries (gates the choice through `ConfirmGate`). Transitions Production state to `BRIEFED`.

```json
{ "production_id": "prod_abc12345", "state": "BRIEFED", "chosen": "angle_2",
  "audit_event_id": "evt_2026…" }
```

### `op gate <production_id> --gate <evidence|consistency|publication> [--input ...]`

Run a named gate against the production. Persists verdict into audit_trail.

```json
{ "production_id": "prod_abc12345", "gate": "evidence",
  "results": [{ "claim_id": "c1", "status": "accepted", "reason": "..." }],
  "summary": "2/3 accepted" }
```

### `op status <production_id>`

Reconstruct current state from `(production.json) + (audit.jsonl applied in order)`. Returns full Production JSON.

```json
{ "production": { "schema_version": "1.0.0", "id": "prod_abc12345",
  "state": "BRIEFED", "scenes": [...], "audit_trail": [...] } }
```

### `op log <production_id> [--since <iso>] [--action <type>]`

Tail the audit log with optional filters. Useful for the reviewer, the bridge client, the judge-pack.

```json
{ "production_id": "prod_abc12345", "count": 12, "entries": [...] }
```

### `op snapshot <production_id> [--label "Pre-color grade"]`

Take a content-addressed snapshot. Writes `<id>.snapshots/snap_<sha>.json`. Emits `snapshot` AuditEntry.

```json
{ "snapshot_id": "snap_…", "content_hash": "abc123…", "label": "Pre-color grade" }
```

### `op branch <production_id> <branch_name> [--from-snapshot <snap_id>]`

Fork a named branch. Branches share the audit_trail at the divergence point. Each branch tracks its own state.

```json
{ "branch_id": "branch_darkcut", "parent_snapshot_id": "snap_…", "production_id": "prod_abc12345" }
```

### `op review <production_id>`

Run the visual reviewer (or text reviewer for the research vertical) against the production. Surfaces flagged items but never silently changes state.

```json
{ "production_id": "prod_abc12345", "flagged": [...], "passed": [...] }
```

### `op export <production_id> [--format manifest|json|html|pdf]`

Produce a publish artifact. Validates that `state == PUBLISHED` unless `--allow-draft`.

---

## 4 · ProductionService — the runtime

Single class, lives in `src/service/production_service.py`. Roughly:

```python
class ProductionService:
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir

    def init(self, name: str, studio_id: str | None = None) -> Production: ...

    def load(self, production_id: str) -> Production: ...
        # Reconstruct from production.json + audit.jsonl

    def apply_event(self, prod: Production, entry: AuditEntry) -> Production: ...
        # Apply a single audit event to the current state.
        # Returns a NEW Production; never mutates in place.

    def save(self, prod: Production) -> Production: ...
        # Persist production.json (full state) and audit.jsonl (new entries).

    def snapshot(self, prod: Production, label: str | None = None) -> VersionSnapshot: ...

    def branch(self, prod: Production, name: str, from_snapshot: str | None = None) -> Branch: ...

    def list_productions(self, studio_id: str | None = None) -> list[ProductionSummary]: ...
```

Key invariants:
- `apply_event` is pure — never mutates the input. The service always returns a new `Production`.
- `save` is atomic — write to temp file, rename, only then append to journal.
- `load` never trusts the production.json file's `audit_trail` field alone. It replays the journal from the last hydration to verify state matches the journal.

---

## 5 · Storage layout

```
<storage_dir>/
  prod_abc12345/
    production.json          # current state, recovered on load
    audit.jsonl              # append-only journal
    snapshots/
      snap_<sha>.json        # one file per snapshot
      ...
```

Why both `production.json` and `audit.jsonl`?
- `production.json` makes `load` cheap (no journal replay for typical reads).
- `audit.jsonl` is the source of truth. If `production.json` is corrupted, you can reconstruct from the journal alone.
- Snapshots are content-addressed so two identical branches produce the same hash, and diffing becomes cheap.

---

## 6 · HTTP bridge (`src/public_demo/`)

The current `src/public_demo/server.py` already wraps `src/demo_flow.py:build_demo_report()` in a small `ThreadingHTTPServer`. The migration:

1. `build_demo_report()` becomes a thin wrapper around `ProductionService` that:
   - Calls `service.init()` if no production_id is supplied
   - Calls `service.brief()` to generate angles
   - Uses `ConfirmGate` (already exists in `src/agents/confirm_gate.py`) to gate the user's choice
   - Uses the existing gates in `src/validation/gates.py` for evidence/consistency/publication
   - Calls `service.save()` at the end
2. The HTTP server exposes POST handlers that map to CLI commands:
   - `POST /v1/init` → `service.init`
   - `POST /v1/brief` → `service.brief`
   - `POST /v1/decide` → `service.decide`
   - `POST /v1/gate` → `service.gate`
   - `POST /v1/status` → `service.status`
   - `GET  /v1/log` → `service.log`

This makes the browser demo use the same backend as the CLI. **One ProductionService, two front-ends.**

---

## 7 · Migration path from `build_demo_report`

### Step 1 — keep the existing demo, add a Production wrapper

In `src/demo_flow.py`:

```python
def build_demo_report(topic, audience="educated_lay", tone="neutral",
                     chosen_angle_id=None, production_id=None,
                     audit_path=None, audit_dir="output/public-demo"):
    svc = ProductionService(storage_dir=Path(audit_dir).parent)
    if production_id is None:
        prod = svc.init(name=topic[:80])
    else:
        prod = svc.load(production_id)

    angles = generate_angles(topic, audience, tone)
    prod.intent = IntentDocument(topic=topic, audience=audience, tone=tone)
    prod = svc.apply_event(prod, AuditEntry(
        id=...,
        ts=...,
        actor="system",
        action_type="decision",
        payload={"operation": "propose_angles", "options": [a["id"] for a in angles]}
    ))

    # ... existing confirm_gate logic, but using svc.apply_event ...

    prod = svc.save(prod)
    return {... existing return shape ...}
```

This keeps the public API of `build_demo_report()` stable. No callsite changes. Only the internals learn about `Production`.

### Step 2 — add the CLI in `bin/op`

```bash
#!/usr/bin/env python
import argparse, json, sys
from pathlib import Path
from open_production.service.production_service import ProductionService

def main():
    parser = argparse.ArgumentParser(prog="op")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("name")

    args = parser.parse_args()
    svc = ProductionService(storage_dir=Path("./productions"))
    if args.cmd == "init":
        prod = svc.init(args.name)
        print(json.dumps({"production_id": prod.id, "state": prod.state}))

if __name__ == "__main__":
    main()
```

### Step 3 — wire HTTP server

Replace the body of `src/public_demo/server.py:do_POST()` with a thin dispatcher:

```python
def do_POST(self):
    body = json.loads(self.rfile.read(...))
    route = self.path.lstrip("/").split("/")
    cmd = route[1] if len(route) > 1 else ""
    svc = ProductionService(...)
    handler = {
        "init": svc.init,
        "brief": svc.brief,
        "decide": svc.decide,
        ...
    }.get(cmd)
    if not handler:
        self.send_error(404)
        return
    result = handler(**body)
    self._send_json(result)
```

---

## 8 · Failure modes & mitigations

| Failure | Effect | Mitigation |
|---|---|---|
| `production.json` corrupted | Can't load | Reconstruct from `audit.jsonl` (one-shot recovery script). |
| `audit.jsonl` entry invalid | Production can't be replayed | Validate every entry against schema on append. Catch at write time, not at load time. |
| Concurrent edits to same production | Lost writes | File lock per production_id. Acquire on `load`, release on `save`. |
| Snapshot hash collision | Snapshot overwrite | Use SHA-256 of canonical JSON serialization. P(hostile collision) is negligible. |
| Bridge client crashes mid-decide | Partial state | All events are idempotent. Replay gives same state. |
| Reviewer flags mid-generation | User surprised later | Reviewer is fail-closed (Law 5). Production state stays at last approved value. |

---

## 9 · What this design does NOT cover (scope cuts)

For the IBM submission window (~3 days), this bridge is **designed**, not **implemented**. Specifically deferred:

- ❌ Authentication / multi-user permissions — single-actor model. Production has an `actor` field but no role-based access.
- ❌ Real-time collaboration (Operational Transform / CRDT) — Roadmap Phase 3.
- ❌ Reviewer agent in the loop — `op review` is a stub; real Reviewer is Roadmap Phase 2 (4–6 weeks).
- ❌ Consistency Contract enforcement — `docs/architecture/production-document-schema.md` is shipped as a doc, but the gating path is not wired.
- ❌ Snapshot diff UI — snapshots exist as files, but no human-facing tool ships in the prototype window.

Each of these is already named in `open-production-plan.md`. This doc just narrows what we promise to ship by Friday.

---

## 10 · Verification checklist (when implemented)

- [ ] `op init "Test"` creates `productions/prod_<id>/{production.json, audit.jsonl}`.
- [ ] `op brief prod_<id> --topic "..."` returns 3 angles, persists intent, and emits a decision AuditEntry.
- [ ] `op decide prod_<id> --choice angle_2` advances state from DRAFT to BRIEFED.
- [ ] `op status prod_<id>` reconstructs correctly even if production.json is deleted (journal replay).
- [ ] `op snapshot prod_<id>` writes a sha256-named file under snapshots/.
- [ ] `op branch prod_<id> darkcut` creates a branch with its own state.
- [ ] All CLI commands round-trip through the HTTP bridge with identical JSON shape.
- [ ] Existing `build_demo_report()` call sites still pass their assertions.

When all 8 boxes tick, `src/demo_flow.py` is using `ProductionService` and the bridge is shipping.

---

*Designed as part of ACT-8 · CLI bridge · 2026-07-27 · companion to ACT-5 schema*