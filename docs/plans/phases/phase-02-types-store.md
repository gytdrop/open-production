# Phase 2 — TypeScript Types + Zustand Store

**Category:** Data Layer  
**Depends on:** Phase 1  
**Unlocks:** Phase 3

---

## Goal

Define TypeScript interfaces that mirror every Python dataclass in `src/schema/production_document.py`. Build the Zustand store with two slices (Flow + Console) and write typed API hook wrappers for the three backend endpoints. No UI is built in this phase.

---

## File structure produced

```
web/src/
├── types/
│   └── production.ts          ← mirrors src/schema/production_document.py exactly
├── store/
│   └── productionStore.ts     ← Zustand: shared + flow slice + console slice
└── hooks/
    ├── useProductionApi.ts    ← fetch wrappers: reframe(), finalize(), getStatus()
    └── useAuditPoll.ts        ← setInterval 5s poll on /api/production/:id/status
```

---

## Types to define (`production.ts`)

```ts
// ── Literal unions (mirror Python Literal types) ──────────────────────────
export type ProductionState =
  | 'DRAFT' | 'BRIEFED' | 'IN_PRODUCTION'
  | 'IN_REVIEW' | 'APPROVED' | 'PUBLISHED'

export type ActionType =
  | 'gate_decision' | 'decision' | 'lock' | 'unlock'
  | 'snapshot' | 'branch' | 'merge'
  | 'state_transition' | 'stage_advance' | 'override' | 'comment' | 'system'

export type ShotStatus =
  | 'draft' | 'in_production' | 'generated'
  | 'in_review' | 'approved' | 'rejected'

// ── Core dataclasses ──────────────────────────────────────────────────────
export interface IntentDocument {
  topic: string
  audience?: string
  tone?: string
  platform?: string
  duration_sec?: number
  style_seed?: string
}

export interface AuditEntry {
  id: string
  ts: string
  actor: string
  action_type: ActionType
  gate_name?: string
  claim_id?: string
  decision_status?: string
  reason?: string
  evidence: Record<string, unknown>
  payload: Record<string, unknown>
  state_before?: string
  state_after?: string
}

export interface Shot {
  id: string
  scene_id: string
  intent: string
  duration_sec: number
  status: ShotStatus
  camera?: CameraSpec
  lighting?: LightingSpec
  audio?: AudioSpec
  locked: boolean
  storyboard_frame?: string
  color_spec?: Record<string, unknown>
  motion_spec?: Record<string, unknown>
}

export interface Scene {
  id: string
  name: string
  shots: Shot[]
  location?: string
  notes?: string
  stage?: string
}

export interface Production {
  id: string
  state: ProductionState
  intent: IntentDocument
  scenes: Scene[]
  audit_trail: AuditEntry[]
  title?: string
  created_at: string
  updated_at: string
  references: Reference[]
  characters: Character[]
  environments: Environment[]
  branches: Branch[]
  snapshots: VersionSnapshot[]
  metadata: Record<string, unknown>
}

// ── API response shapes ────────────────────────────────────────────────────
export interface Angle {
  id: string
  name: string
  summary: string
  risk_focus: string
  questions_to_address: string[]
}

export interface DemoRunResult {
  topic: string
  audience: string
  tone: string
  angles: Angle[]
  chosen_angle: Angle
  accepted_claims: number
  rejected_claims: number
  contradictions: unknown[]
  summary: string
  audit_path: string
  audit_entries: AuditEntry[]
  production_id: string | null
  reviewer_results: unknown[]
  research_result: { gate_passed: boolean; source_count: number; verdict: string }
  env_result: { proposals?: unknown[] }
  shot_plan_result: { shots?: unknown[] }
  editor_result: { proposals?: unknown[] }
  branch_result: { branch_id?: string; snapshot_id?: string }
  publish_result: { proposals?: unknown[] }
  archive_result: { archived_at?: string; expires_at?: string }
}
```

---

## Store shape (`productionStore.ts`)

```ts
interface ProductionStore {
  // ── Shared ──────────────────────────────────────────────────
  productionId: string | null
  production: Production | null
  pollingActive: boolean

  // ── Flow slice ───────────────────────────────────────────────
  intent: { topic: string; audience: string; tone: string }
  angles: Angle[]
  chosenAngleId: string | null
  runResult: DemoRunResult | null
  flowStep: number          // 1–7, drives StepIndicator
  flowStatus: string        // inline status message
  flowLoading: boolean

  // ── Console slice ────────────────────────────────────────────
  auditEntries: AuditEntry[]
  selectedActor: string | null   // null = show all
  activeTab: 'events' | 'proposals' | 'state'
  consoleError: string | null

  // ── Actions ──────────────────────────────────────────────────
  setIntent(intent: Partial<ProductionStore['intent']>): void
  loadAngles(): Promise<void>
  finalizeRun(angleId: string): Promise<void>
  pollProduction(): Promise<void>
  setSelectedActor(actor: string | null): void
  setActiveTab(tab: ProductionStore['activeTab']): void
  resetFlow(): void
}
```

---

## API hooks contract (`useProductionApi.ts`)

| Function | Method | Endpoint | Request body | Returns |
|---|---|---|---|---|
| `reframe(intent)` | POST | `/api/reframe` | `{ topic, audience, tone }` | `{ angles: Angle[] }` |
| `finalize(intent, angleId)` | POST | `/api/finalize` | `{ topic, audience, tone, chosen_angle_id }` | `DemoRunResult` |
| `getStatus(id)` | GET | `/api/production/:id/status` | — | `Production` |

### `useAuditPoll.ts`
```ts
// Starts a 5-second interval calling getStatus(id)
// Diffs new audit_trail entries against store, appends only new ones
// Clears interval on component unmount
// Silently skips on network error (retries next tick)
export function useAuditPoll(productionId: string | null): void
```

---

## Acceptance criteria

| Check | Expected |
|---|---|
| `npm run typecheck` | 0 errors — all types resolve |
| Import `Production` in a test component | No TS errors |
| Store `loadAngles()` called | Sets `flowLoading: true` then `angles: Angle[]` |
| `useAuditPoll(null)` | Does nothing (guard on null) |
| All fetch wrappers return typed promises | No `any` in API hooks |
