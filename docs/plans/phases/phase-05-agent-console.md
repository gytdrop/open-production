# Phase 5 — Agent Console View

**Category:** View 2 of 2  
**Depends on:** Phase 3  
**Can run in parallel with:** Phase 4  
**Unlocks:** Phase 6 (after Phase 4 also done)

---

## Goal

Build every component in the Agent Console view as a pixel-faithful React implementation of `docs/wireframes/04-agent-console.svg`. Uses static/mock data in this phase — live API wiring happens in Phase 6.

---

## File structure produced

```
web/src/views/AgentConsole/
├── index.tsx                  ← route /console — 3-col layout + fixed status bar
├── CrewRail.tsx               ← 220px fixed left — 12 agents, status dots
├── ConversationThread.tsx     ← center scroll area — assembles message blocks
├── SystemEvent.tsx            ← green dot + bold SYSTEM label + detail + ts
├── AgentMessage.tsx           ← avatar + agent name + ts + bubble
├── OptionCards.tsx            ← 3 A/B/C cards inside Creative Director bubble
├── UserMessage.tsx            ← green-tinted "YOU" reply bubble
├── ThinkingBubble.tsx         ← animated 3 cyan dots + muted status text
├── ReviewerFlag.tsx           ← pink border, ⚠ heading, action buttons
├── ShotStrip.tsx              ← bottom shot timeline: S01–S06 coloured blocks
├── CommandBar.tsx             ← ⎈ prefix + placeholder input + Send button
└── ContextRail.tsx            ← 460px fixed right — shot details, events, branches
```

---

## Layout (from `04-agent-console.svg`)

```
┌──[220px CrewRail]──┬──────────────────[center: ConversationThread]──────────────────┬──[460px ContextRail]──┐
│                    │                                                                  │                       │
│  CREW    8/12      │  CONVERSATION                              filter ▾ all agents  │  CONTEXT              │
│                    │                                                                  │                       │
│  [CD] Creative…    │  ● SYSTEM  ✓ Shot 7 generation complete · 12.4s · review…       │  Shot 7 · Close-up    │
│  [PR] Producer     │                                                                  │  Scene 3 · 2.1s…      │
│  [SB] Storyboard…  │  [CD] Creative Director          14:22:31 · 3 options            │                       │
│  [SD] Shot Des… ⚡ │  ┌──────────────────────────────────────────────────────────┐   │  RECENT EVENTS        │
│  [CH] Character…   │  │ The current shot reads… 3 framings:                      │   │  14:22:08 system…     │
│  [EA] Env Artist   │  │  [A·Tighter] [B·Lower angle] [C·Split comp.]             │   │  14:22:31 CD…         │
│  [ED] Editor       │  └──────────────────────────────────────────────────────────┘   │                       │
│  [CO] Colorist     │                                                                  │  BRANCHES             │
│  [RV] Reviewer ⚠  │  [YOU]  Approve B. But can height be 1.0m…                      │  [main●] [dark-cut]   │
│  ─────             │                                                                  │                       │
│  [VD] standby      │  [SD] Shot Designer            thinking… ⚡                     │  LOCKED DECISIONS     │
│  [MC] standby      │  ┌──────────────────────────────────────────────────────────┐   │  ✓ mood · palette     │
│  [SN] standby      │  │  ●●● Resolving camera spec for option B…                 │   │  ✓ temperature 3200K  │
│                    │  └──────────────────────────────────────────────────────────┘   │                       │
│  + show 4 inactive │                                                                  │                       │
│                    │  [RV] Reviewer                   14:23:48 · 1 finding            │                       │
│                    │  ┌──────────────────────────────────────────────────────────┐   │                       │
│                    │  │  ⚠ Character expression diverges from anchor             │   │                       │
│                    │  │  S07_03 is 0.34 cosine-similarity off from protagonist…  │   │                       │
│                    │  └──────────────────────────────────────────────────────────┘   │                       │
│                    │  ──────────────────────────────────────────────────────────────  │                       │
│                    │  [S01✓][S02✓][S03✓][S04✓][S05▶][S06⚠]       ⌘K command palette │                       │
│                    │  ⎈ Ask the crew anything — type ⌘K…                 [Send]       │                       │
└────────────────────┴──────────────────────────────────────────────────────────────────┴───────────────────────┘
[ STAGE 16/26 · review ] [ CREW  8 ready · 1 thinking ] [ REVIEWER 1 finding ] [ BRANCHES main+2 ] [ AUDIT 249 ]
```

