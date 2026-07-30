# Guided Flow v2 — 7-Stage Wireframes

> **Replaces:** `02-guided-flow.svg` (ACT-3, 2026-07-27)
> **Status:** Design sprint v2 — awaiting review
> **Owner:** Design
> **Persona:** Sam (primary) · Jordan graduating into Director's Canvas

---

## 0. Why a v2

The v1 Guided Flow (`02-guided-flow.svg`) was built on Law 4 ("same engine, fewer knobs") taken to its extreme: **the crew is invisible**. The user sees a single voice — "we'll help you develop it" — and never meets the agents doing the work.

That choice was right for first-time onboarding. It is wrong for the real product. The Five Laws say:
- **Law 3**: Every decision has a reason. The user must see *why*.
- **Law 5**: AI earns autonomy incrementally. Hiding the AI prevents it from earning trust.

v2 keeps Sam's friendliness but **surfaces the crew at the right depth** — a thin Crew Activity strip, inline "Why this?" on every AI value, and a persistent audit-trail link. Power users (Jordan) get the same wireframes; the crew strip expands on demand.

This document is the detailed spec. The accompanying `02-guided-flow-v2.svg` (to be rendered from this) is the visual artifact.

---

## 1. The 7 Stages — Names & Rationale

The v1 stage names were truncated (`Ref`, `Gen`, `Pub`) and production-domain-inspecific. The v2 names are full, action-oriented, and read like sentences a real producer would say.

| # | v1 | v2 | User Decision | Output → Next Stage |
|---|----|----|---------------|---------------------|
| 1 | Idea | **State Your Vision** | What story, for whom, on what platform, in what tone | An `IntentDocument` that seeds Stage 2 |
| 2 | Ref | **Pin Your References** | Which references, mood, voice anchors ground the story | A `ReferenceCluster` with SHA-256 provenance |
| 3 | Mood | **Find Your Angle** | Which creative angle (skeptic / advocate / contrarian) frames the story | A `ChosenAngle` that gates Stage 4 |
| 4 | Cast | **Build Your World** | Which characters, locations, and consistency contracts define the universe | A populated `Cast` + `Environment` set |
| 5 | Plan | **Plan the Production** | Which scenes, shots, camera, lighting, storyboard frames execute the angle | A `ShotPlan` + `Storyboard` ready for generation |
| 6 | Gen | **Generate & Polish** | Run the crew, review each pass, iterate | Approved, gated artifacts (frames, voice, music, edit) |
| 7 | Pub | **Publish with Evidence** | Lock the cut, pass final gate, archive, publish | A `PUBLISHED` production + audit trail |

**Why these names:**
- Each verb is concrete: state, pin, find, build, plan, generate, publish.
- Each name is **production-domain**, not engineering-domain — no "intent declaration," no "orchestration graph."
- Each name **hints at the crew's work** without naming agents: "Find Your Angle" implies the creative reframing step; "Generate & Polish" implies the entire agent crew + Reviewer.
- The last stage — "Publish with Evidence" — is the most powerful differentiator: publishing is not "upload a video," it is "publish with an audit trail."

---

## 2. Agent Collaboration Blueprint

### 2.1 The Crew Pattern

Open Production runs a **bounded-crew pattern**, not a single assistant. Three roles recur across every stage:

- **Lead agent** — owns the primary decision at this stage. Owns the artifact.
- **Supporting agents** — contribute inputs (research, references, specs, gates).
- **Reviewer agent** — runs on every artifact. Never owns; only validates. Its verdict is *always visible*.

Plus one cross-cutting process:
- **ConfirmGate** — sits between stages. A human-approval gate, not an AI gate. Prevents stage advance without explicit user OK.

### 2.2 Crew-at-a-Stage Table

| Stage | Lead Agent | Supporting Agents | Reviewer | ConfirmGate |
|-------|-----------|-------------------|----------|-------------|
| 1. State Your Vision | (User) | ResearchAgent (passive background) | — | soft |
| 2. Pin Your References | ReferenceClusteringAgent | ResearchAgent, MoodboardAgent (queued) | Reviewer (provenance check) | soft |
| 3. Find Your Angle | CreativeReframingAgent | ConfirmGate (angle validity) | Reviewer (consistency vs. brief) | **hard** |
| 4. Build Your World | CharacterDirectorAgent · EnvironmentArtistAgent | MoodboardAgent, AssetLibraryAgent | Reviewer (consistency contract) | soft |
| 5. Plan the Production | ShotPlanningAgent | StoryAgent, ScriptAgent, ShotDesignerAgent, StoryboardArtistAgent | Reviewer (plan feasibility) | soft |
| 6. Generate & Polish | GenerationAgent | AnimationDirector, VoiceDirector, MusicComposer, SoundDesigner, Colorist, Editor | Reviewer (every artifact) | **hard** between passes |
| 7. Publish with Evidence | PublisherAgent | All agents (final sign-off) | Reviewer (final QA) | **hard** (final lock) |

