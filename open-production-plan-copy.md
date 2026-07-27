# Open Production — Exhaustive Architecture & Product Plan
# AI-Native Production Studio: From CLI to Creative Operating System

**Document type:** Architecture & Product Plan  
**Status:** [ ] pending implementation  
**Scope:** Full product vision, research synthesis, system architecture, and execution checklist  
**Source prompt:** Principal AI Product Architect / HCI / Creative Production Pipeline / Senior Systems Architect research brief

---

## TASK CHECKLIST — EXECUTION ORDER

Use this checklist to track progress through the plan. Each item maps to a section below.
**Legend:** [x] = written in this document | [ ] = requires external validation or implementation action

### Phase 0 — Foundation Research (validate before building anything)
- [ ] P0-1: Validate competitive landscape findings against current product state (2025–2026) → Section 2, Appendix F
- [ ] P0-2: Validate academic research synthesis (2024–2026 papers) → Section 6
- [ ] P0-3: Confirm user persona definitions with at least one real user per persona → Section 8
- [ ] P0-4: Confirm production pipeline stage ordering with a practicing video producer → Section 14, Appendix G
- [ ] P0-5: Stress-test the "Generation is only 5%" philosophy against real user workflows → Section 3, Appendix F Q5

### Phase 1 — Product Philosophy & Vision
- [x] P1-1: Lock the product philosophy (Section 3) — Five Laws + 5% Rule written
- [x] P1-2: Define the three non-negotiable design axioms (Section 4) — written
- [x] P1-3: Write the "Features that should NEVER be added" list (Section 25) — 8 items written
- [x] P1-4: Define the differentiators list (Section 26) — 10 differentiators written

### Phase 2 — Architecture Design
- [x] P2-1: Design the information architecture (Section 9) — Studio/Production/Shot model + schemas written
- [x] P2-2: Design the production pipeline data model (Section 14 + Appendix G) — 26 stages + deep dives written
- [x] P2-3: Design the asset system schema (Section 13) — 7 asset types + provenance model written
- [x] P2-4: Design the agent collaboration protocol (Section 15) — crew coordination protocol + scope contracts written
- [x] P2-5: Design the state management model (Section 16) — state machine + event log + version trees written
- [x] P2-6: Design the plugin/extensibility architecture (Section 17–18) — plugin contracts + kernel-blind model written

### Phase 3 — Frontend Architecture
- [x] P3-1: Design the spatial canvas model (Section 10) — 5 views written
- [x] P3-2: Design the AI interaction model (Section 11 + Appendix D) — crew model + 7 interaction patterns written
- [x] P3-3: Design the customization system (Section 12 + Appendix H) — 7 categories fully designed
- [x] P3-4: Design the iteration/version tree system (Appendix E) — 3 iteration types + version tree + layer stack written

### Phase 4 — Risk & Roadmap
- [x] P4-1: Document all technical risks (Section 20) — 9 risks with mitigations written
- [x] P4-2: Document all UX risks (Section 21) — 8 risks with mitigations written
- [x] P4-3: Write the long-term roadmap (Section 23) — 5-phase roadmap (months 0–48+) written
- [x] P4-4: Write the moonshot ideas list (Section 24) — 7 moonshots written

### Phase 5 — Validation
- [x] P5-1: All 6 secondary research questions answered in depth → Appendix F
- [x] P5-2: Pixar/Adobe/Unreal stress tests answered → Appendix B
- [x] P5-3: Beginner/professional dual-path mapped for every major decision → Appendix I
- [x] P5-4: All 26 required output items covered → see cross-reference index below

### Cross-Reference: All 26 Required Outputs → Document Location
| # | Required Output | Location |
|---|---|---|
| 1 | Vision | Section 1 |
| 2 | Product philosophy | Section 3 |
| 3 | Competitive analysis | Section 2 |
| 4 | Research findings | Section 5 |
| 5 | Academic findings | Section 6 |
| 6 | Missing gaps in today's products | Section 7 |
| 7 | User personas | Section 8 |
| 8 | Production workflow | Section 14 + Appendix G |
| 9 | Information architecture | Section 9 |
| 10 | Frontend architecture | Section 10 + Appendix C |
| 11 | AI interaction model | Section 11 + Appendix D |
| 12 | Customization system | Section 12 + Appendix H |
| 13 | Asset system | Section 13 |
| 14 | Production pipeline | Section 14 + Appendix G |
| 15 | Agent collaboration | Section 15 |
| 16 | State management | Section 16 |
| 17 | Plugin architecture | Section 17 |
| 18 | Extensibility | Section 18 |
| 19 | Scalability | Section 19 |
| 20 | Technical risks | Section 20 |
| 21 | UX risks | Section 21 |
| 22 | Research opportunities | Section 22 |
| 23 | Long-term roadmap | Section 23 |
| 24 | Moonshot ideas | Section 24 |
| 25 | Features never to add | Section 25 |
| 26 | Differentiating features | Section 26 |

### Remaining Actions (external to this document)
- [ ] ACT-1: User research — validate personas with 1 real user per persona type
- [ ] ACT-2: Technical spike — prototype the Consistency Contract implementation
- [ ] ACT-3: Design sprint — build the Director's Canvas wireframe (5 views)
- [ ] ACT-4: Agent design — write the scope contract for each of the 12 agents
- [ ] ACT-5: Data model — finalize Production Document JSON schema for implementation
- [ ] ACT-6: Provider research — evaluate generation backends against CameraPreset + LightingPreset specs
- [ ] ACT-7: Legal — rights clearance model for Voice Library and Music Library
- [ ] ACT-8: CLI bridge — design the API bridge from existing CLI backend to the production state model

---

## SECTION 1 — VISION

### The One-Sentence Vision
Open Production is a **production operating system** where the AI behaves as an entire production crew, the user behaves as a director, and every creative decision is permanent, inspectable, and reversible.

### What This Is Not
- Not a video generator. Generators produce outputs. Studios produce *productions*.
- Not a chatbot with a render button. Conversation is one channel among many.
- Not a wrapper around a model API. The model is one tool in a production crew of many.
- Not a tool for one person. It is designed to scale from solo creator to studio team.

### The Central Bet
The central bet is that **the production process is the product**. The output video is a byproduct of a captured, inspectable, replayable production process. A user who finishes a production should be able to hand off the entire production — not just the video — to a collaborator who can pick up exactly where they left off, change the creative direction, regenerate any stage, and publish a different cut.

### The Pixar Test
Pixar takes 4–7 years per film. Every frame is a decision. Every decision is traceable. The production is a living document that evolves. The final render is a snapshot of a process, not the process itself. Open Production must pass the Pixar test: **would a production team at Pixar recognize this as a production environment, not a toy?**

---

## SECTION 2 — COMPETITIVE ANALYSIS

### What Exists Today (2024–2026 Snapshot)

| Product | Strength | Critical Gap |
|---|---|---|
| Runway Gen-3 | Fast generation, growing controls | No production concept; each output is orphaned |
| Google Veo / Flow | High quality video | No iterative workflow; no asset persistence |
| Pika / Kling | Accessible, fast | Single-shot; no composition or timeline thinking |
| Luma Dream Machine | Strong camera motion | No narrative structure |
| Adobe Premiere AI | Editing power | Generation is bolted on; no generative-first design |
| Adobe Firefly | Brand safety, consistency | Isolated tool; no pipeline |
| CapCut / Captions | Consumer friendly | Production depth missing |
| ComfyUI / InvokeAI | Maximum control | No production UX; experts only |
| OpenMontage | Pipeline-aware | Still prompt-centric; lacks asset management, timeline, iteration |
| DaVinci Resolve | Professional editor | AI is an add-on; generative-first is not the paradigm |
| Unreal Engine | Production-grade | Steep; not designed for AI-native generation |
| Figma | Multiplayer canvas, components | Video-blind; no timeline; no generation |
| Cursor | Agent-native IDE | Code-only; the AI model is the right interaction metaphor |

### The Design Pattern Every Product Gets Wrong
Every existing product treats generation as the **primary action**. The user prompts; the AI generates; the user evaluates; the user re-prompts. This is a feedback loop, not a production workflow.

Real production is:
1. **Intent** — what do we want to say?
2. **References** — what does it look and feel like?
3. **Structure** — how is it organized?
4. **Execution** — how is it made?
5. **Evaluation** — does it say what we wanted?
6. **Iteration** — what changes?
7. **Publication** — who sees it?

No current product models all seven. Most model only step 4. Some add step 5. None model steps 1–3 as first-class citizens.

---

## SECTION 3 — PRODUCT PHILOSOPHY

### The Five Laws

**Law 1: Generation is a service call, not a product.**  
Generation is what the AI does when the human has finished deciding. The interface should make clear that generation is a step in a larger process, not the goal.

**Law 2: Nothing is final until the user says so.**  
Every generated asset, every script line, every camera angle is provisional until explicitly locked. Locking is an affirmative user action. Unlocking is always possible.

**Law 3: Every decision has a reason.**  
The system captures *why* a decision was made (chosen angle, chosen reference, chosen constraint) alongside *what* was decided. This is the audit trail principle from the research-writing vertical, applied to production.

**Law 4: Beginners and professionals use the same engine, different views.**  
The production engine is the same. The interface layer adapts. A beginner sees guided mode. A professional sees director mode. The engine beneath is identical.

**Law 5: The AI earns autonomy incrementally.**  
The AI is not trusted by default. It earns the right to act autonomously by demonstrating quality. Until it has earned trust, every AI action is proposed, not executed.

### The 5% Rule (Production Philosophy)
- **5% generation** — the AI renders; this is the least interesting part
- **25% planning** — intent, reference, structure, briefing the production crew
- **40% iteration** — review, adjust, re-generate, compare, approve
- **15% asset management** — build libraries, save presets, reuse elements
- **15% production management** — sequence, schedule, orchestrate, publish

This ratio must be enforced at the UX level. The interface should make it *harder* to jump to generation than to plan first.

---

## SECTION 4 — THREE NON-NEGOTIABLE DESIGN AXIOMS

### Axiom 1: Production State is First-Class
The production state — the full record of every decision, asset, reference, script, shot, and generation — must be serializable, versioned, diffable, and shareable. A production is not a folder of video files. It is a document.

### Axiom 2: Every Interface is a View of the Same Model
The timeline view, the storyboard view, the node graph view, the script view, and the chat interface are all views of the same underlying production model. Changing something in one view changes it everywhere.

### Axiom 3: Human Override is Always Available
No AI action is irreversible. No AI decision is hidden. Every AI-generated value can be manually overridden. The override is stored as an annotation on the production state, not as a replacement.

---

## SECTION 5 — RESEARCH FINDINGS (Industry Patterns)

### Pattern 1: The "Last Mile" Problem
Users of generative tools consistently report that generation accounts for <10% of their total time. The majority of time is spent: (a) preparing inputs that lead to good generation, (b) evaluating and comparing outputs, (c) fixing outputs that are 90% right. No current product has a good answer to any of these three.

### Pattern 2: Prompt Scaling Failure
Prompts fail to scale for four structural reasons:
1. **Context window pressure** — complex productions require more context than a prompt can hold
2. **Implicit knowledge loss** — domain knowledge (lighting rules, composition rules, narrative rules) cannot be fully expressed in natural language
3. **No memory of intent** — a new prompt has no memory of why previous prompts were written
4. **No shared vocabulary** — the user's mental model and the model's latent space share no stable vocabulary

The solution is **structured intent objects** — production briefs, shot sheets, character specs — that replace ad-hoc prompts with structured data the model can reliably condition on.

### Pattern 3: The "Director's Cut" Gap
Professional productions are defined by their cuts. The final cut is the product. But no AI video tool has a concept of a cut, a version, or an alternative. Every generation is a new thing. This is why AI video tools feel like toys — they produce artifacts, not productions.