---

## Component specifications

### `CrewRail.tsx`

Width: `220px`, fixed left, `overflow-y: auto`, `background: rgba(0,0,0,0.4)`.

Header: `CREW` (10px bold #a78bfa) + `8 / 12 ACTIVE` (9px #5d6678) right-aligned.

**All 12 agents** to render (from SVG lines 22–92):

| Agent | Initials | Dot colour | Default state |
|---|---|---|---|
| Creative Director | CD | green | active (selected) |
| Producer | PR | green | idle |
| Storyboard Artist | SB | green | idle |
| Shot Designer | SD | amber | thinking |
| Character Director | CH | green | idle |
| Environment Artist | EA | green | idle |
| Editor | ED | green | idle |
| Colorist | CO | green | idle |
| Reviewer | RV | green | flagged (pink row) |
| Voice Director | VD | gray | standby (dim) |
| Music Composer | MC | gray | standby (dim) |
| Sound Designer | SN | gray | standby (dim) |

Per-agent row spec:
- Avatar: `width:26px height:26px border-radius:50%` + status dot (8px, bottom-right, border 1.5px solid bg)
- Agent name: `font-size:11px font-weight:600 color:#e4e7eb`
- Status text: `font-size:10px color:#8a93a6` (thinking=amber, flagged=pink, ready=green)
- Row states: `active`=blue tint+border, `thinking`=amber tint+border, `flagged`=pink tint+border, `standby`=opacity:.45

Clicking a row: sets store `selectedActor` (used in Phase 6 for thread filtering).

Footer: `+ show 4 inactive` in italic `#5d6678`.

---

### `ConversationThread.tsx`

`flex:1`, `overflow-y:auto`, assembled in order from top:
1. `<SystemEvent />` — generation complete
2. `<AgentMessage agent="Creative Director" />` containing `<OptionCards />`
3. `<UserMessage />` — "Approve B…"
4. `<AgentMessage agent="Shot Designer" thinking />` containing `<ThinkingBubble />`
5. `<AgentMessage agent="Reviewer" />` containing `<ReviewerFlag />`

Top bar: `CONVERSATION` label left + `filter ▾ all agents` right.

---

### `OptionCards.tsx`

3-column grid inside the Creative Director bubble (from SVG lines 122–143):

| Card | Letter | Title | Body |
|---|---|---|---|
| A | `A · Tighter` | `85 → 110mm, same angle.` | `Squeezes background. Less cue, more face.` |
| B | `B · Lower angle` | `Camera 1.2m high, subject looms.` | `Stairs silhouettes in BG.` |
| C | `C · Split comp.` | `Doorway in 4th-left, actor off-center right.` | `Implies choice.` |

Each card: thumbnail placeholder (`height:40px bg:rgba(255,255,255,.025)`) + letter + title + body.  
Selected: `border-color: #6b8eff; background: rgba(107,142,255,.1)`.  
Clicking toggles selection (visual only in P5).

---

### `ReviewerFlag.tsx`

Background: `rgba(244,114,182,.06)`, border: `1px solid #f472b6`, border-radius: 6px.

```
⚠ Character expression diverges from anchor        ← #f472b6 bold
Generated S07_03 is 0.34 cosine-similarity off from protagonist.v1 anchor.
Suggest re-generating or accepting with override annotation.
(Audit trail will record either choice.)            ← dim italic

[Re-generate]  [Accept + Override]                 ← action buttons
```

Clicking **Re-generate**: button text changes to "✓ Re-generating…", opacity dims.  
Clicking **Accept + Override**: row fades to dim + adds override annotation text.

---

### `ShotStrip.tsx`

Fixed at bottom of center column, `border-top: 1px solid #2d3340`, `background: rgba(0,0,0,.5)`.

Label: `SHOTS · SCENE 3` (10px bold #a78bfa).

Shot blocks (from SVG lines 248–261):
| Block | Colour | Label |
|---|---|---|
| S01 | `rgba(34,197,94,.4)` | S01 ✓ |
| S02 | `rgba(34,197,94,.4)` | S02 ✓ |
| S03 | `rgba(34,197,94,.4)` | S03 ✓ |
| S04 | `rgba(34,197,94,.4)` | S04 ✓ |
| S05 | `rgba(107,142,255,.5)` + 2px accent border | S05 ▶ thinking |
| S06 | `rgba(251,191,36,.4)` | S06 ⚠ |

Right side: `⌘K command palette` label (purple bold) + sub-text.

---

### `CommandBar.tsx`

```
┌──────────────────────────────────────────────────────────────────[border:accent]──────┐
│  ⎈  Ask the crew anything — type ⌘K for commands…                           [Send]    │
└────────────────────────────────────────────────────────────────────────────────────────┘
Try: "ask review to recheck S07" · "branch the cut darker" · "lock shot 7"
```

Border: `1px solid rgba(107,142,255,.3)`, background: `rgba(255,255,255,.04)`.  
Hint text: 10px italic `#5d6678` below the bar.  
Send button: `background: #6b8eff; color: #0f1117; font-weight: 700`.

---

### `ContextRail.tsx`

Width: `460px`, fixed right, `overflow-y: auto`, `background: rgba(0,0,0,.4)`.

Sections (from SVG lines 188–242):

**CONTEXT** header + shot details:
```
Shot 7 · Close-up             ← 13px font-weight:600
Scene 3 · 2.1s · 85mm · 3200K ← 11px muted
```

**RECENT EVENTS** — 5 rows, each `(timestamp, message)`:
```
14:22:08   system · generation done
             — shot_7_v3.jsonl          ← 9px dim indent
14:22:31   CD · 3 framings proposed
14:23:14   user · approve B (height 1.0m)
14:23:21   SD · reading production state…
14:23:48   RV · flagged: expression drift
— 247 events total in this production   ← 9px dim
```

**BRANCHES** — chip row:
```
[main · neutral ●]  [dark-cut]  [warm-amber]  [+ start new from here]
```
Active chip: `rgba(167,139,250,.18)` border purple.

**LOCKED DECISIONS** — 4 rows:
```
✓  mood · 90s thriller palette
✓  temperature · 3200K
✓  protagonist anchor · v1 (drift -0.02)
—  director's framing · in proposal       ← muted
```

---

### Status bar (fixed bottom, 40px)

`position:fixed; bottom:0; left:0; right:0; height:40px; background:rgba(0,0,0,.55); border-top:#2d3340`

5 cells from SVG lines 266–278:

| Cell | Label | Value | Colour |
|---|---|---|---|
| 1 | STAGE | 16 / 26 · review | #e4e7eb |
| 2 | CREW | 8 ready · 1 thinking | #22c55e |
| 3 | REVIEWER | 1 finding · 0 override | #f472b6 |
| 4 | BRANCHES | main + 2 · 1 in progress | #e4e7eb |
| 5 | AUDIT EVENTS | 249 lines | #e4e7eb |

---

## Acceptance criteria

| Check | Expected |
|---|---|
| Layout matches `04-agent-console.svg` | 3-col: 220px / flex / 460px, 40px status bar |
| CrewRail renders all 12 agents | Correct initials, dots, status text, row colours |
| Creative Director bubble shows 3 option cards | A/B/C layout, thumbnail placeholders |
| Clicking an option card | Highlights with accent border |
| ReviewerFlag renders | Pink border, ⚠ heading, 2 action buttons |
| Re-generate button click | Button dims, text changes to "✓ Re-generating…" |
| Shot strip | S01–S06 blocks with correct colours |
| Status bar | 5 cells visible with correct labels and mock values |
| `npm run typecheck` | 0 errors |
