# P0-4 · Pipeline Validation Plan

> Confirm the production pipeline stage ordering (the 26 stages in `open-production-plan.md` §14) with a practicing video producer.

**Status:** P0-4 plan · 2026-07-27
**Owner:** Product
**Inputs:** `open-production-plan.md` §14 (26-stage pipeline), Appendix G (pipeline deep dives), `docs/wireframes/05-node-graph.svg`
**Output:** validated stage ordering · re-prioritized roadmap · evidence for what ships in Phase 1 vs Phase 2

---

## 0 · Scope honesty

Same constraint as ACT-1: I (Boris) cannot book a video producer from a Telegram thread. **This is the protocol.** Run it post-submission when there's time to actually recruit and pay someone.

---

## 1 · Why this validation matters

The 26-stage pipeline in `open-production-plan.md` §14 is a **flat list**. The doc itself notes:

> "The 26-stage pipeline has no priority order. Which 5 ship first? The doc lists them all flat." — review at 2026-07-27 15:25

That's a problem for the roadmap. If we ship the wrong 5 first, the prototype demos the wrong workflow. If we ship them in the wrong order, the developer experience is worse than it needs to be.

A single 60-minute conversation with a practicing video producer resolves most of this. We don't need a panel — we need **one person who's actually made 50+ videos professionally** to walk the list and say "this is right" or "this is wrong" or "swap X and Y."

---

## 2 · What we're validating

| # | Hypothesis | Source |
|---|---|---|
| H1 | The 26 stages are exhaustive — no major real-world step is missing | §14 stage list |
| H2 | The stage ordering is roughly right for typical scripted video production | §14 + Appendix G |
| H3 | Stages 1–6 (Idea → Script) come before any visual generation | §14 + §15 agent scope |
| H4 | Stages 13–14 (Camera, Lighting) come after Script but before Generation | §14 |
| H5 | Music (stage 20) comes after Picture Lock (stage 17) | §14 |
| H6 | Color (stage 22) comes after Edit (stage 17) and before Review (stage 23) | §14 |
| H7 | Iteration (stage 24) is a real stage, not just a loop on stage 16 (Generation) | §14 |
| H8 | Review (stage 23) is a distinct gate from Generation (stage 16) — i.e. they're not the same thing | §14 + differentiators |
| H9 | The first 5 stages to ship in Phase 1 are: Idea → Script → Shot Plan → Generate → Review | §23 |
| H10 | Phase 1 doesn't need stages 19 (Voice), 20 (Music), 21 (Sound) to demonstrate the architecture | §23 |

A practicing video producer is more likely to **break** these hypotheses than confirm them. That's the point.

---

## 3 · Recruitment criteria

One participant. Concrete, narrow.

- **Has shipped 50+ professional video projects** (any genre: brand, narrative, music videos, broadcast, doc — but "professional" matters, not hobbyist)
- **Has used a non-linear editor professionally** (Premiere, DaVinci, FCP, or comparable)
- **Has worked in a team** (director + DP + editor + colorist OR a single-creator wearing multiple hats on a 50+ project portfolio)
- **Currently active** — made a video in the past 12 months
- **60 minutes available** for a recorded video call
- **English-speaking**

### Compensation

$150 gift card. (Higher than user-research because of the longer session + more specialized expertise.)

### Universal excludes

- Works at IBM
- Worked on AI video tools in the past year
- Personal connection of the team

---

## 4 · Pre-interview task

Send 48 hours before:

> "We're testing a 26-stage pipeline for a video production tool. Before our call, please think about your last 3 video projects. For each, jot down (in 1 sentence each) what you did in order. We'll compare your answers to our pipeline when we meet."

This gives us real-world ordering baselines from a single person. We won't generalize beyond one participant, but we'll get concrete "this is what I actually do" data.

---

## 5 · The interview protocol

**Total time:** 60 minutes. Allow 10 min buffer.

| Phase | Duration | What happens |
|---|---|---|
| (0) Framing | 3 min | "We're testing a pipeline structure. There are no wrong answers. Recording consent." |
| (1) Pre-task review | 7 min | They walk us through their 3 last projects (order of operations). We note what they did vs. what our pipeline says. |
| (2) Stage-by-stage walk | 30 min | We go through the 26 stages one by one. For each stage, ask: "Is this a real stage? Is the ordering right? Anything missing?" |
| (3) Reorder test | 10 min | Show 3 specific stages where we have low confidence in ordering. Ask them to reorder. |
| (4) Phase 1 test | 10 min | Show our proposed Phase 1 (Idea → Script → Shot Plan → Generate → Review). Ask "if you had to teach someone video production, is this the right 5 to start with?" |

---

## 6 · The 26 stages we'll walk

In the order from `open-production-plan.md` §14 (verbatim, condensed for the interview):

