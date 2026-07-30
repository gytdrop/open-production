# Phase 6 — Live API Wiring & Real-Time Data

**Category:** Integration  
**Depends on:** Phase 4 + Phase 5  
**Unlocks:** Phase 7

---

## Goal

Connect every store action and component to the live Python backend. Replace all mock data with real API responses. Wire the 5-second audit polling loop. Enable cross-view navigation via `?id=` URL parameter. Add error states.

---

## Prerequisites

The Python server must be running before testing this phase:

```bash
# From repo root
python src/public_demo/server.py
# → http://127.0.0.1:8000
```

Vite dev proxy forwards `web/` → `:5173/api/*` → `:8000/api/*`.

---

## What changes per view

### Guided Flow — live connections

| Component | Was (mock) | Becomes (live) |
|---|---|---|
| `IntentForm` submit | Sets mock angles | Calls `POST /api/reframe` → real `Angle[]` from CreativeReframing agent |
| `AngleCards` pick | Shows mock result | Calls `POST /api/finalize` → real `DemoRunResult` with gate verdicts |
| `ResultPanel` | Mock counts | Real `accepted_claims`, `rejected_claims`, `contradictions.length` from response |
| `ResultPanel` production_id | Mock id | Real `result.production_id` stored in Zustand + URL: `/console?id=prod_xxx` |
| `PipelineWizard` stages | Hardcoded done | Derived from `runResult` fields (see table below) |
| Audit download button | No-op | `JSON.stringify(runResult.audit_entries)` → blob download |
| "Open in Agent Console" | Static link | `navigate('/console?id=' + productionId)` |

**PipelineWizard stage derivation from `runResult`:**

```ts
const doneStages = new Set<number>([1]) // Intent always done after run

if (runResult.research_result?.gate_passed)          doneStages.add(2)
if (runResult.ref_cluster_result?.proposals)         doneStages.add(3)
if (runResult.moodboard_result?.proposals)           doneStages.add(4)
if (runResult.chosen_angle)                          doneStages.add(5)
if (runResult.env_result?.proposals)                 doneStages.add(9)
if (runResult.shot_plan_result?.shots)               doneStages.add(10)
if (runResult.editor_result?.proposals)              doneStages.add(12)
if (runResult.reviewer_results?.length > 0)          doneStages.add(23)
if (runResult.branch_result?.branch_id)              doneStages.add(24)
if (runResult.publish_result?.proposals)             doneStages.add(25)
if (runResult.archive_result?.archived_at)           doneStages.add(26)
if (runResult.accepted_claims > 0)                   doneStages.add(25)

const activeStages = new Set<number>([3, 25].filter(n => !doneStages.has(n)))
```

---

### Agent Console — live polling

| Element | Was (mock) | Becomes (live) |
|---|---|---|
| Production loaded on mount | Static mock data | Read `?id=` param → call `GET /api/production/:id/status` |
| Audit events in thread | Static 5 mock rows | `auditEntries` from store, polled every 5s |
| Status bar values | Hardcoded strings | Live from `production.state`, `audit_trail.length`, etc. |
| `StateMachineBadge` | Static "IN_PRODUCTION" | `production.state` from store |
| Shot strip | Static S01–S06 | `production.scenes[0].shots` mapped to blocks |
| Actor filter | Visual only | Filters `auditEntries` by `entry.actor === selectedActor` |
| Context rail — recent events | Static 5 rows | Last 5 `auditEntries` sorted by `ts` desc |
| Context rail — branches | Static chips | `production.branches.map(b => b.name)` |
| Context rail — locked | Static list | Gate decisions with `decision_status: 'accepted'` |

---

## `useAuditPoll` implementation detail

```ts
export function useAuditPoll(productionId: string | null) {
  const pollProduction = useProductionStore(s => s.pollProduction)

  useEffect(() => {
    if (!productionId) return
    pollProduction()                          // immediate first fetch
    const id = setInterval(pollProduction, 5000)
    return () => clearInterval(id)           // cleanup on unmount
  }, [productionId, pollProduction])
}
```