**ConfirmGate hardness:**
- **soft** = user can skip with "I know what I'm doing" (Jordan pattern)
- **hard** = user cannot skip; must explicitly approve or reject (Stage 3 angle, Stage 6 per-pass, Stage 7 publication)

### 2.3 Loop

```
            ┌──────────────────────────────────────────┐
            │                                          │
            ▼                                          │
        ┌───────┐    plan    ┌────────────────┐        │
        │ User  │ ─────────► │ Orchestrator   │        │
        └───────┘            │ (per-stage lead│        │
            ▲                │  agent)        │        │
            │                └───────┬────────┘        │
            │ reflect                │ dispatch        │
            │                        ▼                 │
            │                ┌────────────────┐        │
            │                │ Specialists    │        │
            │                │ (supporting    │        │
            │                │  agents)       │        │
            │                └───────┬────────┘        │
            │                        │ produce        │
            │                        ▼                 │
            │                ┌────────────────┐        │
            └────────────────│ Reviewer       │────────┘
              accepted/      │ (validate      │ rejected →
              reflected       │  every output) │
                              └────────────────┘
```

This loop runs inside every stage. The user only sees the inputs (`plan`) and outputs (`reflect`); the inside is the Crew Activity strip.

---

## 3. Cross-Stage Shell

The wireframes below all share the same chrome. Changes happen in the **canvas** (the main center panel) and the **right rail**. The **header**, **left rail**, **crew strip**, and **footer** are persistent.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                                  │
│  ┌──────┐                                                                │
│  │ Logo │  Open Production · Guided Flow · <Stage Name>   [View] [User]  │
│  └──────┘                                                                │
├──────┬──────────────────────────────────────────────────┬───────────────┤
│ LEFT │  CANVAS                                          │  RIGHT RAIL   │
│ RAIL │                                                  │               │
│      │  <Stage-specific content here>                   │  Stage Help   │
│ 🏠   │                                                  │  · Tip card   │
│ 🎬   │  (see per-stage wireframes below)                │  · Glossary   │
│ ⌘K   │                                                  │  · "Why this?" │
│      │                                                  │               │
├──────┴──────────────────────────────────────────────────┴───────────────┤
│  CREW ACTIVITY STRIP                                                     │
│  ◐ ResearchAgent thinking…  ◑ CreativeReframing idle  ● Reviewer ready  │
├─────────────────────────────────────────────────────────────────────────┤
│  FOOTER  [← Back]  ● ● ◉ ○ ○ ○ ○   Stage 3 of 7 · Find Your Angle  [→] │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Header (60 px)
- Logo (left), production name + stage name (center), View-switch + User menu (right).
- The View-switch dropdown exposes the 5 views (Guided / Canvas / Timeline / Console / Graph). Default is Guided.

### 3.2 Left Rail (60 px collapsed, 200 px expanded)
- Studio icon, production icon, ⌘K command palette.
- Expand on hover → shows labels (Studio, Productions, Command).
- Power-user only: skip-on-click to Director's Canvas.

### 3.3 Canvas (flex)
- Per-stage content. Always one primary action visible above the fold.
- A persistent "What happens next" footer inside the canvas (collapsed in expert mode).

### 3.4 Right Rail (300 px, collapsible)
- Default: Tip card with stage-specific guidance.
- Toggle to: Glossary, Audit Trail, "Why this?" panel, Crew Detail.

### 3.5 Crew Activity Strip (40 px, persistent)
- Horizontal strip showing all active agents with status dots.
- Status dot colors: green (ready), amber (thinking), purple (proposing), magenta (Reviewer flagging), gray (idle).
- Click an agent → opens its scope contract + recent decisions in the right rail.
- **This is the single most important addition vs. v1.** It makes the crew visible without making it the focus.

### 3.6 Footer Progress (60 px, persistent)
- Back button (left), 7-stage progress dots (center), Next button (right).
- Progress dots show: done (filled), active (pulse), future (outline). Hover → stage name.
- Click any done dot → jump back without losing work.

### 3.7 Persistence
- Every keystroke / selection writes to `production.json` via the existing `ProductionService.save()` (thread-safe, single-process).
- "Draft autosaved 3 seconds ago" appears in the footer on idle.
- A "Draft" badge on the header shows the current `ProductionState` (`DRAFT` → `BRIEFED` → `IN_PRODUCTION` → `IN_REVIEW` → `APPROVED` → `PUBLISHED`).

---

## 4. Per-Stage Wireframes

### Stage 1 · State Your Vision

