# Phase 1 — Project Scaffold & Toolchain

**Category:** Foundation  
**Depends on:** Nothing — start here  
**Unlocks:** Phase 2

---

## Goal

Initialise the `web/` directory with Vite 5 + React 18 + TypeScript + Tailwind CSS v4 + ESLint + Prettier. Configure the Vite dev proxy so all `/api/*` calls forward to the existing Python server at `http://127.0.0.1:8000`. No UI is built in this phase.

---

## File structure produced

```
web/
├── index.html                 ← Vite HTML entry, mounts <div id="root">
├── vite.config.ts             ← proxy /api → localhost:8000, path aliases
├── tsconfig.json              ← strict mode, paths: @/* → src/*
├── tsconfig.node.json
├── package.json               ← react, react-dom, react-router-dom, zustand, tailwind
├── tailwind.config.ts         ← design tokens matching wireframe CSS vars
├── postcss.config.js
└── .eslintrc.cjs              ← react-hooks, @typescript-eslint rules
```

---

## NPM dependencies

| Package | Purpose |
|---|---|
| `react` `react-dom` | UI runtime |
| `react-router-dom v6` | `/flow` + `/console` routes |
| `zustand` | Global state store |
| `tailwindcss` `@tailwindcss/vite` | Styling |
| `typescript` `@types/react` `@types/react-dom` | Type safety |
| `eslint` `eslint-plugin-react-hooks` `@typescript-eslint/eslint-plugin` | Code quality |
| `prettier` | Formatting |

---

## Key config details

### `vite.config.ts`
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### `tailwind.config.ts` — design tokens from wireframes
```ts
// CSS vars to register — match the SVG wireframe palette exactly
// --bg: #0f1117
// --border: #2d3340
// --border2: #3a4256
// --text: #e4e7eb
// --muted: #8a93a6
// --dim: #5d6678
// --accent: #6b8eff
// --purple: #a78bfa
// --green: #22c55e
// --amber: #fbbf24
// --pink: #f472b6
// --cyan: #67e8f9
```

---

## Commands

```bash
# From repo root
npm create vite@latest web -- --template react-ts
cd web
npm install react-router-dom zustand
npm install -D tailwindcss @tailwindcss/vite postcss autoprefixer
npm install -D eslint eslint-plugin-react-hooks @typescript-eslint/eslint-plugin prettier
```

---

## Acceptance criteria

| Check | Command | Expected |
|---|---|---|
| Dev server starts | `cd web && npm run dev` | Vite on :5173, blank React page visible |
| TypeScript compiles | `npm run typecheck` | 0 errors |
| ESLint passes | `npm run lint` | 0 errors, 0 warnings |
| Proxy forwards | `curl http://localhost:5173/api/reframe` (with server running) | Response from Python server |
| Tailwind loads | Add `className="text-red-500"` to App, inspect browser | Class applies |

---

## Notes

- The Python backend in `src/public_demo/server.py` is **never modified** in any phase.
- `web/` lives at the repo root alongside `src/`, `docs/`, `tests/`.
- Dev port is `5173`; production build output is `web/dist/`.