`pollProduction` in the store:
```ts
async pollProduction() {
  const { productionId } = get()
  if (!productionId) return
  try {
    const prod = await getStatus(productionId)
    // Diff new audit entries: only append entries not already in store
    const existingIds = new Set(get().auditEntries.map(e => e.id))
    const newEntries = prod.audit_trail.filter(e => !existingIds.has(e.id))
    set(s => ({
      production: prod,
      auditEntries: [...s.auditEntries, ...newEntries],
    }))
  } catch {
    // Silent — retry next interval
  }
}
```

---

## URL routing & cross-view navigation

### Flow → Console
After `finalizeRun()` succeeds and `production_id` is set:
```tsx
<button onClick={() => navigate(`/console?id=${productionId}`)}>
  Open in Agent Console →
</button>
```

### Console on mount
```tsx
// In AgentConsole/index.tsx
const [searchParams] = useSearchParams()
const id = searchParams.get('id')

useEffect(() => {
  if (id) useProductionStore.getState().setProductionId(id)
}, [id])

useAuditPoll(id)  // starts polling
```

### Empty console (no id)
```tsx
if (!productionId) {
  return (
    <div>
      No production loaded. Start one from{' '}
      <Link to="/flow">Guided Flow</Link>.
    </div>
  )
}
```

---

## Error states

| Scenario | UI response |
|---|---|
| `POST /api/reframe` fails | Inline status below form: "Could not generate angles. Is the server running?" |
| `POST /api/finalize` fails | Inline status below angle cards: "The run did not complete." |
| `GET /api/production/:id/status` 404 | Console shows "Production not found" message, polling stops |
| Network error during poll | Silent, retries next 5s tick. Console keeps last known state. |
| `production_id` is null after finalize | ResultPanel hides the "Open in Console" button |

---

## Audit event thread rendering

Convert `AuditEntry` to thread messages:

```ts
// Mapping: action_type / gate_name → thread component
'state_transition'  → <SystemEvent />      (green dot)
'gate_decision'     → <SystemEvent />      (colour = decision_status)
'decision'          → actor === 'human'
                       ? <UserMessage />    (green tint)
                       : <AgentMessage />   (actor colour)
'system'            → <SystemEvent />
// All others        → <AgentMessage actor={entry.actor} />
```

Actor → colour mapping (matches CrewRail avatar colours):
```ts
const ACTOR_COLOURS: Record<string, string> = {
  'demo_flow':              '#5d6678',
  'CreativeReframing':      '#6b8eff',
  'ResearchAgent':          '#f0b85d',
  'MoodboardAgent':         '#a78bfa',
  'ShotDesignerAgent':      '#67e8f9',
  'ReviewerAgent':          '#f472b6',
  'EditorAgent':            '#22c55e',
  'ColoristAgent':          '#fb923c',
  'human':                  '#22c55e',
  'system':                 '#22c55e',
}
```

---

## Acceptance criteria

| # | Check | Expected |
|---|---|---|
| 1 | Submit real topic → Continue | `POST /api/reframe` called, real angles rendered |
| 2 | Pick real angle | `POST /api/finalize` called, real gate counts rendered |
| 3 | Real production_id appears | Monospace chip shown, "Open in Console" enabled |
| 4 | Click "Open in Console" | Navigates to `/console?id=prod_xxx` |
| 5 | Console mounts with `?id=` | `GET /api/production/:id/status` called immediately |
| 6 | Wait 5s on Console | Second poll fires, new audit entries append to thread |
| 7 | Actor filter click | Thread filters to entries where `actor === selected` |
| 8 | API failure | Inline error message appears, no crash |
| 9 | `/console` with no `?id=` | "No production loaded" message + link to flow |
