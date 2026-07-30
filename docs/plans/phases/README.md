# React App Build Phases — `docs/plans/phases/`

> Step-by-step build plan for the Open Production React + Vite frontend.  
> Backend: `src/public_demo/server.py` — **never modified**.  
> Wireframes: `docs/wireframes/02-guided-flow.svg` + `docs/wireframes/04-agent-console.svg`.

---

## Phase index

| File | Phase | Category | Depends on | Parallel with |
|---|---|---|---|---|
| [`phase-01-scaffold.md`](./phase-01-scaffold.md) | **P1 — Scaffold** | Foundation | Nothing | — |
| [`phase-02-types-store.md`](./phase-02-types-store.md) | **P2 — Types + Store** | Data Layer | P1 | — |
| [`phase-03-shell-nav.md`](./phase-03-shell-nav.md) | **P3 — Shell + Nav** | Shell | P2 | — |
| [`phase-04-guided-flow.md`](./phase-04-guided-flow.md) | **P4 — Guided Flow** | View 1 / 2 | P3 | **P5** |
| [`phase-05-agent-console.md`](./phase-05-agent-console.md) | **P5 — Agent Console** | View 2 / 2 | P3 | **P4** |
| [`phase-06-api-wiring.md`](./phase-06-api-wiring.md) | **P6 — API Wiring** | Integration | P4 + P5 | — |
| [`phase-07-polish-build.md`](./phase-07-polish-build.md) | **P7 — Polish + Build** | Ship | P6 | — |

---

## Dependency graph

```
P1 Scaffold
  └─► P2 Types + Store
        └─► P3 Shell + Nav
              ├─► P4 Guided Flow ──────┐
              └─► P5 Agent Console ────┴─► P6 API Wiring
                                               └─► P7 Polish + Build
```

> **P4 and P5 are fully parallel** — they share no component dependencies
> and can be built simultaneously by two developers (or two sessions).

---

## Technology stack

| Layer | Choice |
|---|---|
| Framework | React 18 |
| Build tool | Vite 5 |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 |
| State | Zustand |
| Router | React Router v6 |
| Dev proxy | Vite `server.proxy` → `http://127.0.0.1:8000` |

---

## Backend API surface (read-only, never changed)

| Method | Endpoint | Used in |
|---|---|---|
| `POST` | `/api/reframe` | P4 → P6: generate 3 creative angles |
| `POST` | `/api/finalize` | P4 → P6: run gates, create production |
| `GET` | `/api/production/:id/status` | P5 → P6: 5s polling for live audit events |

---

## Project layout after all phases complete

```
web/                           ← Vite project root (new)
├── index.html
├── vite.config.ts             ← proxy + path aliases
├── tsconfig.json
├── package.json
├── tailwind.config.ts
└── src/
    ├── main.tsx               ← ReactDOM root
    ├── App.tsx                ← BrowserRouter + Routes
    ├── index.css              ← CSS vars + Tailwind base
    ├── types/
    │   └── production.ts      ← TypeScript mirrors of Python dataclasses
    ├── store/
    │   └── productionStore.ts ← Zustand (flow + console slices)
    ├── hooks/
    │   ├── useProductionApi.ts
    │   └── useAuditPoll.ts
    ├── components/
    │   ├── NavBar.tsx
    │   ├── StateMachineBadge.tsx
    │   ├── GateBadge.tsx
    │   ├── AuditEntryRow.tsx
    │   └── ProposalCard.tsx
    └── views/
        ├── ProductionFlow/
        │   ├── index.tsx
        │   ├── StepIndicator.tsx
        │   ├── IntentForm.tsx
        │   ├── AngleCards.tsx
        │   ├── ResultPanel.tsx
        │   └── PipelineWizard.tsx
        └── AgentConsole/
            ├── index.tsx
            ├── CrewRail.tsx
            ├── ConversationThread.tsx
            ├── SystemEvent.tsx
            ├── AgentMessage.tsx
            ├── OptionCards.tsx
            ├── UserMessage.tsx
            ├── ThinkingBubble.tsx
            ├── ReviewerFlag.tsx
            ├── ShotStrip.tsx
            ├── CommandBar.tsx
            └── ContextRail.tsx
```

---

## Final acceptance gate (Phase 7)

| # | Test | Expected |
|---|---|---|
| 1 | `npm run typecheck` | 0 TS errors |
| 2 | `npm run lint` | 0 ESLint warnings |
| 3 | `npm run build` | Exit 0, `web/dist/` generated |
| 4 | `/flow` renders | Matches `02-guided-flow.svg` layout |
| 5 | Submit intent + pick angle | Real gate results + `production_id` appear |
| 6 | "Open in Agent Console" | Navigates to `/console?id=prod_xxx` |
| 7 | 5s poll on Console | Audit events auto-refresh from server |
| 8 | Resize to 375px | No horizontal scroll |
| 9 | `python -m pytest tests/ -q` | All 324 backend tests pass |
