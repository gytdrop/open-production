# How to Launch and Test — Open Production

Three launch contexts. Pick the one you need.

---

## 1. Browser launch — easiest for a general audience

This is the recommended path if you want a non-technical experience.

```powershell
# Step 1: navigate to the project
cd 'D:\IBM Project\Open_Production'

# Step 2: launch the browser demo
make web-demo
# or: python scripts/run_web_demo.py --open-browser
```

The browser opens at `http://127.0.0.1:8000/`. From there:

1. Enter a topic.
2. Click "Show creative angles".
3. Pick skeptic, advocate, or contrarian.
4. Review the summary and audit trail.

The browser demo uses the same underlying logic as the terminal demo, but it is much friendlier for non-technical users.

---

## 2. Terminal launch — run the prototype on your machine

**Prerequisites:** Python 3.10+ on Windows / macOS / Linux. Git. ~5 minutes.

```powershell
# Step 1: navigate to the project (or clone the public repo after Day 4)
cd 'D:\IBM Project\Open_Production'

# Step 2: install dependencies (only pytest + stdlib extras)
python -m pip install -e .
# or: python -m pip install pytest

# Step 3: run the test suite — should be 51/51 passing
make test
# or: pytest -v

# Step 4: run the demo end-to-end
make demo
# or: python scripts/run_demo.py --topic "CRISPR for sickle cell disease"

# Step 5: inspect the audit trail
type audit_demo.jsonl
# or: cat audit_trail.jsonl
```

**Expected output from `make demo`:**

```
Creative angles for: 'CRISPR for sickle cell disease'

  1. [skeptic] The skeptic's view
     What are the strongest objections to current claims about CRISPR for sickle cell disease?
  2. [advocate] The advocate's case
     Why does CRISPR for sickle cell disease matter and who stands to benefit most?
  3. [contrarian] The non-obvious take
     What is the defensible but underexplored position on CRISPR for sickle cell disease?

3 angles · 2 claims accepted · 1 claims rejected · 1 contradictions detected · audit trail: audit_demo.jsonl
```

**Expected output from `audit_trail.jsonl`:** 5 JSON lines, each with `ts`, `gate_name`, `claim_id`, `decision_status`, `reason`, `evidence`. See `examples/output/audit_trail.jsonl` for a worked example.

---

## 3. Local testing — verify the prototype actually works

**Tests (7 files, 51 tests):**

```powershell
pytest -v
```

Expected:
- `test_audit_recorder.py` — 5/5
- `test_confirm_gate.py` — 5/5
- `test_creative_reframing.py` — 9/9
- `test_gates.py` — 12/12
- `test_transforms.py` — 11/11
- `test_videos.py` — 9/9

If anything fails, the prototype is broken — do not submit.

**Smoke test (manual, ~2 min):**

1. Run `python scripts/run_demo.py --topic "AI in creative industries"` — should print 3 angles + summary line.
2. Run `python scripts/run_demo.py --topic ""` (empty topic) — should not crash.
3. Run `python scripts/run_demo.py --topic "test" --out /tmp/test.jsonl` — should write a JSONL file at that path.
4. Open `audit_trail.jsonl` in any editor. Each line should be valid JSON.
5. Confirm 5 entries: 3 from evidence_gate + 1 from consistency_gate + 1 from publication_gate.

**Audit-trail validation:**

```powershell
python -c "import json; [json.loads(l) for l in open('audit_trail.jsonl')]; print('JSONL valid')"
```

If the output is "JSONL valid", every line is well-formed JSON.

**Cross-reference check (5 minutes before submission):**

- [ ] README.md has all 5 required sections (Problem / Solution / AI approach & architecture / Challenge theme / How Bob was used)
- [ ] `bob-sessions/01-codebase-exploration/transcript.md` exists and is raw Bob output
- [ ] `bob-sessions/02-creative-reframing-feature/transcript.md` exists
- [ ] `bob-sessions/03-tests-and-checks/transcript.md` exists
- [ ] `bob-sessions/04-demo-and-audit/transcript.md` exists
- [ ] `bob-sessions/05-confirm-gate/transcript.md` exists
- [ ] `bob-sessions/06-transform-catalog/transcript.md` exists
- [ ] `bob-sessions/07-video-vertical/transcript.md` exists
- [ ] `docs/architecture/architecture.md` exists
- [ ] `docs/architecture/architecture-diagram.mmd` exists
- [ ] `docs/demo/demo-story.md` exists
- [ ] `docs/submission-checklist.md` exists
- [ ] `docs/judge-pack/quick-brief.md` exists (after Boris writes it)
- [ ] `project-page/project-page.md` exists
- [ ] `Makefile` has `demo`, `test`, `install`, `clean` targets

