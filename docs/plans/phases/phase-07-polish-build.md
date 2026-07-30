# Phase 7 — Polish, Build & Integration Test

**Category:** Ship  
**Depends on:** Phase 6  
**Unlocks:** Production-ready app

---

## Goal

Add loading states, smooth transitions, and mobile breakpoints. Run `npm run build` and serve the static output from the existing Python server. Verify all 9 acceptance checks pass and confirm the backend test suite is still green.

---

## Polish checklist

### Loading states

| Trigger | Component | UX |
|---|---|---|
| `POST /api/reframe` in flight | `IntentForm` Continue button | Button text → "Generating angles…", disabled, opacity .7 |
| `POST /api/finalize` in flight | `AngleCards` pick button | Button text → "Running gates…", disabled |
| `GET /api/production/:id/status` on mount | Console thread | Skeleton rows (3 pulsing placeholder rows) |
| Poll in flight | Status bar | "live" dot pulses once |

### Transitions

| Element | Transition |
|---|---|
| Step dots advance | CSS transition `all .25s ease` on background/border/box-shadow |
| AngleCards appear | `opacity: 0 → 1` over 300ms after angles load |
| ResultPanel appears | Slide-down + fade: `transform: translateY(-8px) → 0` + opacity |
| PipelineWizard reveals | Fade-in 200ms after ResultPanel mounts |
| New audit event appended | Row fades in: `opacity: 0 → 1` over 200ms |
| Thinking dots | CSS `@keyframes` pulse: `opacity .6 → 1 → .6` staggered 150ms |

### Scroll behaviour

- After AngleCards appear: `element.scrollIntoView({ behavior: 'smooth', block: 'nearest' })`
- After ResultPanel appears: same
- Console thread: auto-scroll to bottom when new events appended (only if user is already at bottom)

---

## Responsive breakpoints

### Guided Flow (`/flow`)

| Breakpoint | Change |
|---|---|
| `< 1024px` | Helper card moves below wizard col (stacks vertically) |
| `< 768px` | Left rail collapses to icon-only (40px) |
| `< 640px` | Angle grid becomes single column |
| `< 480px` | Platform pills wrap to 2 per row |
| `< 480px` | Pipeline grid becomes 2 columns |

### Agent Console (`/console`)

| Breakpoint | Change |
|---|---|
| `< 1200px` | Context rail hidden (toggle button appears top-right) |
| `< 900px` | Crew rail collapses to icon-only (40px wide) |
| `< 640px` | Status bar labels hidden, values only |
| `< 480px` | Shot strip collapses: show 3 blocks + "…+3" overflow |

---

## Production build

### Step 1 — Build React app

```bash
cd web
npm run build
# Output: web/dist/index.html + web/dist/assets/
```

### Step 2 — Serve from Python server

Add a static file handler to `src/public_demo/server.py` that serves `web/dist/` for any path that does not start with `/api`.

The handler logic:

```python
# Pseudocode — exact implementation in Phase 7
DIST_DIR = Path(__file__).parent.parent.parent / "web" / "dist"

def serve_static(path: str) -> tuple[bytes, str]:
    """Serve web/dist/ for non-API paths. SPA fallback to index.html."""
    if path.startswith('/api'):
        raise NotStaticPath()
    file_path = DIST_DIR / path.lstrip('/')
    if file_path.is_file():
        mime = guess_mime(file_path.suffix)
        return file_path.read_bytes(), mime
    # SPA fallback — any unknown path returns index.html
    return (DIST_DIR / 'index.html').read_bytes(), 'text/html'
```

MIME types to handle:
```
.html → text/html
.js   → application/javascript
.css  → text/css
.json → application/json
.ico  → image/x-icon
.png  → image/png
.svg  → image/svg+xml
.woff2 → font/woff2
```

### Step 3 — Verify serve

```bash
# Terminal 1
python src/public_demo/server.py

# Terminal 2
curl -s http://127.0.0.1:8000/ | head -5
# Expected: <!DOCTYPE html> from web/dist/index.html

curl -s http://127.0.0.1:8000/flow | head -5
# Expected: <!DOCTYPE html> (SPA fallback)

curl -s -X POST http://127.0.0.1:8000/api/reframe \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI in film","audience":"general","tone":"neutral"}' | python -m json.tool
# Expected: {"angles": [...]}
```

---

## Final acceptance gate (all 9 must pass)

| # | Test | Command / action | Expected |
|---|---|---|---|
| 1 | TypeScript | `cd web && npm run typecheck` | 0 errors |
| 2 | ESLint | `cd web && npm run lint` | 0 errors, 0 warnings |
| 3 | Build | `cd web && npm run build` | Exit 0, `web/dist/` generated |
| 4 | Guided Flow renders | Open `http://localhost:5173/flow` (dev) | Layout matches `02-guided-flow.svg` |
| 5 | Full flow run | Submit intent → pick angle | Real gate results + production_id appear |
| 6 | Cross-view nav | Click "Open in Agent Console" | Console opens at `/console?id=prod_xxx` |
| 7 | Live polling | Wait 5s on Console page | Audit events auto-refresh from server |
| 8 | Mobile layout | Resize browser to 375px | No horizontal scroll, readable layout |
| 9 | Backend tests | `python -m pytest tests/ -q` | All 324 tests pass (backend unchanged) |

---

## `package.json` scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src --ext .ts,.tsx --max-warnings 0",
    "format": "prettier --write src/**/*.{ts,tsx,css}"
  }
}
```

---

## Notes

- `web/dist/` is gitignored — generated artefact, not committed
- `web/node_modules/` is gitignored
- Add `web/dist` and `web/node_modules` to `.gitignore` if not already present
- The Python test suite (`tests/`) never imports anything from `web/` — zero risk of backend regression