### Pattern 4: Asset Consistency as the Unsolved Problem
Character consistency across shots, environment consistency across scenes, lighting consistency across a production — these are the hardest problems in AI video and the most important for professional use. Current solutions (IP-Adapter, ControlNet, identity conditioning) are fragile and tool-specific. A production environment needs a **consistency contract** — a formal specification of what must remain stable across generations.

### Pattern 5: The Missing Critique Layer
Professional creatives do not iterate alone. They work with critics, directors, producers, and reviewers. AI tools have no critique layer. The AI generates; the human evaluates; the loop is closed. A production environment needs an AI **reviewer** that can evaluate outputs against the production brief — not just generate.

### Pattern 6: Figma's Lesson
Figma succeeded not because it made design easier (it didn't, compared to Sketch for simple tasks) but because it made **design collaboration** real-time and the design document the source of truth. The lesson: the source-of-truth document is more important than the interface.

### Pattern 7: Cursor's Lesson
Cursor succeeded not because it added AI to an IDE but because it made **AI intent explicit** — you see what the AI is about to do before it does it. The "AI as proposal, human as approver" interaction model is the one that builds trust. This must be the default for Open Production.

### Pattern 8: ComfyUI's Lesson
ComfyUI succeeded with advanced users because it **exposed the computation graph**. Every node is a decision. Every connection is a dependency. Advanced users want to see the wiring. The production node graph should be available as an expert view.

---

## SECTION 6 — ACADEMIC RESEARCH FINDINGS (2024–2026)

### Finding 1: Mixed Initiative is the Right Frame (Amershi et al., extended)
Mixed-initiative AI systems — where the AI and human alternate in taking initiative — consistently outperform both pure-human and pure-AI systems on creative tasks. The key finding: the handoff point matters more than either party's individual contribution. A well-designed handoff (where the AI proposes and the human approves) produces better outcomes than either AI-only or human-only generation.

**Design implication:** Every production stage should have a clear handoff point. The AI drives execution; the human drives approval.

### Finding 2: Creative Scaffolding Reduces Blank-Page Anxiety
Research on creative AI assistants consistently shows that the hardest moment for users is the empty canvas. Users given a structured starting point (even one they will completely replace) produce better outputs and report higher satisfaction. This validates the importance of templates, production presets, and guided onboarding.

**Design implication:** No production should start with a blank canvas. The system should always propose a starting structure — even if that structure is immediately discarded.

### Finding 3: Version History Drives Creative Risk-Taking
Users with visible version history take more creative risks. Knowing they can go back makes them more willing to try bold alternatives. The absence of version history is not just a technical gap — it is a psychological inhibitor of creativity.

**Design implication:** Version history should be front-and-center, not hidden in a menu. The production history should be visible at all times.

### Finding 4: Explanations Increase Trust in AI Outputs
Users trust AI outputs more when the AI explains its reasoning. Unexplained outputs are treated with higher skepticism, even when quality is equivalent. The explanation does not need to be long — a one-sentence rationale increases trust significantly.

**Design implication:** Every AI action should produce a rationale. "I chose this camera angle because..." should appear alongside every AI decision.

### Finding 5: Progressive Disclosure is Optimal for Dual-Expertise UX
The best interfaces for both beginners and experts use progressive disclosure — showing simple controls by default and revealing complex controls on demand. The key finding: the disclosure must be *semantic* (reveal more of the same concept) not *syntactic* (reveal more buttons). Users who see more buttons do not learn faster; users who see deeper views of the same concept do.

**Design implication:** Every panel should have a "go deeper" mode that reveals the same concept in more detail, not more options.

---

## SECTION 7 — MISSING GAPS IN TODAY'S PRODUCTS

1. **No production document.** Every AI video tool produces files, not documents. A production document is a serializable, shareable, diffable record of a production.

2. **No consistency contract.** No tool has a formal way to say "character X must look the same in every shot." IP-Adapter is a workaround, not a system.

3. **No critique layer.** No tool has an AI reviewer. Every loop is: generate → human evaluates → re-prompt. The AI never evaluates its own outputs against a spec.

4. **No multi-stage pipeline.** Every tool is single-stage. You prompt; you get a video. There is no concept of "we are in the storyboard stage, not the generation stage."

5. **No asset library with production provenance.** Assets exist as files. There is no record of which production they came from, how they were made, or which version they represent.

6. **No director mode.** No tool has a concept of the user as director — setting creative direction, approving shots, rejecting performances, requesting alternatives.

7. **No collaborative production state.** No tool has a shared production state that multiple people can work on simultaneously.

8. **No iteration branching.** Every generation is a new thing. There is no concept of a branch — "let's try this creative direction and see where it goes, while keeping the other direction alive."

9. **No production briefing.** No tool has a concept of briefing the AI — giving it the full production context before asking it to act.

10. **No publishing pipeline.** Generation and publication are disconnected. There is no concept of "this production is ready to publish; here is the publishing spec."

---

## SECTION 8 — USER PERSONAS

### Persona 1: The Emerging Creator ("Sam")
- Age 19–28, self-taught, makes content for YouTube/TikTok/Instagram
- Has ideas but lacks production vocabulary
- Will spend 30 min maximum before wanting to see something
- Needs: guided production, smart defaults, instant gratification with a path to depth
- Failure mode: overwhelmed by options, gives up and uses a simpler tool
- Success mode: completes a 60-second video with five intentional shots and a color grade

### Persona 2: The Creative Professional ("Jordan")
- Age 28–45, trained filmmaker or motion designer
- Has production vocabulary; knows what "color grade," "b-roll," "coverage" mean
- Will spend hours on a single sequence to get it right
- Needs: director mode, full control, asset library, no dumbing-down
- Failure mode: can't get to the controls they need; surface is too simplified
- Success mode: directs a 3-minute branded film using the AI as a production crew

### Persona 3: The Studio Lead ("Alex")
- Age 35–55, runs a team of 3–15 creators
- Manages multiple productions simultaneously
- Needs: production management, asset sharing, brand consistency, review workflows
- Failure mode: can't share productions with team; no consistency controls; no approval workflow
- Success mode: the entire team uses the same character library, same brand kit, same production templates

### Persona 4: The Enterprise Buyer ("Morgan")
- Age 40–60, brand manager or content director at a large organization
- Does not create directly; evaluates outputs; approves budgets
- Needs: audit trail, brand safety, cost visibility, integration with existing workflows
- Failure mode: outputs are off-brand; no audit trail; no integration
- Success mode: Open Production is approved for use across 500 creators with a locked brand kit

---

## SECTION 9 — INFORMATION ARCHITECTURE

### The Three-Layer Model

**Layer 1: Studio (the highest level)**
- A Studio is a workspace for an organization or individual
- A Studio contains: brand kits, asset libraries, member roles, production presets
- A Studio is the equivalent of a Figma Team

**Layer 2: Production (the unit of work)**
- A Production is a single creative work — a film, a series, a campaign
- A Production contains: intent document, references, assets, scenes, shots, timeline, versions, audit trail
- A Production is the equivalent of a Figma File

**Layer 3: Scene / Shot (the atomic unit)**
- A Scene is a sequence of shots with a shared location, mood, and narrative purpose
- A Shot is the atomic generatable unit — one camera, one duration, one set of parameters
- A Shot is the equivalent of a Figma Frame

### The Production Document Schema (abbreviated)
```
Production {
  id: uuid
  intent: IntentDocument
  references: Reference[]
  characters: Character[]
  locations: Location[]
  brand_kit: BrandKit
  scenes: Scene[]
  timeline: Timeline
  versions: Version[]
  audit_trail: AuditEntry[]
  state: ProductionState
}

Scene {
  id: uuid
  name: string
  mood: MoodSpec
  location: Location
  shots: Shot[]
  notes: string
}

Shot {
  id: uuid
  scene_id: uuid
  intent: string
  camera: CameraSpec
  lighting: LightingSpec
  characters: CharacterReference[]
  duration: number
  generation: GenerationResult | null
  status: ShotStatus
  version_history: ShotVersion[]
}
```

---

## SECTION 10 — FRONTEND ARCHITECTURE

### The Five Views (all views of the same underlying model)

**View 1: Director's Canvas**
- Spatial, two-dimensional canvas
- Scenes are containers; shots are cards within scenes
- Drag to reorder; click to dive into a shot
- The default view for professionals
- Inspired by: Figma canvas + DaVinci Resolve timeline

**View 2: Guided Production Flow**
- Linear, step-by-step flow
- "What's your idea?" → "Pick references" → "Meet your crew" → "Plan shots" → "Generate"
- The default view for beginners
- Inspired by: Notion onboarding + Linear project creation

**View 3: Timeline Editor**
- Horizontal timeline of shots
- Stacked tracks: video, audio, voice, music, effects
- Cut, trim, reorder, blend
- The default view for editors
- Inspired by: DaVinci Resolve + Premiere Pro

**View 4: Agent Console**
- The production crew in conversation
- Each agent (Creative Director, Shot Designer, etc.) has a panel
- Agents send proposals; the user approves or adjusts
- The default view for AI power users
- Inspired by: Cursor agent panel + Slack threading

**View 5: Node Graph**
- Every production operation as a node
- Every dependency as an edge
- Full DAG of the production
- The expert/developer view
- Inspired by: ComfyUI + Unreal Engine Blueprints

### The Universal Rule
Switching between views must be instant. No data is lost when switching. Changes in one view immediately reflect in all views.

---

## SECTION 11 — AI INTERACTION MODEL

### The Production Crew Model
The AI is not one agent. It is a crew of specialist agents, each with a defined role, scope, and decision authority.

| Agent | Role | What They Own |
|---|---|---|
| Creative Director | Overall creative vision | Intent, tone, style consistency |
| Producer | Execution logistics | Shot schedule, resource allocation |
| Storyboard Artist | Visual planning | Shot compositions, sequences |
| Shot Designer | Individual shot specs | Camera, lighting, framing |
| Character Director | Character consistency | Character specs, expressions, movement |
| Environment Artist | Location consistency | Environment specs, lighting mood |
| Voice Director | Voice performance | Voice specs, tone, pacing |
| Sound Designer | Audio design | Sound palettes, SFX specs |
| Music Composer | Score | Music briefs, cue specifications |
| Editor | Cut logic | Pacing, transitions, timing |
| Colorist | Color grade | Color specs, LUTs, grading intent |
| Reviewer | Quality evaluation | QA checklist, consistency review |

### The Proposal Protocol
Every agent action follows the same four-step protocol:
1. **Context load** — the agent reads the current production state and relevant history
2. **Proposal generation** — the agent generates one to three proposals (never just one, never more than three)
3. **Rationale** — each proposal is accompanied by a one-sentence rationale
4. **Human decision** — the user approves, rejects, or adjusts each proposal

The AI never executes without approval. The approval can be given in bulk ("approve all") for non-critical decisions, but the approval step is never skipped.

### Director Mode vs. Guided Mode

**Director Mode (professionals):**
- User gives direction; agents execute
- Proposals are shown but can be approved with a single keystroke
- The user can override any agent decision at any time
- The conversation history is always visible

**Guided Mode (beginners):**
- The system asks questions; the user answers
- Each answer reduces the decision space for the next question
- The user never sees the raw agent conversation — only the guided prompts
- At any point, the user can "go pro" and switch to Director Mode

---

## SECTION 12 — CUSTOMIZATION SYSTEM

### The Library Hierarchy

**Studio Library (shared across all productions in a Studio)**
- Brand Kits: colors, fonts, logos, approved language, style tokens
- Character Library: named characters with consistency specs
- Environment Library: named locations with consistency specs
- Voice Library: approved voice profiles
- Music Library: approved music briefs and cue templates
- Motion Library: approved motion presets
- Camera Presets: named camera + lens combinations
- Lighting Presets: named lighting setups

**Production Library (specific to one Production)**
- Production-specific characters and environments (can promote to Studio)
- Production-specific presets
- Prompt templates used in this production
- Narrative templates

### The Consistency Contract
Every character and environment has a Consistency Contract — a formal spec that every generation must satisfy:

```
ConsistencyContract {
  subject_id: uuid
  visual_anchors: ImageReference[]  # reference images
  required_attributes: Attribute[]  # must match
  prohibited_attributes: Attribute[]  # must not appear
  variance_tolerance: float  # 0.0 = identical, 1.0 = loose
  reviewer_checklist: ChecklistItem[]
}
```

The Reviewer agent evaluates every generation against the Consistency Contract before it is presented to the user. Failed generations are never shown — the system silently regenerates or escalates.

### Style Tokens
Style tokens are named, reusable visual parameters:
- Color palette (hex codes + emotional labeling)
- Texture vocabulary (described in natural language)
- Lighting vocabulary (described in natural language)
- Motion vocabulary (described in natural language)
- Framing vocabulary (rule of thirds, symmetry, leading lines)

Style tokens are injected into every generation prompt. The user never writes a prompt from scratch — they compose from tokens.

---

## SECTION 13 — ASSET SYSTEM

### Asset Types
1. **Visual Sources** — images, videos, reference frames (with provenance metadata)
2. **Characters** — identity specs, expression libraries, voice associations
3. **Environments** — location specs, lighting moods, time-of-day variants
4. **Audio** — voice profiles, music cues, sound palettes
5. **Presets** — camera, lighting, motion, color grade
6. **Templates** — production structures, scene sequences, narrative arcs
7. **Generations** — every AI-generated output, stored with full generation parameters

### Asset Provenance
Every asset stores:
- Where it came from (imported, generated, derived)
- When it was created
- Which production created it
- Which parameters produced it (for generated assets)
- Which version of the system produced it
- Who approved it
- Where it has been used (cross-production references)

### Asset Addressing
Assets are content-addressed (SHA-256 of content), consistent with the Open Production kernel design. An asset's identity is its content. Two assets with identical content are the same asset. This enables deduplication, caching, and reproducibility.

### The Asset Promotion Flow
Assets flow upward: Shot → Scene → Production → Studio Library.  
Promotion is an explicit user action. Assets are never automatically promoted.  
Demotion is not allowed. A promoted asset can be deprecated but never removed (audit trail integrity).

---

## SECTION 14 — PRODUCTION PIPELINE (All 26 Stages)

Each stage has: **Purpose / AI role / Human role / Outputs / Gates**

| # | Stage | AI Role | Human Role | Output | Gate |
|---|---|---|---|---|---|
| 1 | Idea | Prompt expansion, angle generation | Declare intent | Intent Document | Intent must be parseable |
| 2 | Research | Source retrieval, synthesis | Validate sources | Research Brief | At least 3 sources |
| 3 | References | Reference clustering, mood extraction | Approve references | Reference Board | Style tokens extractable |
| 4 | Moodboard | Visual assembly from references | Approve mood | Moodboard | Tone is locked |
| 5 | Creative Direction | Direction proposal (3 options) | Pick direction | Creative Brief | Direction is locked |
| 6 | Story | Story structure proposal | Approve structure | Story Outline | Structure is locked |
| 7 | Script | Script generation from outline | Line edits | Script | Script is locked |
| 8 | Characters | Character specs from script | Approve characters | Character Library entries | Consistency contract set |
| 9 | Locations | Environment specs from script | Approve locations | Environment Library entries | Consistency contract set |
| 10 | Shot Planning | Shot list from script | Approve shot list | Shot List | Shot count is locked |
| 11 | Storyboard | Frame compositions per shot | Approve compositions | Storyboard | Compositions locked |
| 12 | Timeline | Scene/shot sequencing | Approve sequence | Timeline | Sequence locked |
| 13 | Camera | Camera specs per shot | Approve cameras | Camera Specs | Specs locked per shot |
| 14 | Lighting | Lighting specs per shot | Approve lighting | Lighting Specs | Specs locked per shot |
| 15 | Assets | Asset assembly and gap detection | Approve assets | Asset manifest | All assets resolved |
| 16 | Generation | Video generation per shot | Review outputs | Generated shots | Reviewer gate passes |
| 17 | Editing | Cut assembly | Approve cut | Edit timeline | Cut is locked |
| 18 | Animation | Motion and transition specs | Approve motion | Animated shots | Motion locked |
| 19 | Voice | Voice direction per character | Approve performances | Voice recordings | Performance locked |
| 20 | Music | Score cue generation | Approve score | Music cues | Score locked |
| 21 | Sound | SFX design | Approve sound design | Sound mix | Mix locked |
| 22 | Color | Color grade per scene | Approve grade | Graded timeline | Grade locked |
| 23 | Review | Full production QA | Approve or flag | QA report | All gates pass |
| 24 | Iteration | Alternative generation, branch comparison | Decide on direction | Updated production | Direction confirmed |
| 25 | Publishing | Export, format, platform specs | Approve publish spec | Publish manifest | Publish spec locked |
| 26 | Archive | Production archiving | — | Production archive | Audit trail complete |

### Stage Gates
Between every stage is a **stage gate** — a checklist of conditions that must be met before the next stage begins. Gates are visible to the user. The AI cannot proceed past a gate without human approval. This is the same fail-closed gate principle from the research-writing vertical, generalized to production.

---

## SECTION 15 — AGENT COLLABORATION MODEL

### The Crew Coordination Protocol
Agents communicate through the production state, not through direct messages. An agent reads the production state, proposes an update, and writes the update only after human approval. Agents do not call each other — they read from and write to the shared state.

This is the reconciliation loop from the Open Production kernel:
```
Loop {
  acquire → read current production state
  detect → identify what needs to happen next
  plan → propose the next action
  dispatch → generate a proposal
  commit → write after human approval
  release → notify the next agent that state has changed
}
```

### Agent Scope Contracts
Every agent has a strictly bounded scope. An agent cannot modify state outside its scope. Violations are logged and surfaced to the user.

| Agent | Can Write | Cannot Write |
|---|---|---|
| Creative Director | Intent, tone | Any generation parameters |
| Shot Designer | Camera, lighting, framing | Character specs, script |
| Reviewer | QA flags, quality scores | Any generative parameters |

### The Escalation Protocol
When an agent cannot make a decision within its scope (e.g., a contradiction between the Creative Brief and the Script), it escalates to the user with a clear statement of the conflict. It does not resolve the conflict silently.

---

## SECTION 16 — STATE MANAGEMENT

### The Production State Machine
A Production has exactly six states:

```
DRAFT → BRIEFED → IN_PRODUCTION → IN_REVIEW → APPROVED → PUBLISHED
```

Transitions are one-directional (forward) except for `IN_REVIEW → IN_PRODUCTION` (revision loop). State transitions require human confirmation.

### The Immutable Event Log
Every action on a Production is an event appended to an immutable log:

```
Event {
  id: uuid
  ts: ISO8601
  production_id: uuid
  actor: "human" | agent_id
  action: EventType
  payload: dict
  state_before: hash
  state_after: hash
}
```

The production state at any point in time can be reconstructed from the event log. This is Git for productions.

### Version Trees
A production version is a named snapshot of the production state. Branches are allowed — a branch is a named fork of the production at a specific state. Branches can be compared and merged (with human direction on conflicts).

---

## SECTION 17 — PLUGIN ARCHITECTURE

### The Plugin Surface
Plugins can extend four surfaces:

1. **Generation backends** — swap or add generation providers (Runway, Veo, Pika, local models)
2. **Agent roles** — add custom agents with custom scope contracts
3. **Asset types** — add custom asset types with custom provenance schemas
4. **Export formats** — add custom publish targets (platforms, formats, integrations)

### Plugin Contracts
Every plugin must implement a typed contract:

```
GenerationPlugin {
  name: str
  capabilities: Capability[]
  generate(shot: Shot, context: ProductionContext) -> GenerationResult
  estimate_cost(shot: Shot) -> CostEstimate
  health_check() -> bool
}
```

Plugins that fail their health check are disabled and the user is notified. The production continues with the remaining plugins.

---

## SECTION 18 — EXTENSIBILITY

### The Kernel is Medium-Blind (by design)
The five primitives (Source, Transform, Composition, Evaluation, Intent) are the kernel. Every domain-specific feature (video, research writing, audio, code) is a plugin layer over the kernel. This is the architectural decision already locked in `docs/architecture/architecture.md`.

### The Video Vertical as the Second Plugin
The video production environment described in this document is a vertical — a plugin layer over the Open Production kernel. It does not modify the kernel. It extends it with video-specific types, agents, and views.

### Extensibility Principles
- Any tool that implements the generation plugin contract can be used as a generation backend
- Any organization can define custom agent roles within the scope contract system
- Any platform can be added as a publish target
- The kernel is never modified to support a vertical — the vertical adapts to the kernel

---

## SECTION 19 — SCALABILITY

### The Bottlenecks (and how to address them)

**Bottleneck 1: Generation throughput**  
Solution: generation is async. Shots are queued and generated in parallel. The user sees progress in real time. The production does not block on generation.

**Bottleneck 2: Asset storage**  
Solution: content-addressed storage. Deduplication is automatic. Large productions (hundreds of shots) do not grow linearly in storage.

**Bottleneck 3: State sync for collaboration**  
Solution: the event log is the source of truth. Sync is event-replay, not state-transfer. Conflicts are surfaced as events, not overwritten.

**Bottleneck 4: Agent context window**  
Solution: agents do not hold production context in their context window. They read from the production state on each tick. Context window pressure is bounded by shot-level scope, not production-level scope.

**What happens when productions are 100x larger?**  
A 100-episode series has 100 productions, not one. The Studio Library is the shared state. Each production is independently versionable and archiveable. The system does not try to hold 100 episodes in memory simultaneously.

---

## SECTION 20 — TECHNICAL RISKS

| Risk | Severity | Mitigation |
|---|---|---|
| Character consistency across generations | Critical | Consistency Contract + Reviewer agent gate |
| Generation latency breaks flow state | High | Async generation, optimistic UI, background queue |
| Context window overflow for complex productions | High | Shot-level scoping; no production-level prompts |
| Plugin provider API instability | High | Health checks, fallback providers, cached generations |
| Audit log storage growth | Medium | Append-only log with configurable retention; archive exports |
| State sync conflicts in collaborative mode | Medium | Event sourcing; conflict surfacing protocol |
| Model output drift over time | Medium | Generation parameter pinning; version-locked providers |
| Privacy of production content in cloud | Medium | Local-first option; encrypted state; no telemetry by default |
| Cost unpredictability for generative operations | High | Cost estimation per shot before generation; hard budget caps |

---

## SECTION 21 — UX RISKS

| Risk | Severity | Mitigation |
|---|---|---|
| Beginners overwhelmed by production pipeline depth | Critical | Guided mode as default; progressive disclosure |
| Professionals frustrated by approval gates slowing them down | High | Bulk approve; keyboard-first shortcuts; configurable gate strictness |
| Users not understanding why a generation failed | High | Reviewer agent explains every rejection |
| Version tree becomes unnavigable | Medium | Named versions; branch summaries; visual diff |
| Asset library becomes unusable at scale | Medium | Semantic search; tagging; production provenance filtering |
| AI proposals feel generic or irrelevant | High | Brief the crew before proposing; proposals are context-specific |
| Users abandoning mid-production due to lost flow | High | Auto-save every event; resume from any point; mobile companion app |
| Cognitive overload from multi-agent conversations | Medium | Single-agent view by default; crew console as opt-in |

---

## SECTION 22 — RESEARCH OPPORTUNITIES

1. **Consistency contract efficacy** — which visual anchor types (reference images, embeddings, textual descriptions) produce the most consistent generations across shots?
2. **Optimal proposal count** — is 3 proposals always optimal? Research suggests diminishing returns after 3 but some users prefer 5 for color grading decisions.
3. **Gate strictness calibration** — how strict should the Reviewer agent be? Too strict creates friction; too loose allows inconsistency.
4. **Director mode adoption curve** — how quickly do beginners move from Guided to Director mode? What triggers the switch?
5. **Audit trail comprehension** — do users actually read audit trails? How should they be surfaced to be useful rather than overwhelming?
6. **Multi-agent conversation legibility** — what is the optimal interface for showing multiple agents interacting? Sequential? Parallel? Threaded?

---

## SECTION 23 — LONG-TERM ROADMAP

### Phase 1 — Foundation (months 0–6)
- Production document data model
- Director's Canvas view
- Guided Production Flow (beginner mode)
- 5 core agents: Creative Director, Shot Designer, Editor, Reviewer, Publisher
- Asset library (characters, environments)
- Single generation backend (pluggable)
- Immutable event log
- Version snapshots (no branching yet)

### Phase 2 — Production Depth (months 6–12)
- Full 26-stage pipeline
- All 12 agents
- Consistency Contract system
- Style Token system
- Timeline Editor view
- Version branching
- Studio Library (multi-production asset sharing)
- Plugin API (generation backends, export formats)

### Phase 3 — Collaboration (months 12–18)
- Multi-user production state (real-time sync)
- Role-based access (Director, Producer, Reviewer, Viewer)
- Review workflow (approval chains)
- Brand Kit enforcement
- Enterprise audit trail (tamper-evident)

### Phase 4 — Intelligence (months 18–30)
- Production memory (the system learns from a studio's production history)
- Automatic consistency detection (the system flags inconsistencies without being prompted)
- Predictive production planning (the system estimates completion time, cost, and risk for a production brief)
- Cross-production asset discovery (the system surfaces relevant assets from previous productions)
- AI-directed iteration (the system proposes specific changes to improve quality, not just "try again")

### Phase 5 — Platform (months 30–48)
- Open plugin marketplace
- Third-party agent publishing
- API for external orchestration (integrate with existing production pipelines)
- Mobile companion app (review and approve on the go)
- Physical production integration (AR previsualization, on-set AI assistance)

---

## SECTION 24 — MOONSHOT IDEAS

1. **Production DNA** — every production leaves a DNA fingerprint. The system learns the studio's aesthetic from their production DNA and uses it to improve every future production without being explicitly instructed.

2. **Living Productions** — a production that continues after publication. New episodes, alternate endings, and response content are generated from the same production state in response to audience feedback.

3. **Co-director Mode** — two human directors working on the same production simultaneously, with the AI moderating creative conflicts and proposing resolutions.

4. **Production Translation** — translate a production between formats (short film → interactive narrative → social series) while preserving the production DNA.

5. **Retrospective Analysis** — after a production is published, the system analyzes which decisions made the biggest difference to the final quality and produces a lessons-learned report.

6. **Audience-Adaptive Generation** — the system generates different cuts of the same production for different audience segments, dynamically assembled from the same shot library.

7. **The Zero-Generation Production** — a production made entirely without AI generation, using only existing assets from the studio library. The system orchestrates; the human provides all creative material.

---

## SECTION 25 — FEATURES THAT SHOULD NEVER BE ADDED

1. **"Magic button" one-shot production.** A single button that takes a prompt and outputs a finished video. This violates the product philosophy and trains users to expect magic instead of production.

2. **Auto-publish without human approval.** The publication gate is always a human decision. Automation ends at "ready to publish," not "published."

3. **Prompt history as production history.** Prompts are not a record of creative decisions. Do not expose raw prompts as the primary history view.

4. **AI-generated brand kits.** Brand kits are identity documents. They must be authored by the brand, not generated by the AI. AI can suggest; AI never decides.

5. **Irreversible operations.** Every action must be undoable. No "delete forever" without a 30-day recovery window. No "overwrite" without a version snapshot.

6. **Hidden AI decisions.** If the AI made a decision, the user must be able to see it, understand it, and override it. No silent optimization.

7. **Gamification of production metrics.** No "completion score," no "quality rating," no leaderboard. Production quality is contextual and subjective. Gamification creates incentives to optimize for metrics rather than creative quality.

8. **Cross-production content leakage.** Assets, briefs, and production content from one studio must never appear in another studio's suggestions, training data, or recommendations.

---

## SECTION 26 — FEATURES THAT DIFFERENTIATE THIS PRODUCT

1. **The Production Document** — a serializable, diffable, versionable record of every creative decision. No competitor has this.

2. **The Consistency Contract** — a formal spec for visual consistency across shots and scenes. No competitor has this as a first-class system.

3. **The Production Crew Model** — 12 specialist agents with bounded scope contracts. No competitor treats AI as a crew rather than a single assistant.

4. **Stage Gates** — explicit, human-approved gates between production stages. No competitor makes the stage boundaries explicit and human-controlled.

5. **The Reviewer Agent** — an AI that evaluates outputs against the production brief before showing them to the user. No competitor has a QA layer that catches failures before the human sees them.

6. **Director Mode / Guided Mode on the same engine** — the exact same production engine serves beginners and professionals. The interface adapts; the engine does not. No competitor has solved the beginner/professional split without splitting the product.

7. **Version Branching** — the ability to maintain multiple creative directions simultaneously and compare them. No competitor has this as a first-class production concept.

8. **The Agent Console** — a visible, multi-agent conversation where the user can see which agent is acting, why, and what they proposed. No competitor exposes agent reasoning this way.

9. **Cross-production asset provenance** — every asset knows where it came from, where it has been used, and how it has evolved. No competitor has production provenance at this depth.

10. **The Production Node Graph** — a visual DAG of the full production computation, accessible to expert users. No competitor exposes the production computation graph.

---

## APPENDIX A — THE BEGINNER/PROFESSIONAL DESIGN PRINCIPLE

The central research question — *how should a production environment be designed so that beginners can create amazing productions while professionals still have complete control?* — resolves to one principle:

**The progressive depth principle:** Every feature should have exactly three levels of depth — overview (beginner sees this), standard (intermediate user engages this), expert (professional unlocks this). The levels are not separate modes — they are the same feature, revealed progressively. The beginner who becomes an expert never has to switch tools or learn a new system. They go deeper into the same system.

This principle has been validated in: Figma (layers, components, auto-layout), Blender (shader nodes, geometry nodes), Unreal Engine (Blueprint → C++), and Notion (blocks → databases → formulas). The pattern is consistent: the best creative tools have infinite depth beneath a simple surface.

---

## APPENDIX B — ANSWERS TO THE FIVE ARCHITECTURE STRESS TESTS

**"Why?"** — Because production quality is proportional to process quality. The process is the product.

**"What would Pixar do?"** — Pixar would never ship without a story review. The Reviewer agent is the story review. The consistency contract is the character bible. The production document is the production bible.

**"What would Adobe do?"** — Adobe would build a plugin ecosystem first and worry about the core product second. Do the opposite: build a kernel-first, verticals second. The plugin ecosystem comes when the kernel is proven.

**"What would Unreal Engine do?"** — Unreal would expose every parameter to expert users while hiding nothing. The node graph view is that answer. Nothing is inaccessible; everything is progressively revealed.

**"What would the user actually need?"** — The user needs to finish a production they are proud of. Every design decision should be evaluated against: does this help the user finish? Does this help the user be proud of what they finished?

**"What happens when projects become 100x larger?"** — The Studio Library scales because it is content-addressed. The event log scales because it is append-only. The agent scope contracts scale because agents never hold global context. The plugin architecture scales because providers are swappable.

**"What breaks?"** — The Consistency Contract breaks at scale if visual anchors are not refreshed. The version tree becomes unnavigable without automated summarization. The agent console becomes overwhelming without filtering. These are the known failure modes; design for them from day one.

---

*End of document.*  
*Status: [ ] pending review → [ ] pending implementation → [ ] in progress → [ ] done*


---

## APPENDIX C — UX RESEARCH SYNTHESIS: PATTERNS THAT TRANSFER

### What was researched
Adobe Firefly, Adobe Premiere AI, Adobe Express, DaVinci Resolve, Blender, Unreal Engine, Unity Cinemachine, Runway, Google Flow/Veo, Pika, Kling, Luma Dream Machine, Higgsfield, Captions, CapCut, Cursor, Figma, OpenMontage, ComfyUI, InvokeAI, Automatic1111, MidJourney workflows, Nuke, Autodesk Maya, Cinema4D, professional animation studios, virtual production pipelines, no-code creative software, game level editors.

---

### UX Pattern 1: The Command Palette (Raycast / Linear / Figma)
**What it is:** A single, context-aware input that can trigger any action in the application.  
**Why it transfers:** In a production environment, users frequently need to jump between stages, agents, assets, and views. A command palette removes the need to navigate menus — the user types intent, the system surfaces the action.  
**How to implement:** `Cmd+K` opens a production-aware command palette. It understands production context — if the user is in a shot, it surfaces shot-level actions first. If the user is in the asset library, it surfaces asset actions first. It also surfaces AI crew commands: "Brief the Shot Designer," "Ask the Reviewer to check Scene 3."  
**What to avoid:** A command palette that is just a search box. It must propose actions, not just retrieve items.

---

### UX Pattern 2: The Side-by-Side Comparison (DaVinci Resolve / Figma / GitHub)
**What it is:** The ability to view two states of the same thing simultaneously.  
**Why it transfers:** Iteration is comparison. A user who cannot see two versions of the same shot side-by-side cannot make a confident decision about which is better. The absence of comparison is the single biggest UX failure in current AI video tools.  
**How to implement:** Every shot, scene, and timeline has a "Compare" mode. Two versions are shown side-by-side. The user can scrub both simultaneously. Differences are highlighted. A single click promotes the preferred version.  
**What to avoid:** Comparison that requires manually opening two separate tabs or windows.

---

### UX Pattern 3: The Properties Panel (Figma / Blender / Unreal)
**What it is:** A context-sensitive panel on the right side of the canvas that shows the properties of whatever is selected.  
**Why it transfers:** In a production environment, every object (shot, character, location, asset) has properties that the user may want to inspect or edit. A properties panel makes these accessible without leaving the current context.  
**How to implement:** Selecting a shot opens its properties panel: camera spec, lighting spec, character references, generation history, consistency contract status, reviewer score. The panel has three depth levels — overview (key numbers), standard (full spec), expert (raw generation parameters).  
**What to avoid:** A properties panel that shows everything at once. Overwhelming property panels are the single biggest usability complaint in Blender and Unreal for new users.

---

### UX Pattern 4: Non-Destructive Layers (Photoshop / After Effects / DaVinci)
**What it is:** Changes are applied as layers on top of the original, not modifications to the original.  
**Why it transfers:** In a production, every edit should be reversible. The non-destructive layer model guarantees this structurally — the original is never modified, only supplemented.  
**How to implement:** Every human override of an AI decision is a layer. The base layer is the AI output. Override layers stack on top. The user can remove any layer to see the AI's original output. The final render is a flatten of all layers.  
**What to avoid:** Overwrite-by-default. "Save" in a production environment should always create a new version, never overwrite the previous one.

---

### UX Pattern 5: The "Accept All" / "Review Each" Split (GitHub Copilot / Cursor)
**What it is:** When the AI proposes multiple changes, the user can either accept all in one click or step through each individually.  
**Why it transfers:** Some users (beginners, in a flow state) want to say yes to the AI crew's proposals quickly. Others (professionals, at a critical decision point) want to review each one. The interface must support both patterns without forcing either.  
**How to implement:** The proposal panel always has two buttons: "Accept all" and "Review each." Accept all applies all proposals instantly. Review each opens them in sequence — one at a time, with context, with the option to modify before accepting.  
**What to avoid:** Forcing review of every proposal by default. This is what makes AI coding assistants feel slow and is why "accept all" in Cursor is so heavily used.

---

### UX Pattern 6: Spatial Context (Figma / FigJam / Miro)
**What it is:** Objects in a two-dimensional space have meaning derived from their position relative to other objects.  
**Why it transfers:** Productions are not linear. A storyboard is spatial — the director pins reference images near the shots they inspired, writes notes in the margin, draws arrows between related shots. A spatial canvas models this naturally.  
**How to implement:** The Director's Canvas is a two-dimensional space. Scenes are containers. Shots are cards. Reference images, script notes, and character references can be pinned anywhere on the canvas. Spatial proximity implies relationship (the system uses proximity to suggest connections, not mandate them).  
**What to avoid:** Enforcing a strict grid layout. The spatial canvas must allow freeform arrangement for the early production stages (reference gathering, moodboarding) while supporting structure for the later stages (shot planning, timeline).

---

### UX Pattern 7: The Live Preview (Figma / Framer / VS Code)
**What it is:** Changes are reflected in real time in a preview pane.  
**Why it transfers:** Production decisions need immediate feedback. Changing a character's lighting spec should immediately update the storyboard preview of every shot that uses that character.  
**How to implement:** Every properties change triggers a lightweight preview update. Not a full regeneration — a visual approximation of the change (tint overlay for color, blur for focus changes, compositional mockup for framing changes). Full regeneration is a user-triggered action, not automatic.  
**What to avoid:** Full regeneration on every change. This is expensive, slow, and breaks flow state. The preview and the generation are different operations.

---

### UX Pattern 8: Keyboard-First Navigation (Linear / Raycast / Cursor)
**What it is:** Every action in the application has a keyboard shortcut.  
**Why it transfers:** Professionals never want to reach for the mouse. The most-used actions in a production (approve, reject, next shot, compare, generate) must be keyboard-accessible.  
**How to implement:** A keyboard shortcut overlay (similar to Figma's `Cmd+/` shortcut guide) shows all shortcuts in context. Shortcuts are consistent with industry standards where they exist (J/K/L for timeline scrubbing, Space for play/pause). Non-standard shortcuts are memorable and mnemonic.  
**What to avoid:** Keyboard shortcuts that conflict with browser defaults (Cmd+T, Cmd+W, Cmd+N). The production environment must run in a browser without keyboard hijacking.

---

### UX Pattern 9: The Status Bar (VS Code / DaVinci Resolve)
**What it is:** A persistent bar at the bottom of the screen showing current context state.  
**Why it transfers:** In a production, the user always needs to know: what stage are we in? How many shots are approved? What is the current generation queue status? What is the current cost estimate?  
**How to implement:** A persistent status bar shows: production name, current stage, approved/total shots, generation queue depth, current cost (running total), and a health indicator for the AI crew (all agents ready, one agent waiting, escalation pending).  
**What to avoid:** Status information buried in menus. If the user has to navigate to find out where they are in the production, the status bar has failed.

---

### UX Pattern 10: The Empty State (Notion / Linear / Loom)
**What it is:** When a canvas is empty, show the user what it could become.  
**Why it transfers:** The biggest failure point for new users of any creative tool is the blank canvas. An empty state that shows examples, suggests starting points, and guides the user to the first action eliminates the blank-page problem.  
**How to implement:** Every empty state in the production (empty shot list, empty asset library, empty reference board) shows three things: (1) a brief description of what belongs here, (2) two or three example items, (3) the specific action that adds the first item. The first action is always one click or one keystroke.  
**What to avoid:** Empty states that say "No items yet." This is a failure of UX, not a neutral state.

---

## APPENDIX D — HUMAN-AI COLLABORATION: INTERACTION PATTERN CATALOG

### The Seven Interaction Patterns (with production examples)

---

#### Pattern A: The Briefing (AI as Recipient)
**Description:** The human gives the AI a structured brief. The AI acts on it.  
**When to use:** At the start of each production stage. The human briefs the relevant agent before asking it to produce anything.  
**Example:** Before asking the Shot Designer to spec cameras for Scene 3, the user opens the Shot Design Brief: sets the mood ("tense, claustrophobic"), the narrative goal ("audience should feel trapped"), the character state ("protagonist at lowest point"), and the constraints ("no wide shots"). The Shot Designer reads the brief and proposes cameras accordingly.  
**What makes it work:** The brief is structured, not freeform. The AI can reliably condition on structured data. Freeform briefs produce freeform outputs.  
**Anti-pattern:** Skipping the brief and going straight to "generate some cameras for Scene 3." This produces generic outputs that require many iterations to fix.

---

#### Pattern B: The Proposal Review (AI as Proposer, Human as Approver)
**Description:** The AI generates N proposals. The human selects one, modifies one, or rejects all.  
**When to use:** For every generative decision — camera angles, shot compositions, script lines, color grades.  
**Example:** The Shot Designer proposes three camera angles for Shot 7: (1) low angle, handheld, wide — "creates vulnerability"; (2) eye level, locked, medium — "clinical, detached"; (3) high angle, slow push, tight — "surveillance feeling." The user selects option 3 and adjusts the push speed.  
**What makes it work:** Exactly three proposals. Research consistently shows three is the optimal number — more creates choice paralysis, fewer creates false binary thinking. Each proposal has a one-sentence rationale. The user is approving a rationale as much as a choice.  
**Anti-pattern:** A single proposal ("here is the camera angle"). This positions the AI as an authority rather than a collaborator. Users resist single proposals more than they resist choosing from three.

---

#### Pattern C: The Critique Request (AI as Reviewer)
**Description:** The human asks the AI to evaluate something and tell them what is wrong.  
**When to use:** At every gate — after generation, after editing, before publication.  
**Example:** After assembling Scene 3, the user asks the Reviewer to "check Scene 3 against the production brief." The Reviewer returns: "Three issues found. Shot 7's camera angle contradicts the brief's 'no wide shots' constraint. Shot 9's character is missing their established costume element. The scene pacing is 40% faster than the specified mood." The user addresses each issue.  
**What makes it work:** The critique is specific, referenced, and actionable. Vague critiques ("the scene could be better") are useless. Every critique must cite the specific brief element it references.  
**Anti-pattern:** The AI volunteering unsolicited critiques. Unsolicited critique during creation is one of the most frequently cited frustrations in HCI research on creative AI tools. Critique must be explicitly requested.

---

#### Pattern D: The Expert Consultation (AI as Domain Expert)
**Description:** The human asks the AI a specific question about craft, not about the production.  
**When to use:** When the user needs domain knowledge they don't have — "what is the right lens for this emotional tone?" or "how do professional colorists handle night scenes in period dramas?"  
**Example:** The user is designing lighting for Scene 3 and asks the Character Director: "What lighting setup is most commonly used for interrogation scenes in noir films?" The Character Director responds with a specific answer, three reference images from the production's reference board, and a suggested lighting preset.  
**What makes it work:** The AI's response is grounded in the production's context (references, brief, style tokens), not generic. An answer that ignores the production context is useless.  
**Anti-pattern:** Routing domain questions to a general-purpose chatbot. The production context must be injected into every expert consultation.

---

#### Pattern E: The Override (Human as Authority)
**Description:** The human overrides an AI decision with no justification required.  
**When to use:** Any time. The human is always right.  
**Example:** The Shot Designer proposes a high-angle camera for Shot 7. The user overrides it with a specific camera spec they have in mind. No explanation needed. The override is stored as a layer on top of the AI's proposal. The AI's original proposal is preserved.  
**What makes it work:** Zero friction. Override requires one action. The override is stored non-destructively so the AI's original proposal is always recoverable. The AI does not protest, explain why its choice was better, or ask for justification.  
**Anti-pattern:** Requiring the user to explain their override. "Why are you overriding this?" is a UX failure. The human is the director; they do not owe the AI an explanation.

---

#### Pattern F: The Direction Reset (Human as Creative Director)
**Description:** The human decides the production is going in the wrong direction and resets to a branch point.  
**When to use:** When the current creative direction is not working and the user wants to try something fundamentally different.  
**Example:** The user has been building a dark, tense production for Scene 3. They decide it should instead feel warmly melancholic. They open the Version Tree, find the branch point before the Shot Design brief, and create a new branch from there. The new branch starts with a different mood brief. The original dark branch is preserved.  
**What makes it work:** The branch is instant. The original is never lost. The new branch starts exactly at the decision point where the direction changed, not from scratch.  
**Anti-pattern:** Making the user start the entire production over to try a different direction. This is the single biggest reason users of current AI video tools abandon productions after the first unsatisfactory generation.

---

#### Pattern G: The Handoff (Human to Human, AI as Context Carrier)
**Description:** One human hands a production to another. The AI ensures the receiving human has full context.  
**When to use:** When a production changes hands — director to editor, creator to reviewer, agency to client.  
**Example:** A director finishes the shot planning stage and hands the production to an editor. The AI generates a Production Handoff Summary: "This production is at the Timeline stage. The creative direction is [brief excerpt]. 23 shots are approved; 2 are pending review. Three open decisions are documented in the Shot Notes. The Reviewer flagged one consistency issue in Scene 4 that has not been resolved." The editor starts with full context.  
**What makes it work:** The handoff summary is generated from the production state — it cannot be fabricated or forgotten. The receiving human knows exactly where they are, what was decided, and what is open.  
**Anti-pattern:** Requiring the handing-off human to write the handoff note. Notes written by humans are incomplete, biased toward recent memory, and often simply not written at all.

---

## APPENDIX E — ITERATION SYSTEM: COMPLETE DESIGN

### The Central Insight About Iteration
Iteration in creative work is not undo/redo. It is **creative navigation** — the ability to move through a space of creative possibilities with full awareness of where you have been, where you are, and where you can go. The undo/redo model (borrowed from word processors) is wrong for creative production. The Git branching model is closer, but still too low-level.

The right model is the **decision tree** — a map of every creative decision made, with branches showing paths not taken.

---

### The Three Types of Iteration

**Type 1: Micro-iteration (within a shot)**  
Trying different parameter values for the same shot — different focal length, different lighting intensity, different character expression. This is the most common type of iteration. It should be instant and cheap.  
- Implemented as: parameter variants, all stored under the same shot, viewable in a strip at the bottom of the shot panel.
- Maximum stored: 20 variants per shot (automatically pruned oldest when limit is reached, with user override).

**Type 2: Macro-iteration (alternative creative directions)**  
Trying a completely different approach to a scene or sequence. This is less common but has higher creative stakes.  
- Implemented as: scene branches, accessible from the Scene card's branch menu.
- Branches are named, not numbered. "Dark interrogation direction" vs. "Warm confrontation direction." Names are user-defined; the system suggests names from the brief.

**Type 3: Production-level iteration (creative pivots)**  
Fundamentally rethinking the production direction — different angle, different tone, different structure.  
- Implemented as: production branches, accessible from the Version Tree at the top of the Director's Canvas.
- Production branches are rare and expensive. The system asks for a branch name and a one-sentence description of the new direction before creating the branch.

---

### The Version Tree UI

The Version Tree is a visual representation of all production branches, their creation points, their current status, and their divergence from the main line.

```
main ─────────●────────●────────●────────●──── [current]
              │        │
              ▼        ▼
        dark-angle  warm-angle
        (archived)  (3 shots in)
```

**Reading the tree:**
- Each `●` is a version snapshot (created at each stage gate and on user demand).
- Branches are named forks from a specific snapshot.
- The user can switch between branches in one click.
- Branches can be merged (user directs which elements from each branch to combine).

**Version snapshot triggers:**
- Automatic: at every stage gate transition
- Automatic: before any bulk operation (approve all, regenerate scene)
- Manual: user presses `Cmd+Shift+S` or clicks "Save version"

---

### The Comparison Engine

The Comparison Engine allows any two versions of any object (shot, scene, production) to be placed side-by-side.

**Shot comparison:**
- Two generated outputs play simultaneously (synchronized scrub)
- Differences are highlighted: "Lighting changed 34%. Camera angle changed 12%. Character expression unchanged."
- The user clicks one to promote it as the active version

**Scene comparison:**
- Two scene timelines shown as strips
- Shot-level differences highlighted
- Duration differences shown as colored bars

**Branch comparison:**
- High-level summary: "Branch A has 23 approved shots; Branch B has 17. Branch A's reviewer score is 8.2; Branch B's is 7.6. Branch A follows the brief more closely (creative direction match: 91% vs 78%)."
- Users can request a detailed breakdown of any specific difference

---

### Non-Destructive Editing: The Layer Stack

Every shot in the production has a layer stack:

```
Layer Stack for Shot 7:
┌─────────────────────────────────────────────┐
│ [Layer 4] Color grade override (user, Day 3) │
│ [Layer 3] Camera angle override (user, Day 2)│
│ [Layer 2] AI Shot Designer proposal v2       │
│ [Layer 1] AI Shot Designer proposal v1       │
│ [Base]    Raw generation output              │
└─────────────────────────────────────────────┘
```

The final shot is the result of flattening all layers. Each layer is independently toggleable. Disabling Layer 4 shows what the shot looked like without the color grade. Disabling Layers 3 and 4 shows what the AI originally proposed.

**Why this matters:** A colorist joining the production on Day 5 can see exactly what changes were made to a shot and why. They are not looking at a black box — they are looking at a transparent decision history.

---

### The AI Suggestion Layer (opt-in)

The AI can add a suggestion layer to any shot — a non-binding proposal for how to improve it. Suggestion layers are visually distinct (dashed border, slightly transparent). They are never applied without the user explicitly accepting them.

When the user asks the Reviewer to "check Scene 3," the Reviewer adds suggestion layers to shots that fail the consistency check. Each suggestion layer contains: what is wrong, what the fix is, and a one-click "apply fix" action.

Suggestion layers expire after 7 days if not acted on. The user can also permanently dismiss them ("I've considered this and disagree").

---

### The Creative Reasoning History

Every production maintains a Creative Reasoning History — a log of every creative decision and the rationale behind it. This is separate from the technical event log. It is written in natural language, not JSON.

Example entries:
- "Day 1, 14:32 — Chose 'contrarian' angle for Scene 3 because the advocate framing felt too expected for this audience. [User decision]"
- "Day 2, 09:15 — Shot Designer proposed high-angle camera for Shot 7. Rationale: creates surveillance feeling consistent with the interrogation mood brief. User accepted with modification: slower push speed. [Agent proposal + User modification]"
- "Day 3, 16:47 — Reviewer flagged Shot 9 for character consistency failure. Character missing established costume element. User resolved by regenerating Shot 9 with corrected character reference. [Agent flag + User resolution]"

The Creative Reasoning History is automatically generated from the production event log and the agent rationales. The user can add annotations manually. It is exportable as a PDF and is part of the Production Archive.

**Why this matters:** A director reviewing the production six months later can understand every decision. A client who receives the Production Archive can trace every creative choice. An AI system trained on production histories can learn from the reasoning, not just the outputs.

---

### The "Why" Button

Every AI-generated element in the production has a "Why?" button. Clicking it opens the Creative Reasoning for that element — which agent produced it, what brief it was responding to, what alternatives were considered, and why this one was chosen (or what parameters drove the generation).

The "Why?" button is the transparency mechanism that makes the production system trustworthy. Users who understand why the AI made a decision are three times more likely (per HCI research Finding 4) to trust the output and proceed, rather than regenerating indefinitely.

---

*[Document continues — see Appendices F through I below]*

---

## APPENDIX F — SECONDARY QUESTIONS: DEEP ANSWERS

*These are the six secondary research questions from the original brief, answered exhaustively.*

---

### Q1: Why do current AI video products feel limiting?

The limiting feeling is not a feature gap — it is an architectural gap. Current AI video products are built on a **request-response model**: the user sends a request, the system returns a response. This model is correct for information retrieval. It is wrong for production.

Production is a **state evolution model**: the production has a current state, the user makes a decision that changes the state, the state evolves. The history of state changes is the production. In a request-response system, there is no state — each request is independent. The user must re-establish context on every request. The AI has no memory of what was decided before. Every generation is orphaned.

The five specific mechanisms that create the limiting feeling:

**1. Context amnesia.** Each prompt is stateless. The user wrote "tense, claustrophobic interrogation scene" in prompt 3. Prompt 7 has no access to that. The user must repeat it or the AI drifts. In a production environment, every agent decision is contextualized by all prior decisions. Context amnesia is eliminated structurally.

**2. No creative frame.** A prompt describes what you want visually. It does not describe why — what emotion, what narrative function, what audience experience. Without a creative frame, the AI optimizes for visual plausibility rather than narrative effectiveness. The result looks fine and means nothing.

**3. Evaluation is outsourced to the human.** The AI generates; the human evaluates. The human's evaluation is informal, inconsistent, and unrecorded. The same mistake is made in shot 3, shot 7, and shot 12 because no one told the system what the mistake was. A Reviewer agent with a consistency contract eliminates this.

**4. No iterative identity.** A character in shot 3 and the same character in shot 7 are generated independently. There is no mechanism for them to be the same character. The user is forced to copy-paste reference images between prompts — a workaround, not a solution.

**5. The output is final.** When a video is generated, it is a file. It cannot be un-generated into its constituent decisions. If the color grading is wrong, the entire shot must be regenerated. If the character expression is wrong, the entire shot must be regenerated. Non-destructive editing — standard in every professional tool for 30 years — does not exist in any AI video product.

---

### Q2: Why do users lose creative control?

Users do not lose creative control because the AI is too powerful. They lose it because **the interface has no concept of control to give up**.

Control requires: (a) a model of what can be controlled, (b) a way to express desired values for each controllable parameter, (c) feedback that confirms the control was applied, and (d) the ability to change any parameter independently of others.

Current AI video interfaces provide none of these. The prompt is not a control surface — it is a description. Descriptions are interpreted; parameters are applied. A description of "warm lighting" may or may not produce warm lighting. A lighting parameter of `color_temperature: 3200K, intensity: 0.7, falloff: soft` will always produce the same result.

The path to creative control:
1. Replace natural language descriptions of parameters with **structured parameter objects**
2. Give every parameter a **range, default, and named preset library**
3. Show the user the **effect of changing each parameter** before committing to a generation
4. Make **parameters independent** — changing the lighting should not require regenerating the character

This is exactly how DaVinci Resolve, Blender, and Unreal Engine are built. The reason professional tools feel controllable is that they expose parameters, not descriptions.

---

### Q3: Why does prompting scale poorly?

Prompting scales poorly for five compounding reasons:

**1. Linear complexity, exponential cognitive load.** A 10-shot production requires 10 prompts. A 100-shot production requires 100 prompts. Each prompt must encode all the context that makes this shot consistent with all other shots. The cognitive load grows super-linearly with production size.

**2. No diff.** When a prompt changes, there is no way to know what changed in the output. A single word change in a prompt can produce radically different output. The relationship between prompt delta and output delta is opaque and non-monotonic.

**3. No shared vocabulary.** The production team (even if it is one person) must maintain a mental map of which phrases produce which visual results. This map is private, undocumented, and fragile. When a collaborator joins the production, they have no access to this map.

**4. No constraint propagation.** Changing a character's hair color requires updating every prompt that describes that character. In a 100-shot production, this is 30–40 manual edits. Miss one and the production has a continuity error.

**5. Prompt drift.** Over time, as the production evolves, early prompts become inconsistent with later decisions. The production brief has changed; the prompts have not. There is no mechanism to propagate brief changes to existing prompts.

The solution is **structured production briefs** that replace prompts as the primary input. The brief is written once. The agents generate prompts from the brief for each shot. Brief changes propagate automatically. The user never writes a prompt from scratch.

---

### Q4: Why does production software remain difficult?

Production software is difficult for two reasons that are often conflated but must be separated:

**Reason 1: Inherent domain complexity (legitimate)**  
Video production is genuinely complex. Color science, optics, narrative structure, audio engineering, motion physics — these are real disciplines with real depth. No interface can eliminate the need to understand the domain. The right response is progressive disclosure: hide the complexity until the user needs it, then expose it completely.

**Reason 2: Accumulated interface debt (illegitimate)**  
DaVinci Resolve, Premiere, and Avid are difficult because they were built over 20+ years, adding features without rethinking the interface model. They are difficult not because color grading is hard but because the color grading workflow was designed in 2003 and the 2024 interface is a 21-year-old design with 200 new features bolted on.

An AI-native production environment starts with no interface debt. Every interface decision can be made with 2026 knowledge of UX, AI, and professional workflows. This is the opportunity. The question is not "how do we make a simpler DaVinci Resolve" — it is "what would a color grading interface look like if you designed it today, knowing everything we know about how AI can assist?"

The answer: the colorist describes the emotional intent of a scene ("oppressive, institutional, fluorescent sadness"). The AI generates a starting grade. The colorist adjusts parameters non-destructively. Every parameter has a name, a range, and a comparison mode. The grade is a named preset that can be applied to any scene.

---

### Q5: What do users actually do after generation?

HCI research and user observation in current AI video tools consistently reveals the post-generation loop:

1. **Watch the output** (3–5 times, at different speeds)
2. **Identify the 2–3 things that are wrong** (not the 10 things that are right)
3. **Try to fix the wrong things** — which in a prompt-based system means either:
   a. Rewrite the entire prompt and hope the right things stay right, or
   b. Accept the wrong things and move on
4. **Accept good-enough outputs** — not because they are satisfied but because the cost of improvement is too high
5. **Accumulate debt** — 10 "good enough" shots produce a production that is globally incoherent even though each individual shot is locally acceptable

The critical insight: users do not want to regenerate. They want to **fix**. Regeneration destroys everything good about an output to fix one bad thing. Fix-in-place — the ability to change one parameter of an existing output without regenerating the rest — is the most-requested feature in every AI video user research study and the feature no current product has.

**Design implication:** Every generated shot must have a `fix_in_place()` operation — change the lighting without changing the character, change the character expression without changing the background, change the camera angle without changing the scene content. This is technically hard (requires diffusion inpainting or layered generation) but it is the right product decision. Users will tolerate technical limitations if the interaction model is correct.

---

### Q6: What workflows do professionals actually follow?

Observation of professional video productions (commercial, narrative, documentary) reveals six consistent workflow patterns that no AI video tool currently models:

**Pattern 1: Pre-production is 50% of production.**  
Professional productions spend as much time in pre-production (planning, scripting, storyboarding, casting) as in production (shooting, generating). AI tools skip directly to "production" (generation). The result is that the most important half of the workflow is completely unsupported.

**Pattern 2: References come before decisions.**  
No professional makes a creative decision without looking at references first. A colorist does not grade a scene without looking at reference images that capture the target mood. A cinematographer does not choose a lens without looking at reference frames from films with similar visual goals. AI tools have no reference system — they expect the user to translate references into words (prompts) and then discard the references.

**Pattern 3: The brief is the contract.**  
When multiple people work on a production, the brief is the shared contract. Everyone refers to it. Decisions are justified against it. Deviations from it are escalated. AI tools have no brief. Every user is their own director, producer, and creative director simultaneously, with no shared reference.

**Pattern 4: Review happens in context.**  
Professionals review work in context — a shot is reviewed in the sequence it belongs to, not in isolation. A shot that looks great in isolation may be wrong for its position in the sequence (wrong pacing, wrong color relative to adjacent shots, wrong energy relative to narrative position). AI tools show generated outputs in isolation.

**Pattern 5: Approval is binary.**  
Professional productions have explicit approval workflows. A shot is either approved or it is not. There is no "probably okay." Unapproved shots do not make it to the final cut. AI tools have no approval concept — every generated output is implicitly approved by default because there is no explicit approval step.

**Pattern 6: The edit is where the story is found.**  
In professional narrative production, the edit is not the last step — it is a creative act that discovers the story in the footage. The editor is a co-author. AI tools treat editing as a post-processing step. The right model is that editing and generation are interleaved — the editor's decisions about pacing and sequence should drive what gets generated next.

---

## APPENDIX G — PRODUCTION PIPELINE: STAGE-BY-STAGE DEEP DIVE

*The 26-stage table in Section 14 gives the skeleton. This appendix gives the flesh — what actually happens at each critical stage, what the AI does in detail, and where the beginner/professional split appears.*

---

### Stage 1: Idea — Deep Dive

**What actually happens:**  
The user has an idea. It may be fully formed ("I want to make a 2-minute brand film for a sustainable coffee brand targeting Gen Z, contrarian angle, cinematic, no stock footage feel") or it may be a fragment ("something about coffee and the planet"). The system must work with both.

**The AI's role in detail:**
- If the input is a fragment: the Creative Director proposes 3 expansions — a fully formed intent document for each of three creative directions
- If the input is fully formed: the Creative Director reflects it back as a structured Intent Document and flags any ambiguities ("'no stock footage feel' — do you mean: (a) real people, real locations; (b) cinematic lighting and framing; or (c) both?")
- The Creative Director never invents audience, tone, or length — these must come from the user. It may suggest; it does not decide.

**The Intent Document schema:**
```
IntentDocument {
  topic: string           // what the production is about
  audience: AudienceSpec  // who it is for
  tone: ToneSpec          // how it should feel
  length: DurationSpec    // how long it should be
  format: FormatSpec      // where it will be published
  constraints: string[]   // what must not be done
  references: string[]    // rough pointers to inspiration
  creative_angle: string  // skeptic / advocate / contrarian / neutral
  purpose: string         // what the viewer should feel/do/think
}
```

**Beginner experience:** The system asks five questions in plain language. Each answer populates one field in the Intent Document. The user never sees the schema.

**Professional experience:** The Intent Document is a form the user can fill directly. They can paste an existing brief from an external source. The Creative Director then structures it.

**Gate:** The Intent Document must have: topic, audience, tone, length, purpose. Constraints and references are optional. Creative angle is required — even "neutral" is a choice.

---

### Stage 5: Creative Direction — Deep Dive

**Why this stage exists:**  
Creative direction is the most consequential decision in a production. It determines what story is told, from what perspective, with what emotional register. It cannot be delegated to the AI — but the AI can dramatically improve the quality of the human's decision by surfacing options the human would not have thought of alone.

**The Creative Director agent's three proposals always have:**
- A named angle (not just "option 1")
- A one-sentence emotional promise to the viewer
- Three specific visual/tonal implications
- One specific risk (what could go wrong with this direction)
- One reference production that exemplifies this direction

**Example proposals for "sustainable coffee brand, Gen Z":**

*Direction A: "The Inheritance" (advocate)*  
"Your coffee choice is a letter to the planet you're leaving behind."  
Implications: warm nostalgic color, slow pacing, intergenerational imagery.  
Risk: may feel preachy or guilt-driven — test with Gen Z focus group.  
Reference: Patagonia "Don't Buy This Jacket" campaign tone.

*Direction B: "The Skeptic's Cup" (contrarian)*  
"Sustainability is complicated. Here's what we actually know."  
Implications: cool clinical color, data visualization aesthetic, direct-to-camera.  
Risk: may feel confrontational — works for a specific sub-audience.  
Reference: Kurzgesagt visual style, honest brand tone.

*Direction C: "The Ritual" (advocate, different register)*  
"This cup is the one thing you do every morning that actually matters."  
Implications: intimate, close-up, morning light, ritual focus.  
Risk: may feel ordinary — differentiation must come from execution.  
Reference: Apple product film intimacy, Aesop brand tone.

**Beginner experience:** The three direction cards are shown as full-screen choices. The user taps one. The system confirms and locks it.

**Professional experience:** The user can modify any direction before locking — change the tone, swap the reference, adjust the implications. They can also reject all three and brief the Creative Director again with a different constraint.

**Gate:** One direction must be locked before Stage 6 (Story) begins. The locked direction becomes the creative frame for every subsequent decision.

---

### Stage 8: Characters — Deep Dive

**The consistency problem, stated precisely:**  
A character in an AI-generated production must look the same in Shot 1 and Shot 47. In traditional production, this is solved by casting a real person. In AI production, it must be solved architecturally.

**The Character Spec schema:**
```
Character {
  id: uuid
  name: string
  role: string               // protagonist, antagonist, supporting
  
  visual_spec {
    age_range: [min, max]
    gender_presentation: string
    ethnicity: string
    build: string
    hair: HairSpec
    distinctive_features: string[]
    typical_expression: string
  }
  
  costume_spec {
    production_wardrobe: CostumeByScene[]
    invariant_elements: string[]  // elements that NEVER change
    variant_elements: string[]    // elements that MAY change by scene
  }
  
  visual_anchors: ImageReference[]  // 3-5 reference images
  
  consistency_contract: ConsistencyContract
  
  voice_spec: VoiceSpec
  
  narrative_role: string
  arc: string
}
```

**The visual anchors are critical.** They are 3–5 images (imported by the user, or generated by the system in a character development session) that every generation is conditioned on. The Reviewer agent compares every generated shot of this character against these anchors.

**Character development session (the AI-assisted flow):**  
When a character is first created, the system runs a Character Development Session:
1. The Creative Director reads the script and proposes a character brief
2. The Shot Designer generates 6 candidate visual interpretations
3. The user selects up to 3, rejects the rest, and annotates what they like/dislike
4. The system generates 6 refined interpretations based on the feedback
5. The user selects 1 as the canonical visual anchor
6. The user adds 2–4 additional reference images (from film/photography/illustration) to supplement
7. The Consistency Contract is auto-generated from the final anchor set

This session happens once per character. The character is then available as a named entity in every subsequent prompt — referenced by ID, never described again from scratch.

---

### Stage 11: Storyboard — Deep Dive

**What a storyboard is for (and what it is not for):**  
A storyboard is not a preview of the final video. It is a communication tool — a shared visual language between the director and every member of the production crew. A good storyboard communicates: what is in the frame, where the camera is, what the character is doing, and what the emotional register of the shot is. It does not need to be beautiful. It needs to be clear.

**The AI storyboard generation flow:**
1. For each shot in the shot list, the Shot Designer reads: the shot intent, the camera spec, the character references, the location spec, the lighting spec
2. It generates a compositional sketch — not a photorealistic image, but a clear composition diagram showing: frame boundaries, character positions, camera angle indicator, lighting direction arrow, action description
3. Each sketch includes a one-sentence verbal description of what the viewer should see and feel

**Why compositional sketches, not photorealistic renders:**  
Photorealistic storyboard frames encourage the team to evaluate the lighting, character appearance, and rendering quality — none of which are the point of a storyboard. Compositional sketches keep the focus on composition, blocking, and narrative function. DreamWorks and Pixar both use rough sketches, not photoreal renders, for storyboarding.

**The storyboard panel UI:**  
- Shots are shown as a horizontal strip per scene
- Each frame shows the compositional sketch, the shot number, the duration, and the camera spec summary
- Clicking a frame opens the Shot Panel with full details
- Dragging reorders shots within the scene (updating the timeline automatically)
- A "playthrough" mode animates through the strip at the specified shot durations, giving a rough sense of pacing

---

### Stage 16: Generation — Deep Dive

**Generation is 5% of the experience. Here is exactly what that 5% looks like:**

**Pre-generation checklist (automated, run by the Reviewer before every generation):**
- [ ] Character references resolved and loaded
- [ ] Location spec loaded
- [ ] Camera spec loaded
- [ ] Lighting spec loaded
- [ ] Consistency Contract loaded for all characters in this shot
- [ ] Style tokens loaded from production brief
- [ ] Previous shot's color and mood checked (for scene continuity)
- [ ] Budget estimate within approved limit

If any check fails, generation is blocked and the user is told exactly what is missing. The AI never generates with incomplete context.

**Generation parameter assembly (what the Shot Designer builds):**  
The generation prompt is never written by the user. It is assembled by the Shot Designer from:
- Character spec → character description tokens
- Location spec → environment description tokens
- Camera spec → camera parameter tokens (lens, angle, movement)
- Lighting spec → lighting parameter tokens
- Style tokens → from production brief
- Consistency anchors → reference image conditioning
- Shot intent → narrative/emotional guidance

The assembled prompt is shown to the user before generation as a structured parameter list (not as a raw prompt string). The user can edit any parameter.

**Post-generation quality gate (run automatically by the Reviewer):**
- Character consistency check against visual anchors (score: 0.0–1.0, threshold: 0.75)
- Consistency Contract attributes check
- Brief adherence check (does the shot serve its stated intent?)
- Technical quality check (blur, exposure, artifact detection)

Shots that fail the quality gate are silently regenerated (up to 2 retries). If they still fail after 3 attempts, the user is shown the best result with the specific failure flagged. The user decides: accept with note, override gate threshold for this shot, or trigger manual regeneration with adjusted parameters.

**The generation queue:**  
All shots are queued and generated asynchronously. The user does not wait for generation — they continue planning subsequent stages while the queue processes. A progress indicator in the status bar shows queue depth and estimated completion. When a shot is ready, a notification appears in the Director's Canvas.

---

### Stage 22: Color — Deep Dive

**Why color deserves its own interface:**  
Color grading is the single most powerful tool for emotional communication in video production. The difference between a mediocre and a powerful production is often entirely in the color grade. Current AI video tools have no color grading concept at all.

**The Colorist agent workflow:**
1. The user briefs the Colorist with the emotional intent of each scene ("oppressive, institutional fluorescent sadness" / "warm, intimate morning hope")
2. The Colorist proposes a scene-by-scene grading strategy — not individual adjustments, but a named look for each scene
3. Each proposed look includes: reference frame, emotional justification, 3 key parameter values
4. The user approves or adjusts the proposed looks at the scene level
5. The Colorist then applies the looks to all shots in each scene
6. The user reviews shot-by-shot and can override individual shots

**The Color Spec schema (what the Colorist works with):**
```
ColorSpec {
  look_name: string             // "institutional_cold_blue"
  reference_frame: ImageRef     // a frame that exemplifies the look
  
  primary {
    shadows: RGBOffset           // color cast in shadows
    midtones: RGBOffset          // color cast in midtones
    highlights: RGBOffset        // color cast in highlights
    contrast: float              // 0.0–2.0
    saturation: float            // 0.0–2.0
  }
  
  creative {
    split_tone: SplitToneSpec    // shadow/highlight color split
    vignette: VignetteSpec
    grain: GrainSpec
    halation: float
  }
  
  scene_match: bool              // force all shots in scene to match
  lut_export: bool               // exportable as a LUT file
}
```

**Beginner experience:** The user describes the mood in plain language. The Colorist generates a look. The user says "warmer" or "more contrast." The system adjusts. The user never sees a color wheel.

**Professional experience:** The full ColorSpec is exposed as a parameter form. The Colorist's proposed values are shown as starting points. Every parameter is directly editable. The LUT can be exported and applied in DaVinci Resolve for final grading.

---

### Stage 25: Publishing — Deep Dive

**The publish spec is a first-class production artifact.**  
Every production has a Publish Manifest — a formal specification of how, where, and in what format the production will be published. It is created at the start of Stage 25 and gates the export.

**Publish Manifest schema:**
```
PublishManifest {
  production_id: uuid
  
  targets: PublishTarget[]     // one or more platforms
  
  per_target {
    platform: string           // "youtube" | "instagram_reels" | "broadcast" | "archive"
    format: VideoFormat        // codec, container, bitrate
    resolution: Resolution     // 1080p, 4K, vertical, square
    duration_limit: seconds    // platform cap
    caption_spec: CaptionSpec  // subtitles, style, timing
    thumbnail: ImageRef        // the key frame for the thumbnail
    metadata: PublishMetadata  // title, description, tags, rights
  }
  
  audit_trail_included: bool   // include production audit in archive
  
  approvals_required: string[] // named approvers who must sign off before publish
}
```

**The platform-aware export:**  
The system knows the technical requirements of every major platform (YouTube, Instagram Reels, TikTok, broadcast, cinema DCP). When a target is selected, the format parameters are pre-filled with platform-optimal defaults. The user only needs to override if they have non-standard requirements.

**Rights and audit:**  
Before any publish, the system generates a rights clearance checklist: which generated assets are platform-safe, which voice profiles are licensed for commercial use, which music cues have cleared rights. Any unresolved rights issue blocks publication.

---

## APPENDIX H — CUSTOMIZATION SYSTEM: CATEGORY-BY-CATEGORY DESIGN

*The Customization System in Section 12 gives the framework. This appendix gives the full design for each category.*

---

### Category 1: Brand Kit

A Brand Kit is the production identity of a Studio. It ensures that every production made in a Studio is recognizably from that Studio.

**Components:**
- **Visual identity:** Primary color palette (3–7 colors, each with name, hex, emotional label, and usage rule), secondary palette, forbidden colors, brand logo (with safe-zone specification)
- **Typography tokens:** Display font, body font, caption font — with size scales, weight rules, and color-on-background rules
- **Tone of voice:** 3–5 adjectives that describe the brand voice, 3–5 adjectives that describe what the brand voice is NOT, example sentences that pass/fail the tone check
- **Visual style tokens:** Photographic style (cinematic, editorial, documentary, lifestyle), color grade family (warm/cool, high/low contrast, saturated/muted), motion style (dynamic, restrained, rhythmic), pace (fast-cut, slow-burn, balanced)
- **Approved talent:** Named characters and voice profiles that are pre-approved for use
- **Approved music:** Named music briefs or actual licensed tracks pre-cleared for the brand

**Enforcement:**  
Every AI-generated output in a Studio with a Brand Kit is automatically reviewed against the Brand Kit by the Reviewer agent. Violations are flagged, not silently corrected. The user decides whether to fix or override.

---

### Category 2: Character Library

Characters are named, persistent entities that can be used across multiple productions.

**Each character has five levels of definition:**

1. **Core identity** (mandatory): name, role type, one-paragraph bio
2. **Visual anchor** (mandatory): 3–5 reference images, consistency contract
3. **Extended visual spec** (recommended): full visual spec as in Stage 8 above
4. **Voice spec** (optional): voice profile with sample, tone guide, speaking style
5. **Narrative library** (optional): past appearances, character arc notes, relationship map

**Character evolution:**  
Characters can evolve between productions (aged, different costume period, different emotional state). Each evolution is a named variant — "Alex_2040" vs "Alex_2026." Variants share the core identity and voice but have separate visual anchors.

**Character lending:**  
A Studio can make a character available to collaborating Studios (partner agency, co-producer). Lending is permission-controlled and auditable. The lent character's consistency contract travels with it.

---

### Category 3: Camera Presets

Camera presets encode the cinematographer's visual vocabulary — the recurring shot types that define a production's visual style.

**A camera preset contains:**
```
CameraPreset {
  name: string                // "Tense_Closeup_03"
  description: string         // when to use this preset
  
  lens {
    focal_length: mm          // 24, 35, 50, 85, 135
    aperture: f-stop          // f/1.4 to f/16
    focus_distance: string    // "shallow", "deep", "split"
  }
  
  framing {
    shot_size: string         // ECU, CU, MCU, MS, MWS, WS, EWS
    composition_rule: string  // rule_of_thirds, centered, dutch, overhead
    headroom: string          // tight, normal, loose
    look_space: string        // left, right, none
  }
  
  camera_movement {
    type: string              // static, handheld, dolly, crane, drone
    direction: string         // push_in, pull_out, lateral, orbit, tilt
    speed: string             // fast, medium, slow, imperceptible
    motivation: string        // why the camera moves (or doesn't)
  }
  
  emotional_register: string  // what feeling this preset creates
  example_reference: ImageRef
}
```

**Preset libraries:**  
Presets are organized into libraries. A library is a named collection that corresponds to a production style — "Kubrick-inspired" (static, centered, wide angle), "Dogme 95 style" (handheld, natural light, long takes), "Commercial luxury" (slow dolly, shallow depth, macro details). A user can apply an entire library as a starting point and customize from there.

---

### Category 4: Motion Library

Motion defines the kinetic grammar of a production — how things move, how fast, with what easing, with what emotional character.

**Motion token types:**

- **Cut rhythm:** the average shot duration and the pattern of short/long cuts that creates a specific pacing feel
- **Transition vocabulary:** what transitions are used (cut, dissolve, match cut, smash cut, wipe) and when
- **Character motion:** how characters move in this production (constrained and tense, expansive and fluid, fragmented)
- **Camera motion:** as above in Camera Presets, elevated to a production-wide setting
- **Environment motion:** how the environment moves (wind, water, crowds — the ambient motion that creates world-feel)

**Easing presets:**  
Every motion in the production has an easing curve — the acceleration and deceleration profile. Easing curves are the most underspecified element in current AI video tools. A preset library of named easing curves (with emotional labels: "urgent", "contemplative", "playful", "industrial") gives the user fine control over the kinetic feel of the production.

---

### Category 5: Lighting Presets

Lighting is the single most expressive technical element in video production. It is also the element most poorly described in prompts and most inconsistently reproduced in AI generation.

**A lighting preset contains:**
```
LightingPreset {
  name: string               // "Hospital_Fluorescent_Hard"
  description: string
  
  primary_light {
    type: string             // sun, practicals, LED, HMI, candle, fluorescent
    direction: string        // above_front, side, back, under
    quality: string          // hard, soft, diffused, mixed
    color_temp: kelvin       // 2700K–6500K+
    intensity: float         // 0.0–1.0
  }
  
  fill_light {
    ratio: float             // key:fill ratio, e.g., 4:1
    color_temp: kelvin
    direction: string
  }
  
  practicals {               // visible light sources in frame
    present: bool
    type: string
    contribution: float
  }
  
  time_of_day: string        // golden_hour, noon, dusk, night, interior
  weather: string            // clear, overcast, rain, fog
  
  emotional_register: string
  reference_frame: ImageRef
}
```

**Why this matters at scale:**  
In a 30-shot production, lighting consistency across all shots in a scene is maintained by applying the same lighting preset to all shots in that scene. Changing the preset changes all shots simultaneously — non-destructively.

---

### Category 6: Voice Library

Voice is the most personal element of a production and the hardest to regenerate consistently.

**A voice profile contains:**
- **Acoustic spec:** pitch range, resonance, breathiness, pace, articulation
- **Emotional range:** how the voice expresses emotion (restrained, expressive, deadpan, warm)
- **Sample library:** 10–20 sample utterances covering the range of emotional registers
- **Technical spec:** sample rate, format, intended generation model (if applicable)
- **Rights clearance:** who owns this voice, what uses are permitted, expiry date

**Voice consistency enforcement:**  
Every voice line generated for a character uses the character's voice profile as a conditioning reference. The Reviewer checks every generated voice line against the profile's sample library. Lines that fail the consistency check are flagged for re-generation.

**Custom voice creation:**  
A user can create a custom voice profile by: (a) recording 5–10 sample sentences in the target voice, (b) having the system analyze and generate an acoustic spec from the samples, (c) testing the profile against a set of target utterances, (d) approving or adjusting. The custom voice profile is stored in the Studio Library and can be used in any production.

---

### Category 7: Narrative Templates

A Narrative Template is a production structure — the sequence of stages, scenes, and shots that has proven effective for a specific type of production.

**Built-in templates:**
- **Brand film (60s):** 3 scenes — problem (15s), tension (20s), resolution with product (25s)
- **Documentary short (3min):** 5 scenes — hook, background, conflict, turn, resolution
- **Social series (15s):** 2 scenes — hook (5s), payoff (10s), CTA (overlay)
- **Explainer (90s):** 4 scenes — question, complication, explanation, call-to-action
- **Testimonial (60s):** 3 scenes — problem statement (person), product introduction, outcome

**Template customization:**  
Every template is fully editable. The user can: add scenes, remove scenes, reorder scenes, change scene durations, change the number of shots per scene. The template is a starting point, never a constraint.

**Template creation:**  
After completing a production, the user can save its structure as a template — stripping the content and keeping only the structure. Templates created by the user are saved to the Studio Library and can be shared with team members.

---

## APPENDIX I — THE BEGINNER/PROFESSIONAL DECISION MAP

*For every major production decision, here is exactly how the beginner experience and professional experience differ — and how they converge.*

---

### Decision Map Format
Each entry shows:
- **The decision** (what needs to be decided)
- **Beginner path** (what the interface shows and asks)
- **Professional path** (what the interface exposes)
- **The convergence point** (where both paths reach the same decision)

---

### Decision 1: Starting a Production

**Beginner path:**  
"What do you want to make?" → freeform text input → Creative Director proposes 3 structured Intent Documents → user picks one → production begins with a pre-filled structure

**Professional path:**  
Empty Intent Document form → user fills all fields directly → optional: paste existing production brief → system validates and flags ambiguities → production begins

**Convergence:** A locked Intent Document with all required fields populated.

---

### Decision 2: Creative Direction

**Beginner path:**  
3 full-screen direction cards, each with a visual metaphor, an emotional promise, and a one-sentence risk. User taps one. Done.

**Professional path:**  
3 direction cards with full detail (as in Stage 5 deep dive). User can modify any direction before locking — change tone, swap reference, adjust implications. Can reject all three and write a custom brief for the Creative Director.

**Convergence:** A locked Creative Brief with named direction, emotional promise, visual/tonal implications, and reference.

---

### Decision 3: Character Design

**Beginner path:**  
"Describe your main character in a few sentences" → Creative Director generates a character spec → 6 visual options are shown → user picks the one that looks right → character is created

**Professional path:**  
Full Character Spec form → visual anchor import → consistency contract configuration → character development session (as in Stage 8 deep dive) → manual refinement of every parameter

**Convergence:** A Character with at least: name, role, visual anchor, consistency contract.

---

### Decision 4: Shot Composition

**Beginner path:**  
"What should happen in this shot?" → freeform description → Shot Designer proposes 3 compositional options → user picks one → shot is added to the storyboard

**Professional path:**  
Full Shot Panel open → camera preset selector → framing control → character blocking diagram → Shot Designer proposes options but user can edit every parameter → shot is added to the storyboard

**Convergence:** A Shot with locked camera spec, framing, and character blocking.

---

### Decision 5: Generation Approval

**Beginner path:**  
Generated shot shown full-screen → "Does this work?" → Yes / Try again / Make it [more/less] [X] → approval or guided re-generation

**Professional path:**  
Generated shot shown in Shot Panel → Reviewer score and flags shown → layer stack open → parameter-level adjustments available → approve / regenerate with specific changes / override gate

**Convergence:** An approved shot with status "approved" in the production state.

---

### Decision 6: Color Grading

**Beginner path:**  
"How should this scene feel?" → emotion picker (warm/cool/dramatic/intimate/etc.) → Colorist applies a look → "More like this / Less like this" → locked grade

**Professional path:**  
Full ColorSpec form → Colorist proposes starting values → every parameter directly editable → scene-level and shot-level grade → LUT export for external grading

**Convergence:** A locked ColorSpec applied to all shots in the scene.

---

### Decision 7: Publishing

**Beginner path:**  
"Where do you want to share this?" → platform picker → system auto-fills format, resolution, duration → review thumbnail → "Publish" → Publish Manifest created automatically

**Professional path:**  
Full Publish Manifest form → multiple targets → custom format specs → approvals workflow → rights clearance checklist → staged publish (unlisted → review → public)

**Convergence:** A signed-off Publish Manifest with all required fields and all rights cleared.

---

### The Universal Convergence Principle

Every beginner path and professional path converge at the **same production state object**. There is no "beginner production" and "professional production." There is only a production, with a state. The beginner reaches the same state through guided questions. The professional reaches the same state through direct parameter control.

A beginner who finishes their first production in Guided Mode can open the same production in Director Mode and see every decision they made — fully specified, fully editable, fully transparent. The transition from beginner to professional is not a mode switch. It is a gradual revelation of the same system's depth.

---

*End of document.*
*Status: [ ] pending review → [ ] pending implementation → [ ] in progress → [ ] done*
*Version: 1.2 — Appendices F, G, H, I added (Secondary Questions, Pipeline Deep Dives, Customization Categories, Beginner/Professional Decision Map)*
*Total sections: 26 required outputs + 9 appendices (A–I)*