---

## 4. Public launch — push to GitHub and submit

**Push to GitHub (Day 3 evening):**

```powershell
cd 'D:\IBM Project\Open_Production'
git init
git add .
git commit -m "Open Production v0.1 — IBM AI Builders Challenge July 2026"
git branch -M main
git remote add origin https://github.com/yourname/open-production.git
git push -u origin main
```

If you don't have a GitHub repo yet, create one at github.com/new. Name it `open-production` (or `pdt-july-challenge` — your call).

**Fill the Project Page on the platform (Day 3 evening, ~30 min):**

- URL: `https://aibuilderschallenge-bobhub.bemyapp.com/#/projects`
- Use the drafts at `project-page/project-page.md` (12.3 KB) — paste each section into the corresponding field.
- Project name: **Open Production**
- Track: **July — Reimagine Creative Industries with AI**
- Team: solo (you)

**Upload SkillsBuild cert (Day 3 evening):**

- The cert PDF should be at `bob-sessions/certificates/skillsbuild-cert.pdf` (you save this manually).
- Upload via Project Page Section 8.

**Submit (Day 4 morning, ~15 min):**

- Final QA: clone repo into a fresh dir, run `make install && make test && make demo`. All succeed.
- Verify Project Page links: GitHub repo (public), YouTube video (public, ≤3 min).
- Click "Submit" on the platform.
- Save confirmation email + screenshot the submitted page.

---

## What you do NOT need

- **No real LLM API key.** MockLLMClient is enough for v0.1 demo. Adding OpenAI/Anthropic is a v0.2 feature.
- **No Docker.** Judges don't require it. v0.2 if asked.
- **No CI.** Same.
- **No internet during demo.** The MockLLMClient is fully deterministic.
- **No PDT import.** PDT is inspiration citation only; the working prototype is the Bob-built code in `src/`.

---

## What can go wrong — and what to do

| Problem | Fix |
|---|---|
| `pytest` reports import errors | Run from project root: `cd 'D:\IBM Project\Open_Production' && pytest -v` |
| `make demo` exits 1 | Run with `--topic "..."` argument. Empty topic without flag should still work; check stderr. |
| `audit_trail.jsonl` empty | The demo runs the gates on a hardcoded fixture set. If empty, `scripts/run_demo.py` is broken — re-run Bob session 4. |
| Tests fail on a fresh clone | `python -m pip install pytest` (only external dep needed beyond stdlib). |
| Bob IDE can't find the workspace | Re-open Bob IDE, point at `D:\IBM Project\Open_Production\`. Bob session transcripts are in `bob-sessions/NN-*/transcript.md`. |
| Git push fails with auth error | Set up SSH key or personal access token. Standard GitHub flow. |

---

## Testing matrix — what to verify, by day

| Day | Test | Pass criterion |
|---|---|---|
| Day 0 (now) | `pytest -v` | 51/51 |
| Day 0 | `make demo` | prints 3 angles, summary line, exits 0 |
| Day 0 | `audit_trail.jsonl` | 5 entries, all valid JSON |
| Day 3 | Fresh clone test | `git clone`, `make install`, `make test`, `make demo` — all succeed |
| Day 3 | Demo video check | ≤3 min, audio present, links resolve |
| Day 4 | Final pre-submit | Project Page links resolve; Bob session transcripts readable |
| Day 4 | Submit | Confirmation email received |

---

## Quick reference — the single command that proves it works

```powershell
cd 'D:\IBM Project\Open_Production' && python -m pytest -v && python scripts/run_demo.py --topic "test topic" && python -c "import json; [json.loads(l) for l in open('audit_trail.jsonl')]; print('JSONL valid:', sum(1 for _ in open('audit_trail.jsonl')), 'entries')"
```

If that one command exits 0 and prints "JSONL valid: 5 entries" (or similar), the prototype is alive. Use this as your go/no-go gate before recording the demo video.

---

## What "tested" means in this submission

- **Unit tests** — 51/51 passing. Each module's behavior is verified in isolation.
- **Integration test** — `make demo` runs the full pipeline end-to-end with audit trail.
- **Smoke tests** — manual checks above (empty topic, custom output path, JSONL validation).
- **Audit trail** — every gate decision is recorded in JSONL format.

What's NOT tested (v0.2 concerns):
- Real LLM provider integration (MockLLMClient only).
- Cross-OS sandboxing.
- Concurrent / re-entrant behavior (acknowledged in Bob session 4).
- Performance under load.

Judges evaluating "Technical Execution" should see: working tests, working demo, working audit trail, clean architecture. We have all four.
