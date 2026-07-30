# How to Launch and Test — Open Production

Three launch contexts. Pick the one you need.

---

## 1. Browser launch — easiest for a general audience

This is the recommended path if you want a non-technical experience.

```powershell
# Step 1: navigate to the project
cd 'D:\IBM Project\Open_Production'

# Step 2: launch the browser demo
python src/public_demo/server.py
```

The browser opens at `http://127.0.0.1:8000/`. From there:

1. Enter a topic and click **"Show creative angles"**.
2. Pick skeptic, advocate, or contrarian.
3. Click **"Use this angle"** on the chosen card.
4. Review the gate results — accepted/rejected claims, contradictions detected.
5. The **production_id panel** appears — click **"Open in Agent Console →"** to see the live event log.

Two views are available via the `?view=` parameter:

- `http://127.0.0.1:8000/?view=guided` — Guided Production Flow (default)
- `http://127.0.0.1:8000/?view=console&production_id=<id>` — Agent Console

---

## 2. Terminal launch — run the prototype on your machine

**Prerequisites:** Python 3.10+ on Windows / macOS / Linux. Git. ~5 minutes.

```powershell
# Step 1: navigate to the project (or clone the public repo)
cd 'D:\IBM Project\Open_Production'

# Step 2: install dependencies (only pytest + stdlib extras)
python -m pip install -e .

# Step 3: run the test suite — 166 tests must pass
python -m pytest tests/ -q
# Expected: 166 passed in ~3s, 0 failures, 0 errors

# Step 4: start the browser demo
python src/public_demo/server.py
# Then open http://127.0.0.1:8000/?view=guided

# Step 5: inspect a demo audit trail (written on each finalize run)
# Look in output/public-demo/ for audit_<timestamp>.jsonl
```

**Expected output from the browser demo finalize:**
- Accepted/rejected/contradiction counts update
- Production_id panel shows the new production ID
- "Open in Agent Console →" link appears
- Clicking it opens `/?view=console&production_id=<id>` with live event log

---

## 3. Local testing — verify the prototype actually works

```powershell
python -m pytest tests/ -q
```

Expected (166 tests across 20 test files):

| File | Tests |
|---|---|
| `test_creative_reframing.py` | 9 |
| `test_gates.py` | 12 |
| `test_confirm_gate.py` | 5 |
| `test_audit_recorder.py` | 5 |
| `test_transforms.py` | 11 |
| `test_videos.py` | 9 |
| `test_production_service.py` | 8 |
| `test_demo_flow.py` | 6 |
| `test_view_switching.py` | 7 |
| `test_shot_designer.py` | ~6 |
| `test_character_director.py` | ~6 |
| `test_storyboard_artist.py` | ~6 |
| `test_environment_artist.py` | ~7 |
| `test_reviewer.py` | ~7 |
| `test_editor.py` | ~6 |
| `test_publisher.py` | ~8 |
| `test_voice_director.py` | 7 |
| `test_sound_designer.py` | 7 |
| `test_music_composer.py` | 8 |
| `test_colorist.py` | 9 |

If anything fails, the prototype is broken — do not submit.

**Smoke test (manual, ~2 min):**

1. Start `python src/public_demo/server.py`.
2. Open `http://127.0.0.1:8000/?view=guided` — the Guided Flow should load.
3. Submit the sample topic — three angle cards should appear.
4. Pick an angle — the gate result panel should appear with a production_id.
5. Click "Open in Agent Console →" — the Agent Console should load with the event list.
6. The left-rail Actors panel should show actors with event counts.

**Audit-trail validation:**

```powershell
# After a finalize run, audit files are in output/public-demo/
$latest = Get-ChildItem output/public-demo/*.jsonl | Sort-Object LastWriteTime -Desc | Select-Object -First 1
python -c "import json; entries=[json.loads(l) for l in open('$($latest.FullName)')]; print('JSONL valid:', len(entries), 'entries')"
```

---


## 3.5. CLI replay — `production timeline <id>`

The audit trail is the most novel property of Open Production. To make it
inspectable without the browser demo, the project ships a one-shot CLI:

