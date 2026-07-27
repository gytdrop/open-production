# Demo Video Recording Guide — Open Production

**Goal:** Produce the ≤3:00 video for the IBM AI Builders Challenge Project Page. Maps to all five judging criteria.

**Shot-by-shot script:** `docs/demo/demo-story.md`
**Submission path:** YouTube (public). Link goes in the Project Page Section 6.

---

## 1. Tooling

**Screen recorder:** OBS Studio (free). https://obsproject.com/

**Settings:**
- 1080p resolution (1920x1080)
- 30 fps
- Output format: MP4 / H.264
- Audio: your microphone, 44.1 kHz mono

**Browser:** Chrome or Edge for the public-facing demo. This should be the main experience.

**Terminal:**
- PowerShell on Windows (or any terminal) only for optional cutaways or the audit trail file.
- Use a large font (Consolas 16pt minimum) if you show it on screen.
- Background: black or dark navy (matching the design palette).

---

## 2. Pre-recording checklist (15 min before)

Run through this list before hitting record:

- [ ] `cd 'D:\IBM Project\Open_Production'`
- [ ] `pytest -v` — must show `51 passed`
- [ ] `make web-demo` — must open the browser demo and show 3 angles + summary flow
- [ ] `python scripts/run_demo.py --topic "CRISPR for sickle cell disease" --no-confirm` — optional fallback, should still show 3 angles + summary line
- [ ] `python -m src.videos.render --title "Demo" --duration 6 --shots 3` — must show "Rendered X frames"
- [ ] Open `audit_trail.jsonl` in Notepad — must show 6 JSONL entries
- [ ] Open `output/video_demo/verdicts.json` — must show verdicts for all frames
- [ ] Close all browser tabs except the ones you need
- [ ] Silence your phone, turn off notifications, kill your music
- [ ] Test mic: speak at normal volume, watch the input meter hit green/yellow
- [ ] Set desktop background to solid color (avoid distractions)
- [ ] Drink water, clear throat

---

## 3. Shot-by-shot recording

Run through this in one take. **Don't stop between shots** — judges won't see the cuts but you'll be more relaxed.

### Shot 0 — Title card (5 sec)

**On screen:** Pure black for 1 second, then:

```
+---------------------------------------------+
|                                             |
|     [OP] Open Production                     |
|     AI as a creative partner                 |
|     for long-form content                    |
|     Built with IBM Bob                       |
|                                             |
+---------------------------------------------+
```

**Voiceover:** "Open Production — built with IBM Bob. AI as a creative partner for research writing."

**How to do it:** Stop recording, paste this card into a slide or Notepad, full-screen it. Hit record, give it 3 sec, start talking.

### Shot 1 — Problem (10 sec)

**On screen:** Switch to the browser landing page. Don't run anything yet.

**Voiceover:** "Every creator knows the bottleneck — research is slow, citations break, drafts contradict themselves, deadlines force shortcuts that lose trust."

### Shot 2 — Architecture in one shot (15 sec)

**On screen:** Open `docs/architecture/architecture-diagram.mmd` in any Mermaid renderer (or the GitHub preview). Let the cursor trace the path: Intent → Reframing → Research → Gates → Output.

**Voiceover:** "Open Production runs five stages. You declare an intent. The system proposes three creative angles. You pick one. Four academic agents research in parallel. Three fail-closed gates refuse to publish anything untraceable."

### Shot 3 — Creative reframing (40 sec — the highlight)

**On screen:** In the browser, type the topic and click **Show creative angles**. The three cards appear. Click "Use this angle" on one card.

**Voiceover:** "Watch the reframing — the system proposes skeptic, advocate, contrarian. I pick advocate. That's the AI as creative partner move: the system doesn't generate content unilaterally, it proposes alternatives and lets me decide."

### Shot 4 — Multi-agent research + gates (45 sec)

**On screen:** The browser result panel updates with the summary, counts, and audit trail. Optionally open the generated JSONL file in PowerShell for a quick cutaway.

**Voiceover:** "Multi-agent research hits four academic APIs in parallel. The evidence gate rejects a claim without a citation. The consistency gate surfaces a contradiction. The publication gate halts because of metadata. Fail-closed: every gate refuses to publish anything untraceable."

### Shot 5 — Output + audit trail (20 sec)

**On screen:** Open `audit_trail.jsonl` in a code editor. Scroll slowly. Each line has `ts`, `gate_name`, `claim_id`, `decision_status`.

**Voiceover:** "Result: every gate decision recorded. Every sentence traces back to a source. The audit trail is auditable — every query, every claim, every gate decision is recorded."

### Shot 6 — Closing (10 sec)

**On screen:** Switch back to the title card (same as Shot 0). Update it:

