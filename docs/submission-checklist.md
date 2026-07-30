# Submission Checklist — Open Production

**Deadline:** Fri 2026-07-31, 11:59 PM ET ≈ Sat 2026-08-01, 11:29 AM IST.
**Submission target:** Day 4 (Thu Jul 30) IST morning, well before the deadline.

Use this on Day 4 as a single-pass verification list. Each item is a hard gate — if it fails, fix before submitting.

---

## Gate 1 — Platform account + project page

- [ ] Registered on `https://aibuilderschallenge-bobhub.bemyapp.com/` with a fresh email (NOT the Bob one).
- [ ] Selected **July — Reimagine Creative Industries with AI** track.
- [ ] Project name on Platform = "Open Production" (matches `README.md`).
- [ ] Project page on Platform has all sections marked complete:
  - [ ] Project summary
  - [ ] Problem statement
  - [ ] Solution (5 stages — Creative Reframing is stage 2)
  - [ ] AI approach and architecture (cross-references `docs/architecture/architecture.md`)
  - [ ] How IBM Bob was used (9 captured sessions)
  - [ ] Demo video link (YouTube, public)
  - [ ] GitHub repo link (public)
  - [ ] Team member(s) + SkillsBuild cert

## Gate 2 — SkillsBuild certificate

- [ ] Course completed: *"How IBM Bob and AI Tools Are Changing the Way Solutions Are Built"* (or the troubleshooting lab).
- [ ] Certificate PDF saved locally.
- [ ] PDF path: `D:\IBM Project\Open_Production\bob-sessions\certificates\skillsbuild-cert.pdf`.
- [ ] Uploaded as part of the platform submission (Section 8).

## Gate 3 — Public GitHub repository

- [ ] Public repo created under Kartikey's GitHub account.
- [ ] Repo name matches Project Page (e.g., `open-production`).
- [ ] All non-PDT code lives in `D:\IBM Project\Open_Production\` and is pushed.
- [ ] README.md has **all 5 required sections** (Problem / Solution / AI approach & architecture / Challenge theme / How Bob was used).
- [ ] `python -m pytest tests/ -q` reports **164+ passed** (as of submission build).
- [ ] `bob-sessions/01-codebase-exploration/transcript.md` exists, raw Bob output preserved.
- [ ] `bob-sessions/02-creative-reframing-feature/transcript.md` exists with `src/agents/creative_reframing.py` and `tests/test_creative_reframing.py`.
- [ ] `bob-sessions/03-tests-and-checks/transcript.md` exists with `tests/test_gates.py` and the check log.
- [ ] `bob-sessions/04-demo-and-audit/transcript.md` exists.
- [ ] `bob-sessions/05-confirm-gate/transcript.md` exists.
- [ ] `bob-sessions/06-transform-catalog/transcript.md` exists.
- [ ] `bob-sessions/07-video-vertical/transcript.md` exists.
- [ ] `bob-sessions/08-code-review/transcript.md` exists.
- [ ] `bob-sessions/09-deployment-readiness/transcript.md` exists (this session).
- [ ] `docs/architecture/architecture.md` exists and reflects current implementation (all 13 agents, current Mermaid diagram).
- [ ] `docs/architecture/architecture-diagram.mmd` parses (renders in GitHub Markdown preview).
- [ ] `docs/demo/demo-story.md` exists.
- [ ] `python -m pytest tests/ -q` runs and passes (≥164 tests, 0 errors).
- [ ] License = MIT.

## Gate 4 — Working prototype

- [ ] Browser demo starts: `python src/public_demo/server.py` then open `http://127.0.0.1:8000/?view=guided`.
- [ ] The demo shows: intent → 3 angles → user picks → gates fire → production_id displayed → Agent Console link visible.
- [ ] `python -m pytest tests/ -q` passes with ≥164 tests, 0 errors, without any `--basetemp` flag.
- [ ] No real API keys in `src/` or `tests/`. `.env.example` only has commented placeholders.

## Gate 5 — Demo video (≤ 3 minutes)

- [ ] Video is ≤ 3:00 in duration.
- [ ] Uploaded to YouTube.
- [ ] Visibility switched from **unlisted → public** before submission.
- [ ] Hits all 5 judging criteria (per `docs/demo/demo-story.md` shot list):
  - [ ] Real-World Impact (0:15–0:35)
  - [ ] Technical Execution + Challenge Fit (0:35–1:05)
  - [ ] Innovation — Creative Reframing (1:05–1:45)
  - [ ] Feasibility + Technical Execution (1:45–2:20)
  - [ ] Output PDF + audit trail (2:20–2:50)
- [ ] URL pasted into Project Page Section 6.

## Gate 6 — Final QA before submit

- [ ] Clone repo into a fresh directory. Run `python -m pip install -e . && python -m pytest tests/ -q && python src/public_demo/server.py`. All succeed.
- [ ] Project Page `https://aibuilderschallenge-bobhub.bemyapp.com/#/projects` — click every link, including GitHub repo and YouTube video. All resolve to public, working URLs.
- [ ] Re-read the Project Page once with fresh eyes. No typos, no half-finished sentences.
- [ ] Spot-check the demo video — does it have audio? Any dead time?
- [ ] Verify the GitHub repo link is the **public** one, not your local working directory.

## Gate 7 — Submit

- [ ] Hit the platform's "Submit" button.
- [ ] Save the confirmation email.
- [ ] Screenshot the submitted project page.
- [ ] Capture and store the submission timestamp.

---

## What a "blocked" gate looks like

If any gate fails on Day 4 morning:

1. **Pause.** Don't submit a broken submission.
2. **Triage by severity:**
   - Hard fail (no Bob usage, broken demo): fix before submission. Push by 2 hours.
   - Soft fail (typo, slight wording): fix and submit.
3. **If the deadline is closer than the fix, downgrade scope:**
   - Ship a working 90s video, not a polished 3min one.
   - Ship a partial Project Page with `TBD` markers (but the judges will notice).
4. **Final rule:** A real, working submission with one rough edge beats a polished submission that doesn't run. Verifiable evidence > polish.

---

## Post-submission

- [ ] Pin a notification for the Week of August 11 winners announcement webinar (`https://aibuilderschallenge-bobhub.bemyapp.com/#/talks`).
- [ ] Save a copy of the submission in `D:\IBM Project\Open_Production\submission-archive\` with the date in the filename.
- [ ] If asked for revisions during judging, time-box the response to 2 hours — the call may be time-critical.