```powershell
# Replay a production's audit trail as a readable timeline.
python -m src.cli.timeline prod_9915e6697a12

# Just the header + state progression + gate counts (skip the per-event table).
python -m src.cli.timeline prod_bd35b24041d6 --summary

# Emit a single JSON document for piping into jq / scripts.
python -m src.cli.timeline prod_bd35b24041d6 --json
```

The command searches `output/public-demo/`, `output/productions/`, and the
project root, so any production created by the browser demo or the
`ProductionService` is reachable by id. Pass an explicit path instead of an
id when the production lives elsewhere.

The CLI is intentionally small (one new module) and is the first of several
commands listed in `docs/plans/audit-2026-07-29.md` (`trace`, `doctor`,
`run`, `compare`, `plan-status`). Once `production timeline <id>` is in
place, the others reuse the same lookup helper.

## 4. Public launch — push to GitHub and submit

**Push to GitHub:**

```powershell
cd 'D:\IBM Project\Open_Production'
git init
git add .
git commit -m "Open Production v1.0 — IBM AI Builders Challenge July 2026"
git branch -M main
git remote add origin https://github.com/yourname/open-production.git
git push -u origin main
```

**Fill the Project Page on the platform (~30 min):**

- URL: `https://aibuilderschallenge-bobhub.bemyapp.com/#/projects`
- Project name: **Open Production**
- Track: **July — Reimagine Creative Industries with AI**

**Submit:**

- Final QA: clone repo into a fresh dir, run `python -m pip install -e . && python -m pytest tests/ -q`. All 166 tests pass.
- Verify Project Page links: GitHub repo (public), YouTube video (public, ≤3 min).
- Click "Submit" on the platform.
- Save confirmation email + screenshot the submitted page.

---

## What you do NOT need

- **No real LLM API key.** MockLLMClient is sufficient for the demo. All outputs are deterministic.
- **No Docker.** Judges don't require it.
- **No CI.** Same.
- **No internet during demo.** MockLLMClient is fully deterministic.
- **No Makefile.** All commands use `python` directly.

---

## What can go wrong — and what to do

| Problem | Fix |
|---|---|
| `pytest` reports import errors | Run from project root: `cd 'D:\IBM Project\Open_Production' && python -m pytest tests/ -q` |
| Server won't start on port 8000 | Another process using the port. Kill it or change port: `python src/public_demo/server.py` — check stderr. |
| Browser demo shows blank page | Hard refresh (Ctrl+Shift+R). Check server is running. |
| production_id panel doesn't appear | ProductionService storage path issue. Check `output/productions/` is writable. |
| Tests fail on a fresh clone | `python -m pip install -e .` (install the package first). |
| Git push fails with auth error | Set up SSH key or personal access token. Standard GitHub flow. |

---

## Testing matrix — what to verify, by day

| Day | Test | Pass criterion |
|---|---|---|
| Day 0 | `python -m pytest tests/ -q` | 166 passed, 0 failures |
| Day 0 | Browser demo end-to-end | 3 angles → pick → gates fire → production_id shows |
| Day 3 | Fresh clone test | `pip install -e . && pytest tests/ -q` — all pass |
| Day 3 | Demo video check | ≤3 min, audio present, links resolve |
| Day 4 | Final pre-submit | Project Page links resolve; Bob session transcripts readable |
| Day 4 | Submit | Confirmation email received |

---

## Quick reference — the single command that proves it works

```powershell
cd 'D:\IBM Project\Open_Production'
python -m pytest tests/ -q
# Expected: 166 passed in ~3s
python src/public_demo/server.py
# Then open http://127.0.0.1:8000/?view=guided and run a demo
```

---

## What "tested" means in this submission

- **Unit tests** — 166 tests, 20 test files, all passing. Each module's behavior is verified in isolation.
- **Integration test** — browser demo runs the full pipeline end-to-end with a dual-artifact audit trail.
- **Smoke tests** — manual checks above (angle selection, gate firing, production_id surfacing, Agent Console filter).
- **Audit trail** — every gate decision is recorded as append-only `AuditEntry` records in `audit.jsonl`.

What's NOT tested (post-submission concerns):

- Real LLM provider integration (MockLLMClient only — deterministic, no API key required).
- Cross-OS sandboxing.
- Concurrent / re-entrant behavior.
- Performance under load.

Judges evaluating "Technical Execution" should see: 166 working tests, working browser demo, live audit trail, clean production-crew architecture. We have all four.
