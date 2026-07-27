# Demo Story — Open Production

**Duration:** ≤ 3 minutes (cap: 3:00).
**Recorded:** Day 3, after `make demo` runs cleanly from a fresh clone.
**Published:** YouTube, unlisted then public.
**Purpose:** communicate all five judging criteria in 180 seconds.

---

## Shot list — second-by-second

### 0:00–0:15 — Title card

**Visual:** Open Production logo (the 🪷 lotus mark). Tagline: *"AI as a creative partner for long-form content."*

**Voiceover:** "Open Production — built with IBM Bob. AI as a creative partner for research writing."

**Criterion:** none yet — set the frame.

---

### 0:15–0:35 — Problem statement

**Visual:** A mock "thesis deadline" graphic. Clock ticking. Student staring at a blank page. Failed citations highlighted in red.

**Voiceover:** "Every creator knows the bottleneck — research is slow, citations break, drafts contradict themselves, deadlines force shortcuts that lose trust."

**Criterion:** **Real-World Impact.** Sets the human stakes.

---

### 0:35–1:05 — Architecture in one shot

**Visual:** Show the Mermaid diagram at `docs/architecture/architecture-diagram.mmd`. Highlight the five primitives, the creative reframing subgraph, and the three fail-closed gates. Cursor traces the path: Intent → Reframing → Research → Gates → Output.

**Voiceover:** "Open Production runs five stages. You declare an intent. The system proposes three creative angles. You pick one. Four academic agents research in parallel. Three fail-closed gates — evidence, consistency, publication — refuse to publish anything untraceable."

**Criterion:** **Technical Execution** + **Challenge Fit.** Kernel depth in 30 seconds.

---

### 1:05–1:45 — The creative reframing moment

**Visual:** Live screen capture. Browser demo at `http://127.0.0.1:8000/`. The creative-reframing agent runs after the topic is submitted. Three angle cards appear: **skeptic / advocate / contrarian**. Cursor clicks "contrarian."

**Voiceover:** "Watch the reframing — the system proposes skeptic, advocate, contrarian. I pick contrarian. That's the AI as creative partner move: the system doesn't generate content unilaterally, it proposes alternatives and lets me decide."

**Criterion:** **Innovation.** The differentiator. The rubric's exact framing.

---

### 1:45–2:20 — Multi-agent research + gates

**Visual:** Browser result panel. The accepted / rejected / contradiction counts update, and the audit trail scrolls below. If you want a quick terminal cutaway, show `audit_trail.jsonl` in a side window.

**Voiceover:** "Multi-agent research hits four academic APIs in parallel. The evidence gate rejects a claim without a citation. The consistency gate surfaces a contradiction. The publication gate halts because the DOI is missing. Fail-closed: every gate refuses to publish anything untraceable."

**Criterion:** **Feasibility** + **Technical Execution.** Live, working, not a slide.

---

### 2:20–2:50 — Output + audit trail

**Visual:** The PDF opens. Scroll through the document — every claim has a footnote linked to a source. Open `audit_trail.json` in another pane — the full query/response/claim/rejection log.

**Voiceover:** "Result: a finished, citable PDF. Every sentence traces back to a source. The audit trail is auditable — every query, every claim, every gate decision is recorded."

**Criterion:** **Feasibility** + **Real-World Impact.** The deliverable is real.

---

### 2:50–3:00 — Closing + Bob usage

**Visual:** Title card. IBM Bob logo. Open Production GitHub URL. "Built with IBM Bob — three captured sessions in `bob-sessions/`."

**Voiceover:** "Built with IBM Bob as the primary development tool. Three captured sessions. Open source, MIT. Read the architecture in the repo."

**Criterion:** none — close cleanly.

---

## Mapping to the five judging criteria

| Time | Criterion | What it scores |
|---|---|---|
| 0:15–0:35 | Real-World Impact | Thesis deadline, citation failure, trust loss |
| 0:35–1:05 | Technical Execution + Challenge Fit | Kernel diagram, primitives, fail-closed gates |
| 1:05–1:45 | **Innovation** (the highlight) | Creative reframing — the rubric's exact framing |
| 1:45–2:20 | Feasibility + Technical Execution | Live multi-agent research + live gate firings |
| 2:20–2:50 | Feasibility + Real-World Impact | Output PDF + audit trail |
| 2:50–3:00 | (closing) | Bob usage callout |

**Why this works:**
- The **innovation highlight is at 1:05**, not buried at the end. Judges see the differentiator in the first third.
- Every criterion gets at least **two shots** of evidence.
- The **live demo** (1:05–2:50) is the longest segment — 105 seconds of working software.
- The **opening** establishes stakes before showing the system.
- The **closing** echoes the Bob usage requirement without making it the whole video.

---

## Pre-recording checklist

Before hitting record:

- [ ] `make demo` runs end-to-end on a fresh clone without intervention.
- [ ] Terminal font size readable at 1080p (16pt minimum).
- [ ] No personal email or sensitive keys on screen.
- [ ] The contrarian angle pick at 1:30 is rehearsed (cursor position known).
- [ ] Voiceover script printed or on second monitor — don't read from the same screen you're recording.
- [ ] Lighting + audio checked (no fan noise, no echo).

---

## What to NOT include

- Reading code line by line (use the diagram, not the source).
- Showing Bob IDE itself (the audit trail is the Bob evidence, not the demo).
- Slides with bullet points (the deck already exists for judges; the video shows the system live).
- Apologies or hedging ("this might not work perfectly") — judges score confidence.
- The other four domains (video, audio, code, design) — the kernel is designed for them but the submission is the research-writing vertical.

---

## Recording tooling

Recommended:
- **OBS Studio** (free) for screen + voice recording.
- **1080p** resolution, 30fps.
- Output as MP4 (H.264).
- Edit in any tool — DaVinci Resolve (free), or just trim in OBS.

---

## After recording

- Upload to YouTube as **unlisted**.
- Watch once with sound off (does the visual story make sense?).
- Watch once with sound on (does the voiceover land?).
- Trim to ≤ 3:00 if over.
- Switch to **public** before submitting.

The YouTube link becomes Section 6 of the Project Page and the "Demo video" link in the README.
