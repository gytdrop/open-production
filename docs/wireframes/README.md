# Wireframes — ACT-3

> Five views of the same production engine, mapped to personas, principles, and the 26-stage pipeline.

**Status:** ACT-3 complete · 2026-07-27
**Owner:** Design
**Inputs:** `open-production-plan.md` Sections 8 (personas), 10 (5 views), 11 (AI model), 14 (pipeline) + `docs/principles.md`

---

## What's in this folder

| File | Size | Persona | Principle embodied |
|---|---|---|---|
| `01-directors-canvas.svg` | 17 KB | Jordan · Creative Professional | Law 3, Law 5 |
| `02-guided-flow.svg` | 7 KB | Sam · Emerging Creator | Law 1, Law 4 |
| `03-timeline-editor.svg` | 16 KB | Jordan · Editor mode | Law 2 (non-destructive) |
| `04-agent-console.svg` | 18 KB | Jordan · AI-native mode | Law 5 + Reviewer as first-class |
| `05-node-graph.svg` | 16 KB | Alex · Studio Lead / Developer | Axiom 2 (every view = same model) |
| `all-views-composite.svg` | 25 KB | All five as thumbnails | overview / judge-pack |
| `README.md` | this file | — | — |

All wireframes are low-fidelity by design — boxes, labels, hierarchy. No polished visuals, no design-system polish. The structure is what's being argued about, not the surface.

---

## The universal rule (underpins all five)

> Switching between views is instant. No data is lost when switching. Changes in one view immediately reflect in all views.
> — `open-production-plan.md` §10

Every wireframe in this folder renders a slice of the same underlying Production state. The View is the choice; the State is the truth. This is Axiom 2 from `docs/principles.md` made concrete.

---

## Per-view design notes

### 01 · Director's Canvas — pro default

**Persona:** Jordan · Creative Professional · trained filmmaker
**When shown:** any time the user opens a shot / scene in director mode
**Layout (left → right):**
- 60 px tool rail (select, hand, frame, link, note, voice)
- Center: infinite canvas. Scenes are containers, shots are cards inside. Reference pins float with caption.
- Right rail (340 px): properties panel. Camera, Lighting, Audio, Reviewer sections. Each section's properties appear for the selected shot only.
- Bottom: cinematic timeline with version branches.
- Floating: AI proposal popovers appear when an agent wants the user's decision. **Law 5 made visible.**
- Status bar: stage · approved count · generation queue · crew health · audit events.

**Key design decision:** AI proposals appear **as floating popovers on the canvas**, not as a separate "AI tab." This is so the user encounters AI in the same visual space as their own work, not in a quarantined panel.

### 02 · Guided Production Flow — beginner default

**Persona:** Sam · Emerging Creator · self-taught, short time-to-gratification
**When shown:** Sam's first session, or whenever Sam clicks "go back to guided mode."
**Layout:**
- Centered wizard column (max 720 px).
- Progress dots at top: 1 of 7 stages.
- One question per screen: idea → references → mood → cast → plan → generate → publish.
- Big textarea, gentle prompts, plain language ("a few sentences is fine").
- Right side: 💡 helper card. No jargon, no audit-trail references, no crew concepts visible.
- Bottom: "Continue →" CTA. Never says "Submit" or "Run."

**Key design decision:** Sam sees **none** of the AI crew model. The system pretends to be one voice — "we'll help you develop it." The crew is busy behind the scenes but the user never has to manage it. This is Law 4 (same engine, fewer knobs) taken to its conclusion.

### 03 · Timeline Editor — editor default

**Persona:** Jordan · same persona, different mode (post-shot, into editing)
**When shown:** when the user clicks into Timeline view or after generation is locked
**Layout:**
- Top: scene tabs (Scene 1, 2, 3 active).
- Left rail (180 px): asset bin with sections (Video · Audio · Music · SFX · Voice).
- Center: horizontal timeline with 5 tracks (V1, V2, A1, A2, A3). Ruler with time markers. Playhead with transport controls at bottom.
- Right rail (300 px): Clip Inspector — timing, transition, audio, speed, reviewer.
- In/Out markers in green, playhead in white.
- Bottom: transport (⏮ ⏯ ⏭ ⏹ 🔁) + zoom slider + snap/ripple/replace toggles + ⌘J/K/L hint.

**Key design decision:** Reviewer verdict appears **inside the Clip Inspector**, not as a popup. Cuts aren't shippable until the Reviewer has cleared them — but the user gets the verdict in the same panel they use to tweak the cut. No context switch.

