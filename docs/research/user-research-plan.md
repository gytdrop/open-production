# ACT-1 · User Research Plan

> Validate the four personas from `open-production-plan.md` §8 with one real user per persona type.

**Status:** ACT-1 plan · 2026-07-27
**Owner:** Product
**Inputs:** `open-production-plan.md` §8 (personas), §5/§6 (research synthesis), §11 (AI model), `docs/wireframes/README.md`
**Output:** validated personas · evidence-based UI adjustments · per-persona adoption curves

---

## 0 · Scope honesty

I (Boris) cannot recruit real users or run interviews from a Telegram thread. **This document is the protocol** — ready to hand to a researcher, founder, or anyone who can actually book the calls. Every artifact needed to execute the plan is included. The interviews themselves happen after the IBM submission window (post Fri 2026-07-31 ET), because the IBM judging rubric isn't blocking on real-user validation.

What you get when this plan runs:
- 4 × 30–45 min recorded interviews
- Per-persona hypothesis pass/fail with quotes
- 1–3 product changes per persona (wireframe-level)
- Validated vs. invalidated persona assumptions

---

## 1 · The four personas being validated

From `open-production-plan.md` §8 (verbatim, condensed):

| # | Persona | Age | Role | Time on task |
|---|---|---|---|---|
| 1 | The Emerging Creator (Sam) | 19–28 | self-taught YouTube/TikTok | wants first cut in <30 min |
| 2 | The Creative Professional (Jordan) | 28–45 | trained filmmaker / motion designer | hours per sequence |
| 3 | The Studio Lead (Alex) | 35–55 | runs team of 3–15 creators | hours × many productions |
| 4 | The Enterprise Buyer (Morgan) | 40–60 | brand/content director at large org | rarely opens the tool directly |

We need **1 real user per persona type**, totalling 4 interviews. Each persona maps to a distinct hypothesis about how the tool should behave.

---

## 2 · What we're validating

For each persona, we have 3 hypotheses from the design that drove the wireframes in `docs/wireframes/`. The interviews are designed to **break or confirm** them.

### Persona 1 — Sam (Emerging Creator)

| H# | Hypothesis | What we'd see if wrong |
|---|---|---|
| 1.1 | Guided Flow view is enough; no need to expose the crew | Sam asks "where do I edit what the AI did?" within 5 min |
| 1.2 | 3 angle proposals is the right number; more is overwhelming | Sam picks the first one without reading, or asks for "another set" |
| 1.3 | One-question-per-screen wizard feels right | Sam wants to skip ahead or paste a script and bypass the wizard |

### Persona 2 — Jordan (Creative Professional)

| H# | Hypothesis | What we'd see if wrong |
|---|---|---|
| 2.1 | Director's Canvas with floating AI proposals is preferred over chat-only | Jordan tabs between Canvas and Agent Console within 1 min |
| 2.2 | Keyboard-first / non-destructive layers are expected, not learned | Jordan asks "where is the timeline?" or "how do I undo?" |
| 2.3 | Director Mode ↔ Guided Mode toggle is desired, not one-mode-fits-all | Jordan says "I wish this was less guided" or vice versa |

### Persona 3 — Alex (Studio Lead)

| H# | Hypothesis | What we'd see if wrong |
|---|---|---|
| 3.1 | Branching (multiple parallel creative directions) is high-value | Alex asks "where can I duplicate the production?" |
| 3.2 | Studio Library (shared characters/environments) is requested first | Alex explains their current workaround for sharing assets |
| 3.3 | Reviewer-as-first-class-agent is welcomed, not bypassed | Alex says "I'll review myself" or skips the flag |

### Persona 4 — Morgan (Enterprise Buyer)

| H# | Hypothesis | What we'd see if wrong |
|---|---|---|
| 4.1 | Audit trail is the deciding factor for procurement | Morgan asks about cost, integration, or training first |
| 4.2 | Brand Kit enforcement matters more than creative flexibility | Morgan volunteers brand-safety concerns during the demo |
| 4.3 | 500-creator scale is plausible (not 5-creator scale) | Morgan references small-team workflows only |

---

## 3 · Recruitment criteria

Concrete, narrow, time-bound. If you can't fill the recruit in 2 weeks, the persona is wrong.

### Sam (Emerging Creator)

- 1+ year posting on YouTube, TikTok, or Instagram Reels
- Has produced at least one video using a tool other than their phone's built-in editor
- Not professionally trained in filmmaking
- Audience size: 100 to 10,000 (small enough that their feedback matters; large enough that they care about quality)
- Compensation: $50 gift card

### Jordan (Creative Professional)

- 5+ years paid work in filmmaking, motion design, or commercial video
- Has shipped work for at least 2 different brands in the past 2 years
- Currently uses a non-trivial tool (DaVinci Resolve, Premiere, After Effects, or comparable)
- Compensation: $100 gift card

### Alex (Studio Lead)

- Manages or owns a creative studio / agency of 3–15 people
- Has hired or contracted freelance video creators in the past year
- Has visibility into both creative output and budget
- Compensation: $100 gift card

### Morgan (Enterprise Buyer)

- Brand director / content director / VP marketing at a company with 50+ employees
- Approves or shapes a video-production budget at least quarterly
- Has decision authority for, or strong influence over, tool procurement
- Compensation: $150 gift card (gift cards skew small for this seniority; consider donation to a charity of their choice instead)

### Universal

- 30–45 min available for a recorded video call
- English-speaking
- Has signed consent for recording
- **Exclude**: anyone who works at IBM, has worked on AI video tools in the past year, or is a personal connection of the team

---

