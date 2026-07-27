# 90-Second Narrated Script — Judge Walkthrough

**Audience:** Competition judge. One run-through, live or recorded.  
**Total spoken words:** ≈ 220  
**User journey:** Emerging creator pastes a script topic → sees 3 angles → picks one → reads the audit trail.  
**What this demo does NOT claim:** real video rendering, multi-user collaboration, brand kits, mobile app.

---

## Pacing guide

| Segment | Clock | Words |
|---|---|---|
| Setup | 0:00–0:10 | ≈ 25 |
| Pick an angle | 0:10–0:40 | ≈ 75 |
| See the audit trail | 0:40–1:10 | ≈ 75 |
| Closing claim | 1:10–1:30 | ≈ 45 |

---

## Script

---

### [0:00–0:10] Setup — 25 words

> "Meet Sam. She has a research topic — CRISPR gene therapy — and no idea
> where to start. She pastes it here and hits go."

*[Screen: browser demo, topic field. User types "CRISPR gene therapy" and submits.]*

---

### [0:10–0:40] Pick an angle — 75 words

> "The system doesn't start writing. It proposes three creative frames:
> **skeptic** — what evidence is missing?
> **advocate** — who benefits and why does it matter?
> **contrarian** — what does the consensus get backwards?
>
> Sam reads the one-sentence summary under each. She picks **contrarian**.
>
> That choice is not cosmetic. Every gate, every claim, every source the system
> evaluates from here will be anchored to the contrarian angle she just approved.
> She directed the AI. The AI didn't direct her."

*[Screen: three angle cards appear. Cursor hovers each summary. Click: contrarian.]*

---

### [0:40–1:10] See the audit trail — 75 words

> "Now watch what gets recorded. Three claims come back from research.
> Claim one — accepted, has a PubMed source.
> Claim two — rejected, no citation.
> Claim three — flagged: it contradicts claim one on the same fact.
>
> Every one of those decisions is a timestamped JSON line written by
> `AuditRecorder.record_gate_decision` in `src/audit/recorder.py`.
> The file is open right here. Nothing is hidden. Nothing is inferred after
> the fact. The log is written at decision time or the decision doesn't count."

*[Screen: audit trail panel scrolls — three gate entries visible, each with `gate_name`, `decision_status`, `reason`.]*

---

### [1:10–1:30] Closing claim — 45 words

> "This is a 51-test prototype. We are not claiming a finished product.
> We are claiming a correct foundation.
>
> **The audit trail IS the production document.
> The video is just one render of it.**"

*[Screen: freeze on the audit trail JSONL. Hold three seconds. Fade.]*

---

## Narrator notes

- **Do not speed up the angle-pick segment.** The three-sentence summaries are the
  innovation. Let the judge read them.
- **Do not skip the rejected claim.** A gate that fires is more compelling than one
  that passes everything.
- **Do not apologise for the prototype stage.** The closing claim owns it directly.
- The `record_gate_decision` method reference in the audit segment is intentional —
  it anchors the claim to working code, not a slide.
  → [`src/audit/recorder.py:23`](../../src/audit/recorder.py:23)
- The quoted closing line is verbatim. Do not paraphrase it.

---

## What this script deliberately omits

| Feature | Why omitted |
|---|---|
| Real video generation | Not in the current prototype |
| Multi-user collaboration | Not in the current prototype |
| Brand kits | Not in the current prototype |
| Mobile app | Not in the current prototype |
| Full 26-stage pipeline | Confuses a 90-second window; use `demo-story.md` for the 3-minute version |