### 04 · Agent Console — AI power user default

**Persona:** Jordan · same persona, AI-native mode (knows the crew, wants to see them)
**When shown:** when the user clicks "Crew" view, or for users who prefer chat-native interfaces
**Layout:**
- Left rail (220 px): crew list. 12 agents, each with avatar + status dot (green=ready, amber=thinking, magenta=flagged, gray=standby).
- Center: threaded conversation. System events, agent proposals, user replies, reviewer flags. Each proposal card has 3 options the user can approve, reject, or adjust.
- Right rail (460 px): context — current shot details, recent events log, branches, locked decisions.
- Bottom: ⌘K command palette input + examples ("ask review to recheck S07").

**Key design decision:** The crew is **visible** but **bounded**. Each agent card shows what they own and what they're doing. The Reviewer agent (magenta) has special status — when it flags something, it gets visual prominence. This makes the AI's bounded scope legible, which is Law 5 in spirit.

### 05 · Node Graph — expert / developer default

**Persona:** Alex · Studio Lead / Developer · wants to see the wiring
**When shown:** when the user clicks "Graph" view, or for power users debugging a workflow
**Layout:**
- Full canvas with grid background.
- Nodes connected by edges. Node types color-coded: violet (composition), blue (transform), green (evaluation/gate), magenta (reviewer).
- Edges labeled with data flow names (camera_spec, lighting_spec, quality_verdict.json).
- Right rail (300 px): Node Inspector for the selected node — metadata, inputs, outputs, status, provenance, actions.
- Bottom: DAG summary + keyboard shortcut hints.

**Key design decision:** Every node has an **Actions panel** with the three safe operations: approve (override), re-run, branch. This makes the "what can I do here?" question answerable in one place. Inspired by ComfyUI / Unreal Blueprints — advanced users want to see the wiring, not abstractions of it.

---

## View selection logic

The view is chosen automatically per-persona but overridable in settings. Suggested heuristics:

| Signal | Default view |
|---|---|
| New user, never opened a project | 02 · Guided Flow |
| Opened a scene for the first time | 01 · Director's Canvas |
| User clicked "Timeline" or scene has ≥3 generated shots | 03 · Timeline Editor |
| User clicked "Crew" or has typed ⌘K | 04 · Agent Console |
| User clicked "Graph" or has ≥1 error in audit log | 05 · Node Graph |
| Power user with 10+ projects | default 01, never 02 |

A user is never forced to fight the surface. Switching views is one click.

---

## What's intentionally NOT in these wireframes

These are intentionally **deferred** to the prototype / post-submission roadmap:

- **Consistency Contract UI** — Section 12 of the plan. Visual editor for character/environment anchors. Will live as a panel inside V1 + V4. Not yet wired in any wireframe.
- **Style Token system** — Section 12. Token picker, palette UI. Roadmap Phase 2.
- **Studio Library** — Section 12. Shared brand kits across productions. Roadmap Phase 2.
- **Multi-user collaborative cursors** — Section 23. Real-time sync. Roadmap Phase 3.
- **Mobile companion view** — Section 23. Read/approve on phone. Roadmap Phase 5.

These belong in `docs/wireframes/` once the core 5 views are validated.

---

## Honest caveats

These wireframes are **design-sprint quality**. They prove the structure works. They do not prove:

- That the production document schema can carry the state these views imply — see `docs/architecture/production-document-schema.md` (engineer work).
- That the CLI bridge from `src/demo_flow.py` to a real production state model is feasible — see `docs/architecture/cli-bridge-design.md` (engineer work).
- That real users prefer these defaults — see `docs/research/user-research-plan.md` (PM work, ACT-1).
- That the 26-stage pipeline ordering survives contact with a real video producer — see `docs/research/pipeline-validation-plan.md` (PM work, P0-4).

Wireframes are necessary, not sufficient. The other four docs in this design sprint are what make them shippable.

---

## Validation status

| Hypothesis | How to validate | Status |
|---|---|---|
| 5 views are exhaustive | User research ACT-1 (4 personas) | planned |
| View switching is lossless | CLI bridge spec (ACT-8) → implementation | designed |
| Same engine serves beginner + pro | Same as above | designed |
| Reviewer-as-first-class-agent works | Pipeline validation P0-4 | planned |
| 26-stage pipeline ordering is right | Pipeline validation P0-4 | planned |

---

*Generated as part of ACT-3 · Director's Canvas wireframe design sprint · 2026-07-27*