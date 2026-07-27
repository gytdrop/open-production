# Open Production — Principles

> **Source:** Distilled from `open-production-plan.md` (Sections 3, 4, 25, 26 + Appendix A).
> **Purpose:** One-page manifesto. Every architectural decision in this repo should be checkable against this document. If a feature violates a principle, the principle wins.

---

## The Central Bet

**The production process is the product.** The output video is a byproduct of a captured, inspectable, replayable production process. A user who finishes a production should be able to hand off the entire production — not just the video — to a collaborator who can pick up exactly where they left off, change the creative direction, regenerate any stage, and publish a different cut.

The Pixar test: _would a production team at Pixar recognize this as a production environment, not a toy?_

---

## The Five Laws

### Law 1: Generation is a service call, not a product
Generation is what the AI does _after_ the human has finished deciding. The interface should make it harder to jump to generation than to plan first.
**Test:** If a user can produce a finished video without writing at least one brief, approving one reference, and locking one stage gate, the product has failed.

### Law 2: Nothing is final until the user says so
Every generated asset, script line, and camera angle is provisional until explicitly locked. Locking is an affirmative action. Unlocking is always possible.
**Test:** If "save" can destroy a previous version, the product has failed.

### Law 3: Every decision has a reason
The system captures _why_ a decision was made (chosen angle, chosen reference, chosen constraint) alongside _what_ was decided. This is the audit trail principle.
**Test:** If a user can see what the AI produced but cannot see why, the product has failed.

### Law 4: Beginners and professionals use the same engine, different views
The production engine is one. The interface layer adapts. Beginners see guided mode. Professionals see director mode. The engine beneath is identical.
**Test:** A beginner's finished production opens in director mode and shows every decision, fully specified and editable. No "beginner tier" lock-in.

### Law 5: The AI earns autonomy incrementally
The AI is not trusted by default. It earns the right to act autonomously by demonstrating quality. Until trust is earned, every AI action is proposed, not executed.
**Test:** If any AI action reaches the user without passing a gate, the product has failed.

---

## The Three Axioms (Architectural Commitments)

### Axiom 1: Production state is first-class
The full record of every decision, asset, reference, script, shot, and generation must be serializable, versioned, diffable, and shareable. A production is a document, not a folder of video files.
**Implementation:** `audit_trail.jsonl` is the source of truth. The current state is a function of the event log.

### Axiom 2: Every interface is a view of the same model
Timeline, storyboard, node graph, script, and chat are all views of the same underlying production model. Changing something in one view changes it everywhere.
**Implementation:** Vertical views read from the same state object. No view has its own copy of the data.

### Axiom 3: Human override is always available
No AI action is irreversible. No AI decision is hidden. Every AI-generated value can be manually overridden. The override is stored as an annotation on the production state, not as a replacement.
**Implementation:** Non-destructive layers. The AI's output is the base layer; human overrides stack on top. Removing any layer reveals the AI's original output.

---

## The 5% Rule (Empirical Claim)

A production is **5% generation, 25% planning, 40% iteration, 15% asset management, 15% production management**. The interface must enforce this ratio structurally. If the system makes generation the easiest action, the user will spend their time there — and produce shallow work.

This is why every agent action goes through a Proposal Protocol (read state → propose → state rationale → wait for approval). Generation is the slowest, most expensive, and least interesting step. Everything else deserves more interface real estate.

---

## The Progressive Depth Principle

Every feature has exactly three levels of depth: **overview** (beginner sees this), **standard** (intermediate user engages this), **expert** (professional unlocks this). The levels are not separate modes — they are the same feature, revealed progressively. The beginner who becomes an expert never switches tools. They go deeper into the same system.

Validated by: Figma (layers → components → auto-layout), Blender (shader nodes → geometry nodes → scripts), Unreal Engine (Blueprint → C++), Notion (blocks → databases → formulas).

---

## Features That Should NEVER Be Added

Non-negotiable. Each item is a defense against a known failure mode.

1. **Magic button one-shot production.** A single prompt → finished video button. Trains users to expect magic instead of production. Violates Law 1.
2. **Auto-publish without human approval.** Automation ends at "ready to publish," not "published." Publication is always a human decision. Violates Law 2.
3. **Prompt history as production history.** Prompts are not a record of creative decisions. Expose decisions, not raw prompts. Violates Law 3.
4. **AI-generated brand kits.** Brand kits are identity documents. They must be authored by the brand, not generated by the AI. AI can suggest; AI never decides brand identity.
5. **Irreversible operations.** Every action must be undoable. No delete-without-recovery. No overwrite-without-snapshot. Violates Law 2.
6. **Hidden AI decisions.** If the AI made a decision, the user must see it, understand it, and override it. No silent optimization. Violates Law 5.
7. **Gamification of production metrics.** No completion scores, no quality ratings, no leaderboards. Production quality is contextual and subjective. Gamification creates incentives to optimize for metrics rather than creative quality.
8. **Cross-production content leakage.** Assets, briefs, and production content from one studio must never appear in another studio's suggestions, training data, or recommendations. Hard privacy boundary.

---

## What Differentiates This Product

The five things that no competitor has:

1. **The Production Document** — serializable, diffable, versionable record of every creative decision.
2. **The Consistency Contract** — formal spec for visual consistency across shots and scenes, gated by a Reviewer agent.
3. **The Production Crew Model** — multiple specialist agents with bounded scope contracts, not a single assistant.
4. **Stage Gates** — explicit, human-approved gates between production stages. AI cannot proceed without approval.
5. **The Reviewer Agent** — an AI that evaluates every output against the production brief before the human sees it. Failed generations are never shown.

---

## Known Caveats (Honest)

These claims are principled but not yet stress-tested. Flagging them so future engineers don't over-claim.

- **"Same engine, beginner/professional"** is the strongest design claim and the least proven. Figma is the closest precedent; the analogy breaks at code-level customization (Blender has Python, Figma has plugins). The "no separate tier" promise is an architectural commitment, not a measured outcome.
- **The Consistency Contract** has no cost model. Reference-image count, variance tolerance, and the Reviewer agent's strictness tradeoff are not quantified. Pricing/performance implications TBD.
- **AI autonomy (Law 5)** is binary in the doc — proposed vs. executed. The real world is graduated. A future revision should define trust levels explicitly (e.g., 0–5 scale, with promotion criteria).
- **"Production DNA" type features** (learning from production history) are absent from this principles doc for a reason: they collide head-on with the Law 8 no-leakage boundary and raise unresolved IP questions. Treat any such feature as architectural-red until proven otherwise.

---

## How to Use This Document

- **Before adding a feature:** check the Five Laws and the NEVER list. If it violates either, the feature is rejected by principle.
- **Before shipping a UI change:** check the Progressive Depth Principle. Does the new view respect the 3-level depth model?
- **Before claiming a differentiator:** check the What Differentiates list. If the claim isn't there, it's a generic feature, not a differentiator.
- **When in doubt:** Law 1 wins. Generation is not the product. The process is.

---

*Version 1.0 · 2026-07-27 · Extracted from open-production-plan.md v1.2*
