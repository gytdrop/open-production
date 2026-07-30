# Phase 3 — App Shell, Router & Design System

**Category:** Shell  
**Depends on:** Phase 2  
**Unlocks:** Phase 4 + Phase 5 (parallel)

---

## Goal

Wire React Router, build the global `NavBar` that matches the SVG wireframe header exactly, define the Tailwind design tokens, and build the shared components that both views use: `StateMachineBadge`, `GateBadge`, `AuditEntryRow`, `ProposalCard`.

---

## File structure produced

```
web/src/
├── main.tsx                   ← ReactDOM.createRoot, BrowserRouter, <App/>
├── App.tsx                    ← Routes: /flow, /console, redirect / → /flow
├── components/
│   ├── NavBar.tsx             ← header bar matching 02/04 SVG header exactly
│   ├── StateMachineBadge.tsx  ← ProductionState → colour pill (6 states)
│   ├── GateBadge.tsx          ← decision_status → colour badge
│   ├── AuditEntryRow.tsx      ← single timestamped event row
│   └── ProposalCard.tsx       ← agent proposal: 3 options + Approve/Adjust/Override
└── index.css                  ← CSS custom properties + Tailwind base
```

---

## NavBar specification

Matches the header present in both `02-guided-flow.svg` and `04-agent-console.svg`:

```
┌──[5px accent bar]──[OPEN PRODUCTION / view title]──[tab: Guided | Console]──[view label / persona / sub]──┐
│  height: 60px  │  background: rgba(0,0,0,0.5)  │  position: fixed top  │  border-bottom: #2d3340          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Slot | Content | Source |
|---|---|---|
| Left accent | `width: 5px; background: #6b8eff` | Both SVGs line 6 |
| Brand top | `OPEN PRODUCTION` — 10px bold #6b8eff | Both SVGs line 7 |
| Brand bottom | Current view title — 17px #e4e7eb | Both SVGs line 8 |
| Center | Tab buttons: **Guided Flow** / **Agent Console** | Added for React SPA |
| Right top | View label e.g. `02 / GUIDED FLOW` — 10px bold #a78bfa | Both SVGs |
| Right mid | Persona — 11px #8a93a6 | Both SVGs |
| Right bottom | Sub-label — 9px #5d6678 | Both SVGs |

---

## Design tokens (`index.css`)

```css
:root {
  /* from SVG wireframes */
  --bg:      #0f1117;
  --panel:   rgba(255,255,255,0.025);
  --border:  #2d3340;
  --border2: #3a4256;
  --text:    #e4e7eb;
  --muted:   #8a93a6;
  --dim:     #5d6678;
  --accent:  #6b8eff;
  --purple:  #a78bfa;
  --green:   #22c55e;
  --amber:   #fbbf24;
  --pink:    #f472b6;
  --cyan:    #67e8f9;
}
body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, Inter, "Segoe UI", Helvetica, Arial, sans-serif;
}
```

---

## StateMachineBadge — 6 states

```
DRAFT         → rgba(255,255,255,.08)  text #8a93a6
BRIEFED       → rgba(107,142,255,.18)  text #a7c8ff
IN_PRODUCTION → rgba(251,191,36,.18)   text #fde8a0
IN_REVIEW     → rgba(167,139,250,.18)  text #d4b4fe
APPROVED      → rgba(34,197,94,.16)    text #86efac
PUBLISHED     → rgba(127,212,193,.18)  text #c0f4e7
```

Usage: `<StateMachineBadge state={production.state} />`

---

## GateBadge — decision status colours

```
accepted           → rgba(127,212,193,.15)  text #c0f4e7
rejected           → rgba(255,122,122,.15)  text #ffb3b3
contradiction_detected → rgba(240,184,93,.15) text #fde8a0
publish_ok         → rgba(34,197,94,.15)    text #86efac
publish_rejected   → rgba(255,122,122,.15)  text #ffb3b3
contract_passed    → rgba(127,212,193,.15)  text #c0f4e7
contract_violated  → rgba(255,122,122,.15)  text #ffb3b3
gate_decision      → rgba(107,142,255,.13)  text #a7c8ff   (generic)
decision           → rgba(167,139,250,.13)  text #d4b4fe
system             → rgba(255,255,255,.08)  text #8a93a6
```

---

## App.tsx router

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from '@/components/NavBar'
import ProductionFlow from '@/views/ProductionFlow'
import AgentConsole from '@/views/AgentConsole'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/flow" element={<ProductionFlow />} />
        <Route path="/console" element={<AgentConsole />} />
        <Route path="*" element={<Navigate to="/flow" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
```

---

## Acceptance criteria

| Check | Expected |
|---|---|
| `/flow` route renders | Placeholder `<ProductionFlow />` mounts without crash |
| `/console` route renders | Placeholder `<AgentConsole />` mounts without crash |
| `/` redirects | Browser navigates to `/flow` |
| NavBar visible | 60px header with accent bar, brand text, tabs |
| `<StateMachineBadge state="IN_PRODUCTION" />` | Renders amber pill |
| `<GateBadge status="accepted" />` | Renders green pill |
| `<GateBadge status="rejected" />` | Renders red pill |
| `npm run typecheck` | 0 errors |