**Goal:** Capture what story, for whom, on what platform, in what tone.
**Lead:** (User). **Supporting:** ResearchAgent (passive). **ConfirmGate:** soft.

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · State Your Vision      [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       What story do you want to tell?                |  Studio Tip     |
|       A few sentences is fine.                       |  -------------  |
|                                                      |  You can change  |
|  +------------------------------------------------+  |  anything later.|
|  | e.g. A short film about a barista who          |  |  The production |
|  | discovers their regular customer is an AI...   |  |  doc keeps every |
|  |                                                |  |  version.        |
|  | A young filmmaker wonders if AI can replace    |  |                  |
|  | _                                       |      |  |  Why this?     |
|  +------------------------------------------------+  |  -------------  |
|  37 / 500                                            |  ResearchAgent   |
|                                                      |  is already scan-|
|  WHERE WILL IT LIVE?                                 |  ning for prior  |
|  [TikTok *] [Instagram o] [YouTube o] [Other o]     |  work on this    |
|                                                      |  topic. Findings |
|  WHAT TONE?                                          |  appear in Stage 2|
|  [Warm o] [Neutral *] [Tense o] [Hopeful o]          |  automatically.  |
|                                                      |                  |
|  [ I have a script - paste it instead ]              |  Glossary        |
|                                                      |  Intent, Topic,  |
|                                              [Continue ->]              |
+------------------------------------------------------+----------------+
|  CREW STRIP  * ResearchAgent scanning  o ReferenceCluster idle  * Reviewer ready |
+------------------------------------------------------------------------------+
|  [< Back (disabled)]   * o o o o o o   Stage 1 of 7 . State Your Vision  [->] |
|                                                                                |
|  WHAT HAPPENS NEXT  -> After you continue, the system suggests 3 creative      |
|  angles. You pick one. Then references. Then mood.                             |
+--------------------------------------------------------------------------------+
```

**Components:**
- Centered headline (h1, 26 px) + sub-headline (muted, 13 px)
- Textarea (focus state: accent border; blur: border2)
- Char counter (bottom-right, amber when > 90%)
- Platform pills (radio, single-select)
- Tone buttons (radio, single-select)
- "I have a script" link (alternative entry)
- Continue button (primary CTA, gradient, disabled until topic non-empty)
- "Why this?" panel hint that ResearchAgent is running

**Progressive depth:**
- **Overview (default Sam):** As above.
- **Standard:** Add audience field, duration_sec field, and a "Style seed" link to past projects.
- **Expert (Jordan):** Add raw `IntentDocument` JSON view, style_seed generator, custom tone vocabulary.

**Hand-off:** `IntentDocument` is committed; ResearchAgent scans asynchronously; the user moves to Stage 2. The Crew Strip shows ResearchAgent moving from "scanning" to "found 4 prior projects on this topic."

---

### Stage 2 · Pin Your References

**Goal:** Ground the story in references — images, videos, audio, prior cuts, anything that anchors the creative.
**Lead:** ReferenceClusteringAgent. **Supporting:** ResearchAgent (provides findings), MoodboardAgent (queued). **Reviewer:** provenance check. **ConfirmGate:** soft.

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · Pin Your References  [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       What should the audience feel?                |  Tip            |
|       Drop references that anchor the tone.         |  -------------  |
|                                                      |  Each reference  |
|  +----------+----------+----------+----------+      |  gets a SHA-256 |
|  |          |          |          |          |      |  hash. Nothing   |
|  |  + ADD   |  [img]   |  [vid]   |  [img]   |      |  is ever lost.   |
|  |          |          |          |          |      |                  |
|  |  image   | mood-1   | cut-04   | color-2  |      |  Stats          |
|  |  video   |          |          |          |      |  3 references   |
|  |  audio   |          |          |          |      |  2 sources cited|
|  |  url     |          |          |          |      |                  |
|  +----------+----------+----------+----------+      |  Why this?      |
|                                                      |  -------------  |
|  FOUND WHILE YOU WORKED:                             |  ResearchAgent   |
|  +------------------------------------------------+  |  found 4 prior   |
|  | doc "AI in coffee shops" - 2025 ACM paper      |  |  projects + 7    |
|  | doc "Cafe culture" - ethnographic study        |  |  papers on this  |
|  | doc "Reframing the Turing Test" - Wired 2024   |  |  topic. They     |
|  +------------------------------------------------+  |  appear below.   |
|                                                      |                  |
|                                  [< Back]  [Continue ->]                |
+------------------------------------------------------+----------------+
|  CREW STRIP  ok ResearchAgent done (4 found)  o ReferenceCluster working  * Reviewer checking provenance |
+------------------------------------------------------------------------------+
|  [< Back]   * * o o o o o   Stage 2 of 7 . Pin Your References  [->]      |
|  Draft autosaved 3s ago . State: BRIEFED                                   |
+--------------------------------------------------------------------------------+
```

**Components:**
- Add-reference tiles (drag-and-drop + click-to-pick) for 4 kinds: image, video, audio, url
- Reference cards (thumbnail + label + provenance hash on hover)
- "Found while you worked" section — async outputs from ResearchAgent land here
- Stats panel in right rail (count, sources)
- Continue / Back

**Progressive depth:**
- **Overview:** Drop and continue.
- **Standard:** Add a "why this reference" caption per pin.
- **Expert:** Direct upload to local `references/` with custom provenance metadata.

**Hand-off:** `ReferenceCluster` is locked with SHA-256 hashes. MoodboardAgent starts working in the background; the user moves to Stage 3. ProductionState transitions `DRAFT` -> `BRIEFED`.

---

### Stage 3 · Find Your Angle

**Goal:** Choose the creative angle. The single most consequential creative decision.
**Lead:** CreativeReframingAgent. **Supporting:** ConfirmGate (validates the chosen angle against the brief). **Reviewer:** consistency vs. brief. **ConfirmGate:** **HARD**.

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · Find Your Angle     [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       Three angles on your story.                   |  Tip            |
|       Pick the one that fits - or remix.            |  -------------  |
|                                                      |  The Reviewer has|
|  +-------------+ +-------------+ +-------------+   |  already scored  |
|  | SKEPTIC     | | ADVOCATE    | | CONTRARIAN  |   |  each angle for  |
|  |             | |             | |             |   |  fit with your   |
|  | "AI cannot  | | "AI can     | | "AI already |   |  brief. Hover    |
|  |  replace    | |  co-create  | |  creates    |   |  any angle to    |
|  |  human      | |  with hu-   | |  - the      |   |  see the score.  |
|  |  warmth"    | |  mans"      | |  question   |   |                  |
|  |             | |             | |  is what    |   |  Fit Score      |
|  | tone: cool  | | tone: warm  | |  comes next"|   |  -------------  |
|  | pace: slow  | | pace: med   | | tone: sharp |   |  Sceptic  78/100|
|  | fit: 78/100 | | fit: 82/100 | | fit: 71/100 |   |  Advocate 82/100|
|  |             | |             | |             |   |  Contrar. 71/100|
|  | [Pick this] | | [Pick this] | | [Pick this] |   |                  |
|  +-------------+ +-------------+ +-------------+   |  Why this?      |
|                                                      |  -------------  |
|  Or remix:                                          |  CreativeRefram- |
|  [ Take parts of two angles -> ]                     |  ing produces 3  |
|                                                      |  angles by       |
|  Reviewer verdict:                                   |  sampling tone,  |
|  ok All three pass the brief-fit gate.               |  pace, and fit   |
|                                                      |  from your       |
|                                  [< Back]  [Confirm & Continue ->]     |  references.     |
+------------------------------------------------------+----------------+
|  CREW STRIP  ok CreativeReframing done  * Reviewer checking fit  o ConfirmGate waiting |
+------------------------------------------------------------------------------+
|  [< Back]   * * * o o o o   Stage 3 of 7 . Find Your Angle  [! Confirm required] |
|  Hard gate: you must pick an angle before continuing.                       |
+--------------------------------------------------------------------------------+
```

**Components:**
- 3 angle cards (skeptic / advocate / contrarian), each with:
  - Thematic headline
  - Tone + pace descriptors
  - Reviewer fit-score (small badge)
  - Primary CTA: "Pick this"
- "Or remix" link -> opens an angle-mixing modal
- Reviewer verdict strip (collapsed) — visible because Law 3 says every decision has a reason
- Confirm CTA — disabled until one angle is picked
- Footer warning: "Hard gate" — explicit, calm, no scolding

**Progressive depth:**
- **Overview:** Three cards, one tap to pick.
- **Standard:** Reveals tone, pace, fit-score, and a "Why this angle?" hover.
- **Expert:** Shows the CreativeReframing prompt, sampling distribution, and the option to write a 4th angle from scratch.

**Hand-off:** `ChosenAngle` is locked. ConfirmGate emits a `gate_decision` audit entry. ProductionState transitions `BRIEFED` -> `IN_PRODUCTION`.

---

### Stage 4 · Build Your World

**Goal:** Define the characters, locations, and consistency contracts that make the universe.
**Lead:** CharacterDirectorAgent . EnvironmentArtistAgent. **Supporting:** MoodboardAgent, AssetLibraryAgent. **Reviewer:** consistency contract. **ConfirmGate:** soft.

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · Build Your World   [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       Who's in it? Where does it happen?             |  Tip            |
|                                                      |  -------------  |
|  CHARACTERS                              [ + Add ]   |  Each character  |
|  +--------------+ +--------------+ +--------------+ |  gets a "consist-|
|  | [portrait]   | | [portrait]   | | [portrait]   | |  ency contract": |
|  | Maya         | | Barista      | | Regular      | |  visual anchors  |
|  | (filmmaker)  | | (curious)    | | (mystery AI) | |  the Reviewer    |
|  | age: 28      | | age: 31      | | age: ?       | |  uses to check   |
|  | voice: warm  | | voice: brisk | | voice: synth | |  every generated |
|  | [Edit]       | | [Edit]       | | [Edit]       | |  frame.          |
|  +--------------+ +--------------+ +--------------+ |                  |
|                                                      |  Stats          |
|  LOCATIONS                               [ + Add ]   |  3 characters   |
|  +--------------+ +--------------+                   |  2 locations    |
|  | [mood]       | | [mood]       |                   |  12 visual anchors|
|  | Cafe interior| | Street exter.|                   |                  |
|  | time: dusk   | | time: noon   |                   |  Why this?      |
|  | light: warm  | | light: harsh |                   |  -------------  |
|  | [Edit]       | | [Edit]       |                   |  CharacterDirec- |
|  +--------------+ +--------------+                   |  tor proposes    |
|                                                      |  from your tone  |
|  MOOD PALETTE                                        |  + age + referen-|
|  * * * * *  (warm-amber)                             |  ces.            |
|  [ Lock palette ]                                    |                  |
|                                                      |                  |
|                                  [< Back]  [Continue ->]                |
+------------------------------------------------------+----------------+
|  CREW STRIP  ok CharacterDirector done  ok EnvironmentArtist done  o Moodboard sealing  * Reviewer OK |
+------------------------------------------------------------------------------+
|  [< Back]   * * * * o o o   Stage 4 of 7 . Build Your World  [->]        |
|  Draft autosaved 12s ago . State: IN_PRODUCTION                          |
+--------------------------------------------------------------------------------+
```

**Components:**
- Characters section: 3-character grid with portrait thumbnails + key attributes (age, voice) + edit
- Locations section: 2-tile grid with mood thumbnails + lighting + edit
- Mood palette: 5-swatch palette + "Lock palette" CTA
- Right rail: stats + glossary + "Why this?"

**Progressive depth:**
- **Overview:** Three characters + two locations pre-populated by CharacterDirector. User edits captions.
- **Standard:** Add a 4th character, change voice, attach a reference.
- **Expert:** Edit raw consistency contract JSON, set variance tolerance, override visual anchors.

**Hand-off:** Characters + locations + mood palette are locked with consistency contracts. AssetLibraryAgent indexes them. StoryAgent starts in the background.

---

### Stage 5 · Plan the Production

**Goal:** Define scenes, shots, camera, lighting, storyboard — the production plan.
**Lead:** ShotPlanningAgent. **Supporting:** StoryAgent, ScriptAgent, ShotDesignerAgent, StoryboardArtistAgent. **Reviewer:** plan feasibility. **ConfirmGate:** soft.

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · Plan the Production [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       How will it unfold?                            |  Tip            |
|       The crew drafts scenes + shots + camera.       |  -------------  |
|       You approve or adjust.                         |  The storyboard  |
|                                                      |  is ASCII for    |
|  +---------------------------------------------+     |  now - fine for  |
|  | Scene 01 . "First Encounter"  (00:00-00:30)|     |  planning; the   |
|  |   [s1] [s2] [s3] [s4] [s5]   5 shots        |     |  crew renders    |
|  +---------------------------------------------+     |  real frames at  |
|  | Scene 02 . "The Reveal"        (00:30-01:15)|    |  Stage 6.        |
|  |   [s1] [s2] [s3] [s4]        4 shots         |    |                  |
|  +---------------------------------------------+     |  Stats          |
|  | Scene 03 . "Aftermath"        (01:15-02:00)|     |  3 scenes        |
|  |   [s1] [s2] [s3]             3 shots         |     |  12 shots        |
|  +---------------------------------------------+     |  02:00 total     |
|                                                      |                  |
|  SHOT DETAIL (selected: s2 of Scene 01)             |  Why this?      |
|  +---------------------------------------------+     |  -------------  |
|  | Camera: 35mm, eye-level, dolly-in           |     |  ShotPlanning    |
|  | Lighting: warm key, soft fill, 3200K        |     |  picks framings  |
|  | Audio: voice + ambient cafe + soft music    |     |  to maximize the |
|  | Storyboard: [ASCII frame]                  |     |  chosen angle.   |
|  | [Edit camera] [Edit lighting] [Edit audio]  |     |                  |
|  +---------------------------------------------+     |                  |
|                                                      |                  |
|  [ + Add scene ]  [ + Add shot ]  [ Regenerate plan ]                  |
|                                  [< Back]  [Continue ->]                |
+------------------------------------------------------+----------------+
|  CREW STRIP  ok Story + Script done  * ShotPlanning proposing  o ShotDesigner queued  * Reviewer OK |
+------------------------------------------------------------------------------+
|  [< Back]   * * * * * o o   Stage 5 of 7 . Plan the Production  [->]       |
+--------------------------------------------------------------------------------+
```

**Components:**
- Scene list (accordion: each scene shows shot chips)
- Shot detail panel (selected shot): camera, lighting, audio, storyboard ASCII frame
- Per-field edit CTAs (camera, lighting, audio)
- "Regenerate plan" — power-user escape hatch
- Add scene / add shot buttons

**Progressive depth:**
- **Overview:** View-only, with edit on tap.
- **Standard:** Adjust camera focal length, lighting temp, voice direction inline.
- **Expert:** Show full Shot JSON, override shot count, edit the planning prompt.

**Hand-off:** The `ShotPlan` is locked. The storyboard is ASCII previews; real frames are queued for Stage 6.

---

### Stage 6 · Generate & Polish

**Goal:** Run the crew. Generate frames, voice, music, sound, color, edit. Reviewer validates every artifact.
**Lead:** GenerationAgent. **Supporting:** AnimationDirector, VoiceDirector, MusicComposer, SoundDesigner, Colorist, Editor. **Reviewer:** every artifact. **ConfirmGate:** **HARD** between passes.

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · Generate & Polish  [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       The crew is working.                          |  Tip            |
|       Approve each pass. Override any frame.        |  -------------  |
|                                                      |  The Reviewer    |
|  PASS 1 . FRAMES                       ok Approved  |  checks every    |
|  +-----+-----+-----+-----+ +-------------+         |  generated asset |
|  | s1  | s2  | s3  | s4  | |  [Approve]  |         |  against your    |
|  | ok  | ok  | ok  | ok  | |  [Override] |         |  consistency     |
|  | >   | >   | >   | >   | |  [Re-run]   |         |  contract.       |
|  +-----+-----+-----+-----+ +-------------+         |                  |
|  Reviewer: ok All 5 shots pass consistency gate.    |  Pass log       |
|                                                      |  -------------  |
|  PASS 2 . VOICE + MUSIC                o Running    |  ok Frames      |
|  +------------------------------------+             |  o Voice + Music|
|  | +++++++-  Voice . 72%              |             |  o Sound        |
|  | +++-----  Music . 31%              |             |  o Color        |
|  +------------------------------------+             |  o Edit         |
|                                                      |  o Reviewer     |
|  PASS 3 . SOUND                        o Queued     |                  |
|  PASS 4 . COLOR                        o Queued     |  Why this?      |
|  PASS 5 . EDIT                         o Queued     |                  |
|  PASS 6 . REVIEWER                     o Queued     |  Each pass has   |
|                                                      |  hard ConfirmGat-|
|  [ Skip to next pass (power user) ]                 |  e. Skipping is  |
|                                                      |  OK.             |
|                                  [< Back]  [Run next pass ->]           |
+------------------------------------------------------+----------------+
|  CREW STRIP  * Generation running  o Voice waiting  o Music waiting  * Reviewer queued |
+------------------------------------------------------------------------------+
|  [< Back]   * * * * * * o   Stage 6 of 7 . Generate & Polish  [! Pass gate] |
|  Hard gate between passes - approve or override each.                       |
+--------------------------------------------------------------------------------+
```

**Components:**
- Pass cards (Pass 1, 2, 3...) — each shows status (approved / running / queued / flagged)
- Per-pass artifacts grid (frames with thumb + play + status)
- Per-pass action palette: Approve . Override . Re-run
- Reviewer verdict inline on each pass
- "Skip to next pass" — explicit power-user escape hatch, written, not hidden
- Right rail: pass log + glossary + "Why this?"

**Progressive depth:**
- **Overview:** See approved counts + reviewer verdict per pass; tap into detail.
- **Standard:** Override individual frames with a re-prompt; lock specific frames.
- **Expert:** Edit raw generation prompt, switch backend (runway-gen3 / veo / local), set cost ceilings.

**Hand-off:** When all 6 passes are approved, the cut is locked. ProductionState transitions `IN_PRODUCTION` -> `IN_REVIEW`. Reviewer runs a final QA pass on the assembled cut.

---

### Stage 7 · Publish with Evidence

**Goal:** Lock the cut. Pass the final gate. Archive. Publish.
**Lead:** PublisherAgent. **Supporting:** All agents (final sign-off). **Reviewer:** final QA. **ConfirmGate:** **HARD** (final lock + publish).

```
+- HEADER -------------------------------------------------------------+
|  Open Production · Guided Flow · Publish with Evidence [Viewv] [Sam v] |
+------------------------------------------------------+----------------+
|  CANVAS                                             |  RIGHT RAIL     |
|                                                      |                  |
|       Ready to publish.                              |  Tip            |
|       Three manifest proposals - pick one.          |  -------------  |
|                                                      |  Your audit     |
|  MANIFESTS                                           |  trail travels   |
|  +-------------+ +-------------+ +-------------+    |  with the        |
|  | TikTok cut  | | YouTube cut | | Both + cite |    |  production.     |
|  | 02:00 / 9:16| | 02:00 / 16:9| |  + DOI      |    |  Anyone receiving|
|  |             | |             | |             |    |  the production  |
|  | audience:   | | audience:   | | audience:   |    |  can replay the  |
|  | creators    | | film fans   | | educators   |    |  entire process. |
|  |             | |             | |             |    |                  |
|  | review: ok  | | review: ok  | | review: ok  |    |  Audit summary |
|  | gate: ok    | | gate: ok    | | gate: ok    |    |  -------------  |
|  |             | |             | |             |    |  21 agents ran  |
|  | [ Publish ] | | [ Publish ] | | [ Publish ] |    |  47 decisions   |
|  +-------------+ +-------------+ +-------------+    |  3 gates passed |
|                                                      |  0 contradictions|
|  FINAL GATE                                          |                  |
|  ok Evidence gate: all claims sourced.               |  View full      |
|  ok Consistency gate: visual contract honored.       |  audit trail -> |
|  ok Publication gate: ready for distribution.        |                  |
|                                                      |                  |
|                                  [< Back]  [Confirm & Publish ->]         |
+------------------------------------------------------+----------------+
|  CREW STRIP  * Publisher proposing  * Reviewer final QA  * All agents signed off |
+------------------------------------------------------------------------------+
|  [< Back]   * * * * * * *   Stage 7 of 7 . Publish with Evidence  [! Final lock] |
|  Hard gate - publishing is irreversible for this cut. Snapshots remain.     |
+--------------------------------------------------------------------------------+
```

**Components:**
- 3 manifest proposals (each with audience, format, gate status)
- Final gate panel — three fail-closed gates shown explicitly
- Audit summary in right rail — agent count, decision count, gate pass count
- "View full audit trail" link -> opens the full audit panel
- Confirm & Publish CTA — disabled until a manifest is picked

**Progressive depth:**
- **Overview:** Three manifests, one tap to publish.
- **Standard:** Edit the audience description, change platform, add a DOI / citation.
- **Expert:** Edit the manifest schema, write a custom manifest, override the final gate.

**Hand-off:** Production is published; `production.json` + `audit.jsonl` are archived. ProductionState transitions `APPROVED` -> `PUBLISHED`. The Crew Strip shows all agents at green ("done").

---

## 5. Cross-Stage UX Details

### 5.1 Progress Indicator (Footer)
- 7 dots, semantic colors: done (filled), active (pulse + glow), future (outline).
- Click any *done* dot to jump back. Click the active dot -> no-op. Click a future dot -> confirm modal ("Skip ahead? You'll lose AI suggestions for the skipped stages.").
- Active step shows a soft glow ring matching the stage's accent color.
- Label under dots shows current stage name (changes on hover/active).

### 5.2 Navigation
- **Back:** always available (except Stage 1, where it's disabled). Back preserves all draft state.
- **Next:** available when stage is satisfied. For hard-gate stages (3, 6, 7), it's disabled until the gate is satisfied — the footer shows why.
- **Skip:** available for soft-gate stages via a small "I know what I'm doing" link, expanded into a confirm modal.
- **Keyboard:** `Left` / `Right` to navigate; `Ctrl+K` opens command palette; `Esc` closes modals.

### 5.3 Persistence
- Every change writes to `production.json` via `ProductionService.save()` (already thread-safe, single-process).
- "Draft autosaved Xs ago" indicator in footer.
- A "Draft" badge in header shows `ProductionState` (`DRAFT` -> `BRIEFED` -> `IN_PRODUCTION` -> `IN_REVIEW` -> `APPROVED` -> `PUBLISHED`).
- Refresh-safe: navigating away or closing the tab loses nothing. Reopening resumes at the last stage.
- "Snapshot" link (power user) -> creates a named, content-addressed `VersionSnapshot`. Diffable.

### 5.4 Help
- Right rail has three tabs: Tip (default), Glossary, Audit Trail.
- Glossary entries are stage-scoped — Stage 3 surfaces "skeptic / advocate / contrarian"; Stage 5 surfaces "focal length / aperture / color temp."
- "Why this?" appears next to every AI-generated value. Click -> shows the agent, the prompt, the audit entry.
- A persistent "?" in the header -> opens a tour / shortcuts cheat sheet.

### 5.5 Accessibility
- Full keyboard navigation.
- ARIA labels on all interactive elements; the Crew Activity strip announces agent changes via `aria-live="polite"`.
- Color is never the sole carrier of meaning — every status dot has a text label.
- Reduced-motion mode disables pulse animations on progress dots.
- Minimum contrast 4.5:1; verified against the dark surface (`#0f1117`).

---

## 6. Design Principles (the three I'm betting on)

### Principle 1 . Crew-on-Stage Visibility
The 21-agent crew is the product's core differentiator. v1 hid it; v2 makes it **visible but bounded**. The Crew Activity strip is always present but compact (40 px); agent details open on demand. The principle: *users see who's working, what they're doing, and why their decision matters — without becoming crew managers.*

**Rationale:** Law 3 ("every decision has a reason") and Law 5 ("AI earns autonomy incrementally") require visibility. Hiding the crew hides the differentiator.

### Principle 2 . Progressive Depth by Default
Every feature has three depths: overview (Sam), standard (intermediate), expert (Jordan). The three are **not separate modes** — they are the same feature, revealed progressively. The default Sam view is minimal; an "Advanced" toggle or a Ctrl+K shortcut opens the standard / expert layer without leaving the stage.

**Rationale:** Law 4 ("same engine, different views") is the strongest claim in the principles doc. Progressive depth is how we honor it without forcing Sam to learn the Director's Canvas before she needs it.

### Principle 3 . Decision-Locked, Not Generation-Locked
Hard gates exist at *decision moments*, not at generation moments. Stage 3 (angle), Stage 6 (per-pass), Stage 7 (publish) are hard. Everything else is soft — user can advance without explicit approval.

**Rationale:** Law 1 ("generation is a service call, not a product") says generation should be the *slowest, most expensive* step. Hard-gating decisions (where the user actually makes a creative call) preserves that. Hard-gating generation would create friction with no creative benefit.

---

## 7. Open Questions & Risks

Things I'd want you to resolve before moving to high-fidelity mocks.

| # | Question | Why it matters | Suggested decision |
|---|----------|----------------|--------------------|
| 1 | Crew Strip width: 40 px (iconic) vs 60 px (icon + label)? | Affects whether Sam feels crewed-on or not. | 40 px; expand on hover. |
| 2 | Hard-gate at Stage 6: per-pass vs once at end? | Affects iteration speed. | Per-pass; it's the user's creative review loop. |
| 3 | "Skip ahead" affordance: confirm modal or direct jump? | Affects power-user friction. | Confirm modal with "what you'll lose" preview. |
| 4 | ResearchAgent activity in Stage 1: visible or hidden? | Affects whether Stage 1 feels single-decision or multi-agent. | Visible (already in wireframe); it sets the "crew is here" tone. |
| 5 | ASCII storyboard in Stage 5 vs lazy-rendered thumbs? | The existing StoryboardArtistAgent outputs ASCII. Real frames come in Stage 6. | Keep ASCII in Stage 5; Stage 6 renders real frames. |
| 6 | "I have a script" entry: still a single link or full alternative flow? | Some users arrive with material. | Keep as link in Stage 1; expands a textarea + skips Stage 3. |
| 7 | Audit Trail in right rail: tab vs separate panel? | Affects scanability of the stage. | Tab in right rail; full panel opens via header link. |
| 8 | Mobile responsiveness: do all 7 stages need mobile? | Sam's persona is desktop-first, but Alex might check on iPad. | Desktop-first; mobile gets a read-only "progress + share" view. |
| 9 | Brand kit injection: when in the flow does it apply? | Currently TBD in principles. | Stage 1 (intent) — pulls in studio defaults; overridable in Stage 4 (palette). |
| 10 | Multi-user collaboration: out of scope? | Roadmap Phase 3. | Out of scope for this v2. |

---

## 8. Honest Caveats

- **The Crew Strip is the riskiest piece.** If it feels busy, we should kill it and put agent activity inside the right rail. Test with Sam before locking.
- **The 7-stage naming is opinionated.** If you prefer "Idea -> Research -> Angle -> Cast -> Plan -> Generate -> Publish" (closer to the existing internal labels), swap the names — the structure stands.
- **Hard-gate at Stage 6 is the UX riskiest decision.** Per-pass gating can feel like a lot of clicking. Test with both a producer (Jordan) and a first-time user (Sam).
- **The "Why this?" pattern is novel.** No reference product uses it this way. Validate with 3-5 users before committing.

---

*Status: design draft . awaiting review . next step: render to `02-guided-flow-v2.svg` using the existing visual language from `02-guided-flow.svg` (dark surface, accent #6b8eff, purple #a78bfa).*