## 4 · Pre-interview task

Send to each participant 48 hours before the call:

> "Pick a project you've actually wanted to make (could be work-related, could be personal). Have a 2–3 sentence description of it ready when we meet. We'll spend the first 10 minutes walking through how you'd start that project in a tool we'd like your feedback on."

This gives us realistic early-funnel material. People with no "thing they want to make" are bad research participants.

---

## 5 · The interview protocol (shared across all 4)

**Total time:** 35–45 minutes. Allow 10 min buffer.

| Phase | Duration | What happens |
|---|---|---|
| (0) Framing | 2 min | "We're testing a new design. There are no wrong answers. We're not selling you anything." Recording consent. |
| (1) Pre-task walkthrough | 8 min | They describe their project. We ask 3 grounding questions (tools used, biggest friction, what they'd automate). |
| (2) Live demo | 15 min | Share screen. Show the wireframe that maps to their persona. Narrate what they're thinking as they click. |
| (3) Comprehension probe | 5 min | For each L1 hypothesis, ask the persona-specific "what would you do if…" question. |
| (4) Wrap | 5 min | "What's the most useful thing in this design?" / "What's the most confusing?" |

---

## 6 · Per-persona demo flow

What to show on screen, in order, for each persona.

### For Sam (Emerging Creator) — Guided Flow + Director's Canvas

1. Start at `02-guided-flow.svg`. They click through stages 1–3 (idea → references → mood).
2. Skip to "Pick a creative angle" — show 3 options, ask "which do you pick and why?"
3. Drop into `01-directors-canvas.svg` for the "you're approved" moment. Don't explain anything. Watch what they do.
4. Ask: "If you could change anything about how this feels, what is it?"

### For Jordan (Creative Professional) — Director's Canvas + Agent Console

1. Open at `01-directors-canvas.svg`. Put them in the middle of an active scene with shot 7 selected and an AI proposal popping.
2. Let them click anywhere. Narrate.
3. Switch to `04-agent-console.svg` for the same production. Ask which view they prefer for what kind of work.
4. Ask: "What tool are you using right now that this would replace, and what would you hate losing?"

### For Alex (Studio Lead) — Agent Console + Node Graph

1. Open `04-agent-console.svg` with branches panel visible on the right.
2. "Walk me through how you'd give the same brief to two of your freelancers."
3. Switch to `05-node-graph.svg`. Ask: "If you had to debug why a shot got rejected, where would you start?"
4. Ask about Studio Library / asset sharing — what is their current workaround?

### For Morgan (Enterprise Buyer) — Director's Canvas (Read-Only)

1. Show `01-directors-canvas.svg` slowly. Don't ask them to interact.
2. Pause at the Reviewer Agent's warning ("character expression diverges from anchor"). Let them ask the first question.
3. Open the audit log from `04-agent-console.svg`. Pause on a gate decision.
4. Ask: "If you were reviewing this for procurement, what would you want to see that you don't?"

---

## 7 · What we're capturing

Per interview, write a single doc with this template:

```markdown
# Interview — <Persona> · <Date>

## Setup
- ID (anonymized): P-<n>
- Duration:
- Recording: <link>

## Pre-task (3 grounding questions)
- Q1: tools used → ...
- Q2: biggest friction → ...
- Q3: what they'd automate → ...

## Live demo notes
- They clicked [X] when I expected [Y] because …
- Confused moment at …
- Aha moment at …

## Hypothesis verdicts (Pass / Fail / Mixed)
- H#.1 → Pass. Quote: "..."
- H#.2 → Fail. Quote: "..."
- H#.3 → Mixed. Quote: "..."

## Verbatim quotes worth surfacing
- "..." (3 max — preserve voice)

## Friction we didn't predict
- ...

## Suggested wireframe changes
- 1. ...
- 2. ...

## Recommendation
- GO / NO-GO on the persona's primary view · one-line rationale
```

That's a 1-page doc per interview. 4 interviews = 4 single-page docs. Easy to circulate.

---

## 8 · What we'd do with the results

Within 1 week of completing all 4 interviews:

1. Tally H# pass/fail rates. If a hypothesis fails across 2+ personas, that's a real signal — change the wireframe in `docs/wireframes/`.
2. Identify the **single biggest unexpected friction** per interview. Surface in a 1-page memo to engineering + design.
3. Update `docs/wireframes/README.md` "Validation status" table to reflect actual data.
4. Decide if any persona is **not the target audience** for the v1 product. If Sam rejects Guided Flow 3/3 times, we may not be building for Sam.

The point is not "validate the personas." The point is **kill the wrong ones early** and ship the right ones faster.

---

## 9 · What we're NOT doing (scope cuts)

- ❌ Quantitative survey (n=4 is qualitative only; surveys need n≥30 to be useful)
- ❌ A/B testing (no production traffic to test against)
- ❌ Eye-tracking or biometric studies (requires equipment, not 30–45 min)
- ❌ International personas (English-only for v1 — assume lowest-cost testing first)
- ❌ Quantitative satisfaction scores (NPS isn't meaningful at n=4)

---

## 10 · Risks the plan doesn't mitigate

- **Selection bias**: anyone willing to be paid $50–150 for a 30-min Zoom call is not representative of the broader persona. Mention this caveat in any published synthesis.
- **Social desirability bias**: even with "no wrong answers" framing, participants may soften criticisms. Pair with implicit signal capture (click paths, time-on-task) in any future iteration.
- **Recruiter influence**: if you use a recruiter, prime them to deliver no preference signals to candidates before the call.

---

*Planned as part of ACT-1 · User research · 2026-07-27 · ready to execute post-submission*