```
1.  Idea              14. Lighting           25. (full list in doc)
2.  Research          15. Assets             26. (we'll show on screen)
3.  References        16. Generation
4.  Moodboard         17. Editing
5.  Creative Direction 18. Animation
6.  Story             19. Voice
7.  Script            20. Music
8.  Characters        21. Sound
9.  Locations         22. Color
10. Shot Planning     23. Review
11. Storyboard        24. Iteration
12. Timeline          25. Publishing
13. Camera            26. Archive
```

For each stage, the protocol asks:

1. **Is this a real stage?** (Have you actually done this in your work, or is it invented?)
2. **Is the ordering right?** (Does it come at this point in the process, or earlier/later?)
3. **Anything missing?** (What do you do that doesn't fit these 26?)

The interviewer captures answers in a single table with one row per stage.

---

## 7 · The 3 reorder tests

These are the stages where our ordering confidence is lowest. Show them to the participant and ask "which order is right, or is there a third order I'm not seeing?"

### Test 1 — Generation (16) vs Lighting (14)

Our doc: Lighting specs come before Generation. Lighting is locked, then shots are generated.
**Question for the producer**: "In your work, do you lock lighting before you start generating shots? Or do you iterate lighting as part of generation?"

### Test 2 — Music (20) vs Color (22)

Our doc: Music cues are authored in stage 20 (after Edit is locked, before Color). Color is stage 22.
**Question for the producer**: "In your work, does music come before or after color grade? Why?"

### Test 3 — Voice (19) vs Animation (18) vs Music (20)

Our doc: Animation (18) → Voice (19) → Music (20). All three come after Edit is locked.
**Question for the producer**: "If you had to pick the order of these three, what would it be? What depends on what?"

---

## 8 · Phase 1 prioritization test

After the reorder tests, show the participant our proposed Phase 1 (Idea → Script → Shot Plan → Generate → Review) and ask:

> "If a new video producer were learning our tool, would these 5 stages teach them the right fundamentals? What's missing that should be in the first 5? What's in the first 5 that should come later?"

Expected outcome: confirm that the 5 are roughly right but possibly swap Generate ↔ Review, or insert Moodboard earlier.

---

## 9 · Capture template

```markdown
# Pipeline Validation Interview — <Producer> · <Date>

## Setup
- ID (anonymized): PROD-<n>
- Duration:
- Recording: <link>

## Pre-task (last 3 projects)
- Project 1: ...
- Project 2: ...
- Project 3: ...

## Per-stage notes
| # | Stage | Real? | Right order? | Missing? |
|---|---|---|---|---|
| 1 | Idea | ✓ / ✗ / partial | before/after #X | ... |
| 2 | Research | ... |
| ... |
| 26 | Archive | ... |

## Reorder tests
- Test 1 (Gen vs Lighting): producer says ...
- Test 2 (Music vs Color): producer says ...
- Test 3 (Voice/Anim/Music): producer says ...

## Phase 1 verdict
- Right 5 / wrong 5 / missing
- Quote: "..."

## Recommended reordering (if any)
- ...

## Stages we'd add (if any)
- ...

## Stages we'd merge (if any)
- ...

## Verdict
- 26 stages as-is: keep / modify / restructure
- Phase 1 priorities: keep / modify / restructure
```

Single 2-page doc per interview.

---

## 10 · What we'd do with the results

Within 1 week of the interview:

1. **Re-rank the 26 stages** per the producer's reorder tests. Update `open-production-plan.md` §14 if the new ordering is materially different.
2. **Confirm or modify Phase 1 priorities** (the 5 to ship first). Update `docs/roadmap/phase-1.md` if needed.
3. **Identify any missing stages** the producer named. Add to §14 if real (not just renamed stages we already have).
4. **Identify any merged stages** the producer suggested. Document the merge rationale — it might just be that our naming is wrong.
5. **Surface the producer's verdict** in the user-research plan's "evidence-based UI adjustments" section.

If the producer breaks more than 3 of our 10 hypotheses, that's a real signal that the pipeline structure itself needs work. If they confirm 8+, ship the current structure as-is.

---

## 11 · What we're NOT doing (scope cuts)

- ❌ Multiple producers (one is enough for prioritization; n=10+ is overkill for this phase)
- ❌ International producers (English-only)
- ❌ Comparing across genres (one person's practice reveals their genre's pipeline; not transferable)
- ❌ Production-company-scale pipeline validation (that needs Alex, not a producer — separate interview)
- ❌ Quantitative time-on-each-stage measurement (requires instrumentation, not 60 min)

---

## 12 · Risks

- **Single-source bias**: one producer's practice may not be representative. Use results to **flag** questions, not to settle them.
- **Genre bias**: if the producer works mostly in commercials, their answers lean toward that pipeline. Music video or documentary may differ. Ask them to disclose primary genre upfront.
- **Recency bias**: people remember their last project most clearly. Pre-task explicitly asks for 3 projects to spread the data.
- **Authority bias**: a producer may unconsciously defer to the "official" pipeline we showed. Counter by asking them to **draw** their own pipeline on a whiteboard before we show ours.

---

*Planned as part of P0-4 · Pipeline validation · 2026-07-27 · ready to execute post-submission*