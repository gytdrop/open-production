# Phase 4 — Guided Production Flow View

**Category:** View 1 of 2  
**Depends on:** Phase 3  
**Can run in parallel with:** Phase 5  
**Unlocks:** Phase 6 (after Phase 5 also done)

---

## Goal

Build every component in the Guided Production Flow view as a pixel-faithful React implementation of `docs/wireframes/02-guided-flow.svg`. Uses static/mock data in this phase — live API wiring happens in Phase 6.

---

## File structure produced

```
web/src/views/ProductionFlow/
├── index.tsx                  ← route /flow — assembles all sub-components
├── StepIndicator.tsx          ← 7 progress dots: Idea·Ref·Mood·Cast·Plan·Gen·Pub
├── IntentForm.tsx             ← textarea + platform pills + tone buttons + CTA
├── AngleCards.tsx             ← 3 cards: Skeptic·Advocate·Contrarian
├── ResultPanel.tsx            ← gate counts + production_id chip + audit download
└── PipelineWizard.tsx         ← 26-stage grid, done/active/future tiles
```

---

## Layout (from `02-guided-flow.svg`)

```
┌──[60px left rail]──────────────────────────────[max-720px wizard col]────────────────[280px helper]──┐
│                   │                                                              │                    │
│  🎬 Studio        │  STEP 1 OF 7  ● ─── ○ ─── ○ ─── ○ ─── ○ ─── ○ ─── ○       │  💡 Tip            │
│                   │                                                              │  card (purple)     │
│  ⊞ Flow           │  What story do you want to tell?                            │                    │
│                   │  A few sentences is fine — we'll help you develop it.        │                    │
│                   │  ┌─────────────────────────────────────────────────────┐    │                    │
│                   │  │  textarea (min-h:130px)                             │    │                    │
│                   │  └─────────────────────────────────────────────────────┘    │                    │
│                   │  37 / 500                                                    │                    │
│                   │  WHERE WILL IT LIVE?                                        │                    │
│                   │  [TikTok●] [Instagram] [YouTube] [Other]                   │                    │
│                   │  WHAT TONE?                                                 │                    │
│                   │  [Warm] [Neutral●] [Tense] [Hopeful]                        │                    │
│                   │  I have a script — paste it instead          [Continue →]   │                    │
└───────────────────┴─────────────────────────────────────────────────────────────┴────────────────────┘
```

---

## Component specifications

### `StepIndicator.tsx`

- 7 dots connected by lines
- Label below each: Idea · Ref · Mood · Cast · Plan · Gen · Pub
- Dot states driven by store `flowStep` (1–7):
  - `done`: filled accent colour + ✓, connecting line turns accent
  - `active`: accent border + glow ring `box-shadow: 0 0 0 6px rgba(107,142,255,.15)`
  - `future`: dim border, dim number
- "STEP X OF 7" label above row

### `IntentForm.tsx`

| Element | Spec | From SVG |
|---|---|---|
| Textarea | `min-height: 130px`, `border: 1px solid #3a4256`, `border-radius: 8px`, placeholder italic | line 41–47 |
| Char counter | Right-aligned `XX / 500` in `#5d6678` | line 50 |
| Platform label | `font-size: 12px; font-weight: 700; color: #a78bfa; letter-spacing: .06em` | line 53 |
| Platform pills | `border-radius: 20px; padding: 10px 24px`, selected = blue fill + border | line 54–61 |
| Tone label | Same style as platform label | line 64 |
| Tone buttons | `border-radius: 6px; padding: 8px 20px`, selected = blue fill | line 65–72 |
| Continue → | `background: #6b8eff; color: #0f1117; font-weight: 700; border-radius: 8px` | line 86–88 |
| Script link | `font-size: 12px; color: #6b8eff; text-decoration: underline` | line 90 |

On submit (Phase 4): calls mock `loadAngles()` → sets `flowStep: 2`, shows `AngleCards`.  
On submit (Phase 6): calls real `POST /api/reframe`.

### `AngleCards.tsx`

3 equal-width cards in a CSS grid (`grid-template-columns: repeat(3,1fr)`):

| Card | Badge colour | Button colour |
|---|---|---|
| Skeptic | `rgba(107,142,255,.15)` text `#a7c8ff` | Default blue |
| Advocate | `rgba(34,197,94,.15)` text `#86efac` | Green gradient |
| Contrarian | `rgba(167,139,250,.15)` text `#d4b4fe` | Purple gradient |

