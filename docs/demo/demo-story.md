# Demo Story — Open Production

**Duration:** ≤ 3 minutes (cap: 3:00).
**Entry point:** Browser demo at `http://127.0.0.1:8000/?view=guided` (no terminal visible to audience).
**Published:** YouTube, unlisted then public.
**Purpose:** communicate all five judging criteria in 180 seconds.

---

## Pre-recording setup

```powershell
cd "D:\IBM Project\Open_Production"
python -m pip install -e .
python src/public_demo/server.py
# Browser opens at http://127.0.0.1:8000/?view=guided
```

Have the Agent Console tab ready at `http://127.0.0.1:8000/?view=console`.

---

## Shot list — second-by-second

### 0:00–0:15 — Title card

**Visual:** Open Production logo (the 🪷 lotus mark). Tagline: *"AI as a creative partner for video production."*

**Voiceover:** "Open Production — built with IBM Bob. A 21-agent production crew with fail-closed gates and a full audit trail."

**Criterion:** none yet — set the frame.

---

### 0:15–0:35 — Problem statement

**Visual:** A mock production brief — dozens of agents, no oversight, no audit. Highlight: "Who approved this? Where's the brief?"

**Voiceover:** "Every AI creative tool shares one failure mode: generation happens unilaterally. No brief. No stage gate. No consistency contract. No audit trail. Open Production fixes that."

**Criterion:** **Real-World Impact.** Sets the human stakes.

---

### 0:35–1:05 — Architecture in one shot

**Visual:** Show the Mermaid diagram at `docs/architecture/architecture-diagram.mmd`. Highlight: Intent → Creative Reframing → 21 Agents → 4 Fail-Closed Gates → Dual-Artifact Output → 2 Browser Views.

**Voiceover:** "Five layers. User Intent feeds Creative Reframing — three angles, user picks one. A 21-agent production crew each with a bounded scope contract. Four fail-closed gates. Every decision written to an append-only audit journal. Two browser views."

**Criterion:** **Technical Execution** + **Challenge Fit.** Kernel depth in 30 seconds.

---

### 1:05–1:45 — The creative reframing moment (live browser)

**Visual:** Live screen capture. Browser demo at `http://127.0.0.1:8000/?view=guided`. Type a topic: "The future of AI in creative industries". Click "Show creative angles". Three angle cards appear: **skeptic / advocate / contrarian**. Click "Use this angle" on the contrarian card.

**Voiceover:** "Watch the reframing — skeptic, advocate, contrarian. I pick contrarian. That is the AI-as-creative-partner move: the system proposes alternatives and waits for a human decision. It does not generate unilaterally."

**Criterion:** **Innovation.** The differentiator. The rubric's exact framing.

---

### 1:45–2:20 — Gates fire + production created

**Visual:** After picking an angle, the Result panel appears. Accepted / rejected / contradiction counts update. The production_id panel appears with the teal "Open in Agent Console →" link. Click it. The Agent Console opens, showing the per-actor event rail and the live audit log.

**Voiceover:** "Evidence gate rejects one claim — no citation. Consistency gate detects a contradiction. Publication gate checks metadata readiness. Every decision logged. And here — the production ID. The Agent Console shows the full event stream, filterable by agent."

**Criterion:** **Feasibility** + **Technical Execution.** Live, working, not a slide.

---

### 2:20–2:50 — Audit trail as proof

**Visual:** Agent Console. Click "system" in the actor rail — filter to system events. Show the audit log entries scrolling. Switch back to "All". Open the browser DevTools network tab briefly to show `/api/production/<id>/log` returning real JSON.

**Voiceover:** "This is the audit trail — every gate decision, every agent action, append-only. Every production is reproducible from its journal. This is what 'AI as creative partner' means: the process is visible, traceable, and verifiable."

**Criterion:** **Feasibility** + **Real-World Impact.** The deliverable is real.

---

### 2:50–3:00 — Closing + Bob usage

**Visual:** Title card. "464 tests. 21 agents. 4 fail-closed gates. Built with IBM Bob — 9 sessions." Open Production GitHub URL.

**Voiceover:** "464 tests. 21 agents. 4 fail-closed gates. Open source, MIT. Built with IBM Bob. The architecture is in the repo."

**Criterion:** none — close cleanly.

---

## Mapping to the five judging criteria

| Time | Criterion | What it scores |
|---|---|---|
| 0:15–0:35 | Real-World Impact | Unauditable AI production — the failure mode creators face |
| 0:35–1:05 | Technical Execution + Challenge Fit | Kernel diagram, 21 agents, fail-closed gates, dual-artifact output |
| 1:05–1:45 | **Innovation** (the highlight) | Creative reframing — the rubric's exact framing |
| 1:45–2:20 | Feasibility + Technical Execution | Live gate firings, production_id, Agent Console with actor filter |
| 2:20–2:50 | Feasibility + Real-World Impact | Audit trail as real artifact + API verification |
| 2:50–3:00 | (closing) | 464 tests, 9 Bob sessions |

**Why this works:**
- The **innovation highlight is at 1:05**, not buried at the end. Judges see the differentiator in the first third.
- Every criterion gets at least **two shots** of evidence.
- The **live browser demo** (1:05–2:50) is the longest segment — 105 seconds of working software.
- The **opening** establishes stakes before showing the system.
- The **closing** echoes the Bob usage requirement concisely.

---

## Pre-recording checklist

Before hitting record:

- [ ] `python -m pytest tests/ -q` reports 464 passed from a fresh terminal (no `--basetemp` flag).
- [ ] Browser demo starts cleanly: `python src/public_demo/server.py` → `http://127.0.0.1:8000/?view=guided`.
- [ ] Guided Flow: topic pre-filled, angles appear, angle selection works, production_id panel visible after finalize.
- [ ] Agent Console: actor rail visible, "All" button active, event list loads.
- [ ] Terminal font size readable at 1080p (16pt minimum).
- [ ] No personal email or sensitive keys on screen.
- [ ] Voiceover script printed or on second monitor.
- [ ] Lighting + audio checked (no fan noise, no echo).

---

## What to NOT include

- Reading code line by line (use the diagram, not the source).
- Showing Bob IDE itself (the audit trail is the Bob evidence, not the demo).
- Slides with bullet points (the architecture doc exists; the video shows the system live).
- Apologies or hedging ("this might not work perfectly") — judges score confidence.
- The terminal / command line (the browser demo is the public face).

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

The YouTube link becomes Section 6 of the Project Page and the "Demo video" link in `README.md`.