```
+---------------------------------------------+
|                                             |
|     [OP] Open Production                     |
|     Built with IBM Bob                       |
|                                             |
|     github.com/yourname/open-production     |
|                                             |
+---------------------------------------------+
```

**Voiceover:** "Built with IBM Bob as the primary development tool. Three captured sessions. Open source, MIT. Read the architecture in the repo."

### Total runtime

| Shot | Duration |
|---|---|
| 0 — Title | 0:05 |
| 1 — Problem | 0:10 |
| 2 — Architecture | 0:15 |
| 3 — Reframing | 0:40 |
| 4 — Research + gates | 0:45 |
| 5 — Output + audit | 0:20 |
| 6 — Closing | 0:10 |
| **Total** | **2:25** |

You have **35 seconds of slack** before hitting the 3:00 cap. Use them: add a quick "built with IBM Bob" mention at the start, or let the audit trail scroll longer in shot 5.

---

## 4. Edit + publish

**Edit (optional):** Trim dead air. Cut anything longer than 5 sec. Don't add music — judges don't want your taste, they want the system.

**Upload to YouTube:**

1. Go to https://studio.youtube.com/
2. Upload → select your MP4
3. Title: **Open Production — IBM AI Builders Challenge July 2026**
4. Description: paste this:

   ```
   Open Production: AI as a creative partner for long-form content.

   Five-stage pipeline:
   1. Intent declaration
   2. Creative reframing (skeptic/advocate/contrarian)
   3. Multi-agent research
   4. Claim extraction with fail-closed gates
   5. Publication gating

   Built with IBM Bob as the primary development tool.
   Seven captured Bob session transcripts in the repo.

   GitHub: https://github.com/yourname/open-production
   ```

5. Visibility: **unlisted** (you'll switch to public before submitting)
6. Click publish

**Switch to public** once the upload completes. YouTube usually takes 5–10 minutes to process.

---

## 5. Verify

- [ ] Video is ≤3:00
- [ ] URL is public (test in an incognito window)
- [ ] URL is pasted into Project Page Section 6
- [ ] GitHub repo is public and the URL is in Project Page Section 7

---

## 6. If you don't have time to record

The video is a "should have," not a "must have." The rubric says "publicly accessible demo or presentation video (maximum 3 minutes)" — they accept either. If you can't record:

- **Submit with no video.** Project Page marks Section 6 as "TBD." Judges score Feasibility lower but you don't get disqualified.
- **Submit with the deck as a video.** Open `deck/how-it-works-with-frontend.pptx` in PowerPoint → "Export → Create a Video" → use the deck slides as the presentation. Saves you from recording yourself.
- **Submit with a screen recording only.** No voiceover. Just record the `make demo` run for 2:30. Upload with a text caption explaining what's happening. Judges accept this format.

---

## 7. Recording-day quick command

When you're ready to record, run this one command to set up everything:

```powershell
cd 'D:\IBM Project\Open_Production'
clear
pytest -v 2>&1 | tail -3
echo ""
echo "Ready to record. Open OBS, hit record, then run:"
echo "  python scripts/run_demo.py --topic 'CRISPR for sickle cell disease'"
```

This gives you the last 3 lines of pytest (showing 51 passed), then the instructions. Hit record in OBS, then run the demo command. Everything else is in the shot list above.

---

## 8. What judges see

When they click the YouTube link in your Project Page:

- **Real terminal** with your command + output
- **Real voice** (or text cards) explaining what's happening
- **Real files** (audit_trail.jsonl, verdicts.json) being opened and inspected

That's a working prototype, not a slide. That's what wins "Feasibility."

---

## 9. Time budget

- Setup + first rehearsal: 30 min
- Rehearsals: 2-3 (10 min each)
- Final take: 1 min
- Edit + upload: 15 min
- Total: 1.5 to 2 hours

Do this once. Don't over-rehearse. The judges want to see the system work; they don't need a polished TED talk.

---

## 10. If you want Boris to write more demos

The current shot list covers the **research demo** end-to-end. If you want to also include the **video demo** (240 frames, video_audit.jsonl), Boris can write Shot 3.5: "Video vertical" — 30 seconds showing `python -m src.videos.render` running. That makes the 2nd-domain generalization visible. Cost: 5 minutes for Boris, 30 sec in the video.

Default: skip it. You're already at 2:25 with 35 sec slack. Adding more risks overshooting the cap.

---

**Bottom line:** Set up OBS, rehearse twice, hit record once, upload to YouTube, switch to public, paste the URL into Section 6 of the Project Page. Total: 1.5 hours.

The recording guide is also at `docs/demo/recording-guide.md`. Boris is doing the work — nothing left for you to wait on. Ping me with questions or to dispatch the optional Shot 3.5 (video demo addition).