Each card contains:
- Badge (top, pill shape)
- Name (bold, 13px)
- Summary body (muted, 11px)
- "Why it matters" label + text
- "Questions to address" bullet list (from `angle.questions_to_address[]`)
- **Use this angle** button (full width)

Selected card: `outline: 2px solid rgba(107,142,255,.4)` + background tint.  
Clicking card or button: calls `finalizeRun(angleId)` → sets `flowStep: 3`, shows `ResultPanel`.

### `ResultPanel.tsx`

```
┌─────────────────────────────────────────────────────────────────────┐
│ Summary sentence (full width, tinted green box)                      │
│                                                                       │
│  [2 accepted]  [1 rejected]  [1 contradiction]  (3 stat tiles)       │
│                                                                       │
│  Production ID: [prod_xxx chip]  [Open in Agent Console →]           │
│  ✓ PublicationGate passed · DOI present · authors attributed          │
│  [Download audit JSON]  [Start over]                                  │
└─────────────────────────────────────────────────────────────────────┘
```

All values from store `runResult` (Phase 4: mock, Phase 6: live).

### `PipelineWizard.tsx`

All 26 pipeline stages with their mapped agent:

| # | Stage | Agent |
|---|---|---|
| 1 | Idea / Intent | IntentDocument |
| 2 | Research | ResearchAgent |
| 3 | References | SHA-256 provenance |
| 4 | Moodboard | MoodboardAgent |
| 5 | Creative Direction | CreativeReframing + ConfirmGate |
| 6 | Story | StoryAgent |
| 7 | Script | ScriptAgent |
| 8 | Characters | CharacterDirectorAgent |
| 9 | Locations | EnvironmentArtistAgent |
| 10 | Shot Planning | ShotPlanningAgent |
| 11 | Storyboard | StoryboardArtistAgent |
| 12 | Timeline | EditorAgent (scene order) |
| 13 | Camera | ShotDesignerAgent |
| 14 | Lighting | ShotDesignerAgent |
| 15 | Assets | AssetLibraryAgent |
| 16 | Generation | GenerationAgent |
| 17 | Editing | EditorAgent |
| 18 | Animation | AnimationDirectorAgent |
| 19 | Voice | VoiceDirectorAgent |
| 20 | Music | MusicComposerAgent |
| 21 | Sound | SoundDesignerAgent |
| 22 | Color | ColoristAgent |
| 23 | Review / QA | ReviewerAgent |
| 24 | Iteration | ProductionService (branch + snapshot) |
| 25 | Publishing | PublisherAgent + PublicationGate |
| 26 | Archive | production.json + audit.jsonl |

Done stages derived from `runResult` fields:
- `research_result.gate_passed` → stage 2
- `env_result.proposals` → stage 9
- `shot_plan_result.shots` → stage 10
- `reviewer_results.length > 0` → stage 23
- `accepted_claims > 0` → stages 1, 5, 25
- `branch_result.branch_id` → stage 24
- `publish_result.proposals` → stage 25

---

## Helper card (`index.tsx` right rail)

Matches SVG lines 75–83:
```
┌─────────────────────────────────────────┐
│ 💡 Tip                                  │
│ You can change anything later —         │
│ the production doc keeps every version. │
│ ─────────────────────────────────────── │
│ Skip ahead any time from Studio menu.   │
│                                         │
│ No saves to manage.        (italic dim) │
└─────────────────────────────────────────┘
```
Border: `1px solid #a78bfa`, background: `rgba(167,139,250,.08)`

---

## "WHAT HAPPENS NEXT" footer box

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ WHAT HAPPENS NEXT                                                                                        │
│ After you continue, the system suggests 3 creative angles for your idea. You pick one.                  │
│ Then references. Then mood. You can change any later.                                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
Hides after angle panel appears.

---

## Acceptance criteria

| Check | Expected |
|---|---|
| Page matches `02-guided-flow.svg` | 60px left rail, wizard col, helper card, step dots |
| Textarea, pills, tone buttons render | Correct colours + selected states |
| Continue → button | Shows angle cards, step 1→2 animates |
| Picking an angle | Shows result panel, step 2→3 animates |
| ResultPanel stat tiles | Accept/reject/contradiction counts visible |
| PipelineWizard renders | 26 tiles with done/active/future states |
| `npm run typecheck` | 0 errors |
