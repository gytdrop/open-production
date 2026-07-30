# Production Roadmap — Open Production

*Authored: 2026-07-30*
*Sources: open-production-plan.md v1.3, README.md, MEMORY.md, SYSTEM_HEALTH.md, docs/architecture/architecture.md, docs/principles.md, repository tree (624 tests, 9 Bob sessions, 21 agents)*
*Method: spec-driven-development + planning-and-task-breakdown*

---

## Assumptions I'm making (per spec-driven-development §Phase 1)

1. **A1** — "Production roadmap" means the post-submission delivery plan. The plan itself (v1.3) was the IBM AI Builders Challenge submission artefact. This document targets what runs *after* submission, organised by what closes real production gaps.
2. **A2** — Out of scope: platform registration, SkillsBuild certificate logistics, demo video recording, public GitHub repo configuration. These are submission-day tasks, not roadmap items.
3. **A3** — "Implementation task" follows the planning-and-task-breakdown shape: acceptance criteria, verification step, files likely touched, size (XS/S/M/L). No source code in this document; the task specs are enough for an engineer or agent to pick up.
4. **A4** — Size scale: **XS** = 1 file / single function or config; **S** = 1–2 files / one component or endpoint; **M** = 3–5 files / one vertical feature slice; **L** = 5–8 files / multi-component feature; anything larger must be split.
5. **A5** — Confidence per audit row is the lowest of three signals: (a) I read the file, (b) tests exist for it, (c) it is referenced by another live artefact. Rows that look complete in source but have no test are marked **Partial** rather than **Done**.
6. **A6** — Audit reflects the repo as it stands at HEAD on 2026-07-30. Anyone using this doc on a later date should re-run python -m pytest tests/ -q and git log --oneline -n 20 and confirm the counts before treating the audit as authoritative.
7. **A7** — Phase numbering is by *production readiness*, not by calendar time. Phases map to open-production-plan.md §23 (months 0–48+) but the roadmap here is dependency-ordered, not month-ordered.

---

## Part 1 — Feature audit

Status legend: ✅ **Done** — code present, tested, integrated · 🟡 **Partial** — code present but incomplete, untested, or stubbed · ⛔ **Missing** — referenced in plan, not implemented.

### 1.1 Foundation (Sections 1, 3, 4, 25, 26)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F1 | Product philosophy (5 Laws + 5% Rule) | ✅ | docs/principles.md:9-67 |
| F2 | Three design axioms | ✅ | docs/principles.md:71-91 |
| F3 | "Features that should NEVER be added" (8 items) | ✅ | docs/principles.md:107-129 |
| F4 | 10-product differentiators list | ✅ | docs/principles.md:135-141 |
| F5 | Progressive Depth Principle enforced in UI | 🟡 | stated in docs/principles.md:97-101; not exercised in web/src |

### 1.2 Information architecture (Sections 9 + 13)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F6 | Production Document dataclass + JSON schema | ✅ | src/schema/production_document.py:435 + docs/schema/production-document.schema.json |
| F7 | Studio/Production/Shot/Scene/Character/Environment/StyleToken/BrandKit/Timeline/Branch/Snapshot/AuditEntry | ✅ | src/schema/production_document.py |
| F8 | ConsistencyContract dataclass | ✅ | src/schema/production_document.py:130-138 |
| F9 | ColorSpec dataclass | ✅ | src/schema/production_document.py:223-230 |
| F10 | MoodSpec/CameraSpec/LightingSpec/AudioSpec/GenerationResult/CharacterReference | ✅ | src/schema/production_document.py:154-220 |
| F11 | Asset schema (image/video/audio/text/url) | ✅ | src/schema/production_document.py:90 + src/plugins/asset_type.py |

### 1.3 Production pipeline (Section 14 + Appendix G — 26 stages)

| # | Stage | Status | Evidence |
|---|---|---|---|
| F12 | Stage 2: Research | ✅ | src/agents/research_agent.py + tests |
| F13 | Stage 3: Reference clustering | ✅ | src/agents/reference_clustering.py + tests |
| F14 | Stage 4: Moodboard | ✅ | src/agents/moodboard.py + tests |
| F15 | Stage 5: Creative reframing (3 angles) | ✅ | src/agents/creative_reframing.py + 7 tests |
| F16 | Stage 6: Story structure | ✅ | src/agents/story.py + tests |
| F17 | Stage 7: Script | ✅ | src/agents/script.py + tests |
| F18 | Stage 8: Character direction | ✅ | src/agents/character_director.py + tests |
| F19 | Stage 9: Environment art | ✅ | src/agents/environment_artist.py + tests |
| F20 | Stage 10: Shot planning | ✅ | src/agents/shot_planner.py + tests |
| F21 | Stage 11: Shot design | ✅ | src/agents/shot_designer.py + tests |
| F22 | Stage 12: Storyboarding | ✅ | src/agents/storyboard_artist.py + tests |
| F23 | Stage 13: Voice direction | ✅ | src/agents/voice_director.py + tests |
| F24 | Stage 14: Sound design | ✅ | src/agents/sound_designer.py + tests |
| F25 | Stage 15: Asset library | ✅ | src/agents/asset_library.py + tests |
| F26 | Stage 16: Generation | ✅ | src/agents/generation.py + tests |
| F27 | Stage 17: Music composition | ✅ | src/agents/music_composer.py + tests |
| F28 | Stage 18: Animation direction | ✅ | src/agents/animation_director.py + tests |
| F29 | Stage 19: Color grading | ✅ | src/agents/colorist.py + tests |
| F30 | Stage 20: Editor (cut assembly) | ✅ | src/agents/editor.py + tests |
| F31 | Stage 21: Timeline assembly | ✅ | production_service.commit_editor_proposal + tests |
| F32 | Stage 22: Publish manifests | ✅ | src/agents/publisher.py + tests |
| F33 | Stage 23: Reviewer (5 check types) | ✅ | src/agents/reviewer.py + tests |
| F34 | Stage 24: Branching | 🟡 | ProductionService.create_branch()/merge(); no visual merge UI |
| F35 | Stage 25: Publishing | 🟡 | src/agents/publisher.py; no actual platform push |
| F36 | Stage 26: Archiving + retention | ✅ | ProductionService.archive() |
| F37 | Confirm gate (interactive pause) | ✅ | src/agents/confirm_gate.py + tests |

**Pipeline completeness note:** The 26 stages run end-to-end via src/service/pipeline_runner.py::PipelineRunner.run() (Stages 2→22) and src/demo_flow.py::run_pipeline(). Stages 23–26 are exercised in uild_demo_report(). The **research-writing vertical** runs with real write-back; the **video vertical** is a *placeholder* (src/videos/render.py writes text-described PNG frame descriptions, not real frames).

### 1.4 State management (Section 16)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F38 | ProductionState enum (DRAFT → BRIEFED → IN_PRODUCTION → IN_REVIEW → APPROVED → PUBLISHED) | ✅ | src/schema/production_document.py:36-39 |
| F39 | Forward-only transitions + IN_REVIEW → IN_PRODUCTION revision loop | ✅ | production_service.py::_ALLOWED_TRANSITIONS |
| F40 | State-transition AuditEntry required | ✅ | production_service.py::apply_event |
| F41 | Per-state gate prerequisites | ✅ | production_service.py::_GATE_CHECKS |
| F42 | Dual-artifact output (production.json + audit.jsonl) | ✅ | ProductionService.save() |
| F43 | Atomic file I/O with retry (Windows-safe) | ✅ | production_service.py::_safe_replace |
| F44 | SHA-256 content hash sidecar | ✅ | ProductionService.save() |
| F45 | Per-instance RLock for concurrent save within process | ✅ | production_service.py::transaction() + 	ests/test_concurrent_save.py |
| F46 | Cross-process file locking | ⛔ | SYSTEM_HEALTH.md architectural risks §2 |
| F47 | Snapshot + branching | ✅ | ProductionService.snapshot()/create_branch() |
| F48 | Audit replay from JSONL | 🟡 | log() reads but no end-to-end replay test for arbitrary productions |
| F49 | Structured logging | ⛔ | SYSTEM_HEALTH.md recommendations §Monitoring |

### 1.5 Agent collaboration (Section 15)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F50 | BaseAgent + ScopeViolation | ✅ | src/agents/base.py |
| F51 | WRITABLE_FIELDS enforcement (K.11 Rule 2) | ✅ | src/agents/base.py::_enforce_scope |
| F52 | Single-method interface un(input) → output (K.11 Rule 1) | ✅ | src/agents/base.py::run |
| F53 | Never raises on empty input (K.11 Rule 4) | ✅ | All 21 agents pass un({}) smoke |
| F54 | ationale mandatory in every proposal (K.11 Rule 5) | ✅ | src/agents/base.py::_enforce_scope |
| F55 | Proposal-first / human-approve workflow (K.11 Rule 3) | 🟡 | Works in demo flow; no general-purpose approval queue API |
| F56 | 10 agent scope contracts (Appendix K) | ✅ | open-production-plan.md:appendix-K |
| F57 | ReviewerAgent 5 check types (Appendix J) | ✅ | src/agents/reviewer.py |
| F58 | Cross-agent call prevention | ✅ | Architectural rule, no direct import paths |
| F59 | General approval-queue API on ProductionService | ⛔ | No propose()/approve_proposal()/reject_proposal() |

### 1.6 Plugins & extensibility (Sections 17–18)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F60 | Four plugin surfaces (Generation/ExportFormat/AssetType/AgentRole) | ✅ | src/plugins/ |
| F61 | PluginRegistry with health-check + auto-disable | ✅ | src/plugins/registry.py |
| F62 | GenerationPlugin Protocol + MockGenerationPlugin | ✅ | src/plugins/generation.py |
| F63 | ExportFormatPlugin Protocol + JSON + MP4-placeholder | ✅ | src/plugins/export_format.py |
| F64 | AssetTypePlugin Protocol + Image/Video/Audio/Document | ✅ | src/plugins/asset_type.py |
| F65 | AgentRolePlugin Protocol + CustomReviewer + ComplianceReviewer | ✅ | src/plugins/agent_role.py |
| F66 | CostEstimate + capability-based plugin selection | 🟡 | src/plugins/generation.py; no per-shot routing logic |
| F67 | Real RunwayPlugin/VeoPlugin/PikaPlugin adapters | ⛔ | None present |
| F68 | Real Mp4ExportPlugin (encode ffmpeg pipeline) | ⛔ | Mp4PlaceholderPlugin only |
| F69 | Plugin discovery from external packages (entry points) | ⛔ | PluginRegistry.register() is manual only |
| F70 | Plugin health-check scheduler | ⛔ | health_check_all() exists; no cron |
| F71 | Plugin telemetry (per-shot cost / latency aggregation) | ⛔ | CostEstimate returned per-call but never aggregated |

### 1.7 Transforms (Section 5 — kernel primitives)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F72 | Transform Protocol + TransformResult | ✅ | src/transforms/base.py |
| F73 | Transform registry with egister_transform() | ✅ | src/transforms/registry.py |
| F74 | text.summary / text.word_count / text.upper | ✅ | src/transforms/text/ + 11 tests |
| F75 | filter.dedupe / filter.require_source | ✅ | src/transforms/filter/ |
| F76 | compose.sequence (DAG of transforms) | ✅ | src/transforms/compose/sequence.py |
| F77 | Image transforms (resize, crop, normalise) | ⛔ | None |
| F78 | Audio transforms (loudness-normalise, transcribe) | ⛔ | None |
| F79 | Video transforms (transcode, thumbnail, scene-detect) | ⛔ | None |
| F80 | VisualQualityGate (video vertical) | ✅ | src/videos/quality_evaluation.py |

### 1.8 Frontend views (Section 10 + Appendix C)

| # | View | Status | Evidence |
|---|---|---|---|
| F81 | Guided Production Flow | ✅ | web/src/views/GuidedFlow/ (7 stage components) |
| F82 | Agent Console | ✅ | web/src/views/AgentConsole/ (12 components) |
| F83 | Director's Canvas | ⛔ | Wireframe only (docs/wireframes/01-directors-canvas.svg) |
| F84 | Timeline Editor | ⛔ | Wireframe only (docs/wireframes/03-timeline-editor.svg) |
| F85 | Node Graph | ⛔ | Wireframe only (docs/wireframes/05-node-graph.svg) |
| F86 | Per-view route + lossless view switching | 🟡 | React Router wired for /flow and /console; canvas/timeline/graph 404 |
| F87 | Zustand store with audit dedup + generation counter | ✅ | web/src/store/productionStore.ts |
| F88 | useProductionApi hook with reframe / finalize / status | ✅ | web/src/hooks/useProductionApi.ts |
| F89 | useAuditPoll (5-second polling) | ✅ | web/src/hooks/useAuditPoll.ts |
| F90 | WebSocket / SSE for sub-5s event latency | ⛔ | SYSTEM_HEALTH.md blockers |
| F91 | Per-actor left-rail filter in Agent Console | ✅ | Bob session 09 |
| F92 | Mobile companion view | ⛔ | Wireframes README §intentionally NOT |

### 1.9 CLI surface (Section 19)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F93 | Dispatcher python -m src.cli | ✅ | src/cli/__main__.py |
| F94 | production timeline <prod_id> — audit replay | ✅ | src/cli/timeline.py + tests |
| F95 | production trace <sha256> — asset lineage | ✅ | src/cli/trace.py + tests |
| F96 | production doctor [prod\|--all] — health report | 🟡 | src/cli/doctor.py + tests; one known yellow on consistency_contract_gate (MEMORY.md) |
| F97 | production compare <a> <b> — side-by-side diff | ✅ | src/cli/compare.py + tests |
| F98 | production run "<intent>" — full pipeline from intent | ✅ | src/cli/run.py + tests |
| F99 | production list — enumerate productions on disk | ✅ | src/cli/list.py + tests |
| F100 | production doctor consistency_contract_gate fix | 🟡 | Open loop in MEMORY.md |

### 1.10 Demo / public server

| # | Feature | Status | Evidence |
|---|---|---|---|
| F101 | src/public_demo/server.py ThreadingHTTPServer | ✅ | src/public_demo/server.py |
| F102 | /api/reframe, /api/finalize endpoints | ✅ | server.py |
| F103 | /api/production/:id/{status,log,proposals,approve} | 🟡 | status/log/proposals done; approve is best-effort |
| F104 | SPA static serving from web/dist/ | ✅ | server.py _serve_static |
| F105 | CORS + OPTIONS preflight | ✅ | SYSTEM_HEALTH.md confirms after fixes |
| F106 | Health endpoint /healthz | ⛔ | SYSTEM_HEALTH.md recommendations |
| F107 | Authentication / rate limiting | ⛔ | Explicitly absent (README.md Concurrency limits) |
| F108 | Concurrency smoke (single process) | ✅ | 	ests/test_concurrent_save.py (8 threads × 25 saves) |

### 1.11 Video vertical (Section 14, vertical #2)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F109 | Frame/Shot/VideoClip/VideoIntent primitives | ✅ | src/videos/primitives.py |
| F110 | ShotComposition (DAG planner) | ✅ | src/videos/composition.py |
| F111 | FrameRenderTransform | 🟡 | Text frame descriptions; not real pixels (src/videos/render_transform.py) |
| F112 | VisualQualityGate | ✅ | src/videos/quality_evaluation.py |
| F113 | ender_video() end-to-end entry | 🟡 | Text artifacts only; no actual MP4 (src/videos/render.py) |
| F114 | 9 video tests | ✅ | 	ests/test_videos.py |

### 1.12 Tests & CI

| # | Feature | Status | Evidence |
|---|---|---|---|
| F115 | 624 tests passing | ✅ | python -m pytest tests/ -q (2026-07-30) |
| F116 | One focused test file per agent | ✅ | 21 	est_<agent>.py files |
| F117 | Concurrency smoke | ✅ | 	ests/test_concurrent_save.py |
| F118 | Consistency violation fixture | ✅ | 	ests/test_consistency_violation_fixture.py + output/consistency_violation/ |
| F119 | View-switching tests | ✅ | 	ests/test_view_switching.py |
| F120 | Fuzz harness | ✅ | 	ests/__fuzz.py |
| F121 | CI pipeline (GitHub Actions / GitLab / similar) | ⛔ | No .github/workflows/ / .gitlab-ci.yml |
| F122 | TypeScript CI (	sc --noEmit, eslint --max-warnings 0) | ⛔ | Local config only (web/tsconfig.json, web/eslint.config.js) |
| F123 | Frontend test framework (Vitest + RTL) | ⛔ | SYSTEM_HEALTH.md recommendations |
| F124 | Coverage threshold enforcement | ⛔ | No pytest --cov-fail-under config |
| F125 | Mypy strict on service + schema | ⛔ | SYSTEM_HEALTH.md recommendations |

### 1.13 Customization & studio system (Section 12 + Appendix H)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F126 | StyleToken / BrandKit dataclasses | ✅ | src/schema/production_document.py:139-152 |
| F127 | style_library.py service | ✅ | src/service/style_library.py + tests |
| F128 | sset_library_service.py | ✅ | src/service/asset_library_service.py + tests |
| F129 | Style-token UI (visual palette picker) | ⛔ | Wireframes README §intentionally NOT |
| F130 | Studio Library cross-production UI | ⛔ | Wireframes README §intentionally NOT |
| F131 | Consistency Contract visual editor | ⛔ | Wireframes README §intentionally NOT |
| F132 | 7-customization-category framework | 🟡 | Described in docs/principles.md; not all 7 wired in service |
| F133 | Multi-user studios (shared brand kits) | ⛔ | Single-user only |

### 1.14 Documentation & demos

| # | Feature | Status | Evidence |
|---|---|---|---|
| F134 | open-production-plan.md v1.3 | ✅ | 26 outputs + 11 appendices |
| F135 | docs/architecture/architecture.md | ✅ | 320 lines |
| F136 | docs/architecture/architecture-diagram.mmd | ✅ | Mermaid source |
| F137 | docs/principles.md | ✅ | Laws + axioms + never-list |
| F138 | 5 wireframes (SVG + PNG) | ✅ | docs/wireframes/ |
| F139 | Submission checklist | ✅ | docs/submission-checklist.md |
| F140 | Demo story + shot list | ✅ | docs/demo/demo-story.md, docs/demo/90-second-script.md |
| F141 | Judge pack (one-pager + differentiators) | ✅ | docs/judge-pack/ |
| F142 | 9 Bob session transcripts | ✅ | ob-sessions/01-09/ |
| F143 | Demo video recording | 🟡 | docs/demo/recording-guide.md exists; video not yet recorded |
| F144 | API reference doc (auto-generated) | ⛔ | No Sphinx / MkDocs / TypeDoc config |
| F145 | User research plan | 🟡 | Protocol written; interviews pending (docs/research/user-research-plan.md) |
| F146 | Pipeline validation plan | 🟡 | Protocol written; sessions pending (docs/research/pipeline-validation-plan.md) |
| F147 | User research interviews (4 personas) | ⛔ | ACT-1 pending post-submission |
| F148 | Pipeline validation session (practicing video producer) | ⛔ | P0-4 pending post-submission |

### 1.15 Research, risks, roadmap, moonshots (Sections 5, 6, 20, 21, 22, 23, 24)

| # | Feature | Status | Evidence |
|---|---|---|---|
| F149 | 9 technical risks documented | ✅ | open-production-plan.md §20 |
| F150 | 8 UX risks documented | ✅ | open-production-plan.md §21 |
| F151 | 5-phase roadmap (months 0–48+) | 🟡 | Described in plan §23; this doc operationalises it |
| F152 | 7 moonshots listed | ✅ | open-production-plan.md §24 |
| F153 | Scalability section (Section 19) | ✅ | plan §19 |
| F154 | Research opportunities section (Section 22) | ✅ | plan §22 |

---

## Audit summary

| Bucket | Count |
|---|---|
| ✅ Done | 105 |
| 🟡 Partial | 19 |
| ⛔ Missing | 30 |

The **Done** count is inflated by the breadth of the agent and gate layers — both fully implemented and tested. The **Missing** items cluster around: real integrations (LLM, generation backends, encode pipeline), 3 of 5 frontend views, multi-user collaboration, CI infrastructure, and the productionisation gaps flagged in SYSTEM_HEALTH.md (cross-process locking, structured logging, auth/rate limiting, frontend tests).

The single highest-leverage gap is **F83/F84/F85 (Director's Canvas, Timeline Editor, Node Graph)** — these are the visual surface that makes the production crew legible. Without them, the system reads as "audit log + buttons" rather than "production environment." This is also the work most defensible from a planning-and-task-breakdown standpoint: wireframes exist, scope is bounded, dependencies are clear.

---

## Part 2 — Production roadmap (post-submission delivery plan)

Phases are ordered by *production dependency*, not calendar time. Each phase closes into a checkpoint where the system remains shippable end-to-end (vertical slicing per planning-and-task-breakdown).

### Phase R0 — Stability & production hardening *(closes the SYSTEM_HEALTH.md blockers)*

**Goal:** the demo server and CLI dispatcher are safe to point at by real users without cross-process races, missing health signals, or silent failures.

**Vertical slice:** doctor reports green for a clean production → all flags propagate to the HTTP server → /healthz answers green → concurrent processes don't lose writes.

#### Tasks

**R0-T1 — Cross-process file lock helper**
- **Description:** Implement cross_process_lock(path) using msvcrt.locking on Windows and cntl.flock on POSIX. Wrap ProductionService.save() so the lock is held across the temp+rename cycle. Make it best-effort (warn on missing permissions rather than crash on read-only filesystems).
- **Acceptance:**
  - [ ] Two ProductionService instances writing to the same <id>/ directory complete without [WinError 5] on Windows.
  - [ ] Same on POSIX with two parallel python processes.
  - [ ] Read-only filesystems emit a clear warning, not a crash.
- **Verify:** extend 	ests/test_concurrent_save.py with a multi-process test using subprocess; manual: launch two python src/public_demo/server.py against the same output/productions/ and run production run 10× concurrently.
- **Files:** src/service/production_service.py, 	ests/test_concurrent_save.py.
- **Size:** M.

**R0-T2 — /healthz endpoint + structured logging**
- **Description:** Add GET /healthz route to src/public_demo/server.py returning JSON {status, version, storage_writable, productions_count, last_save_at}. Replace ad-hoc sys.stderr.write calls with logging.getLogger("open_production") configured to emit JSON lines with equest_id, oute, status, duration_ms.
- **Acceptance:**
  - [ ] curl http://127.0.0.1:8000/healthz returns 200 JSON with all five fields populated.
  - [ ] Each request emits one structured log line.
  - [ ] Log lines parse via python -c "import json,sys; [json.loads(l) for l in sys.stdin]".
- **Verify:** manual curl + new 	ests/test_healthz.py.
- **Files:** src/public_demo/server.py, new src/public_demo/logging_config.py, 	ests/test_healthz.py.
- **Size:** S.

**R0-T3 — Replace silent except Exception: pass in uild_demo_report**
- **Description:** Every swallow in src/demo_flow.py (13 stage write-back blocks per SYSTEM_HEALTH.md) must log at WARNING level with the stage name and exception class. The runtime path stays best-effort; the observability gap closes.
- **Acceptance:**
  - [ ] Zero bare except Exception: pass blocks remain in src/demo_flow.py (search confirms).
  - [ ] Each swallowed exception produces one logging.warning(...) line including stage=<name>, error_class=<cls>, error_msg=<msg>.
  - [ ] Pipeline still completes a demo run when one stage's service mirror is broken.
- **Verify:** grep -n 'except Exception: pass' src/demo_flow.py returns empty; pytest tests/test_demo_flow.py -q stays green.
- **Files:** src/demo_flow.py.
- **Size:** S.

**R0-T4 — production doctor consistency_contract_gate fix**
- **Description:** Per MEMORY.md open loop, production doctor reports YELLOW on consistency_contract_gate while the gate's actual name in the trail is consistency_contract. Fix the lookup to match the recorded name (or rename the gate consistently — pick one).
- **Acceptance:**
  - [ ] production doctor prod_<id> reports green on the consistency contract row for a healthy production.
  - [ ] A production with a known contract violation reports yellow/red correctly.
- **Verify:** extend 	ests/test_cli_doctor.py with a fixture that triggers the renamed gate.
- **Files:** src/cli/doctor.py, possibly src/validation/gates.py, 	ests/test_cli_doctor.py.
- **Size:** XS.

**R0-T5 — Audit replay from JSONL**
- **Description:** ProductionService.log() reads JSONL but there is no end-to-end replay test. Add eplay(audit_path) -> Production that reconstructs state from a JSONL alone, then add a round-trip test: create a production, mutate it 50 times, drop production.json, run eplay, confirm reconstructed state matches the last-saved state.
- **Acceptance:**
  - [ ] eplay() returns a Production dataclass equivalent (deep-equal) to the saved one.
  - [ ] Replay is idempotent: running it twice returns the same Production.
  - [ ] Replay surfaces an explicit error for malformed JSONL, never silent drop.
- **Verify:** pytest tests/test_audit_recorder.py::test_replay_roundtrip -q.
- **Files:** src/service/production_service.py, src/audit/recorder.py, 	ests/test_audit_recorder.py.
- **Size:** M.

**Checkpoint after R0:** pytest tests/ -q green; production doctor --all green for all in-repo fixtures; python src/public_demo/server.py + concurrent python -m src.cli run write 100 productions with zero [WinError 5]; /healthz returns JSON. Review with maintainer before opening R1.

### Phase R1 — Proposal/approval API + agent conversation protocol *(closes F55, F59)*

**Goal:** every agent's proposals list is a first-class object on the production — proposable, approvable, rejectable, diffable. The Agent Console becomes a real workspace, not a transcript viewer.

**Vertical slice:** Editor agent returns 3 cut proposals → they appear as 3 cards in the Console → user approves one → Shot.duration_sec mutates → audit entry records the approval → next agent sees the new state.

#### Tasks

**R1-T1 — ProductionService.propose() / pprove_proposal() / eject_proposal()**
- **Description:** Extend ProductionService with three new methods wrapping pply_event. Proposals become durable records in the production (proposals: list[PendingProposal]) with {proposal_id, agent_id, proposed_at, payload, status: pending|approved|rejected, decided_at, decided_by, applied_event_id}. Rejection is non-destructive: the original duration stays.
- **Acceptance:**
  - [ ] Three new methods exist with these signatures: propose(prod, agent_id, payload) -> proposal_id; pprove(prod, proposal_id, actor) -> prod; eject(prod, proposal_id, actor, reason) -> prod.
  - [ ] Approving applies the proposal through pply_event and records both the proposal and the application in udit_trail.
  - [ ] Rejecting does not mutate the underlying production fields; only the proposal status.
  - [ ] Two approvals of the same proposal_id raises a clear StateError.
- **Verify:** new 	ests/test_proposal_lifecycle.py covering: propose → approve, propose → reject → re-propose, double-approve raises.
- **Files:** src/schema/production_document.py (add PendingProposal), src/service/production_service.py, 	ests/test_proposal_lifecycle.py.
- **Size:** M.

**R1-T2 — Wire demo_flow.build_demo_report through propose/approve**
- **Description:** Replace the _mirror() best-effort path with explicit propose() calls per agent. When chosen_angle is set, walk back and pprove() the CreativeReframing proposal; same for editor, environment, shot planner, colorist, etc. Net behaviour unchanged for the fixture flow; net behaviour for the interactive flow (post R1-T3) becomes auditable.
- **Acceptance:**
  - [ ] udit.jsonl for a demo run now contains proposal_pending, proposal_approved, proposal_rejected events alongside existing gate_decision and state_transition.
  - [ ] The full proposal/approval chain is reconstructable by walking udit.jsonl alone.
- **Verify:** pytest tests/test_demo_flow.py::test_proposal_audit_chain -q (new); manual: python -m src.cli run "demo topic" --no-confirm --pick advocate and inspect udit.jsonl.
- **Files:** src/demo_flow.py, 	ests/test_demo_flow.py.
- **Size:** M.

**R1-T3 — Frontend proposal cards wired to API**
- **Description:** Extend useProductionApi with propose(agentId, payload), pprove(proposalId), eject(proposalId, reason). Add pendingProposals: Proposal[] and proposalError: string | null to the Zustand store. Replace ProposalCard placeholder markup with real approval buttons that hit these endpoints. Surface rejections inline in the Conversation Thread with the agent's rationale and the user's reason.
- **Acceptance:**
  - [ ] Clicking Approve on a ProposalCard mutates the production; the card moves to a "decided" state with timestamp.
  - [ ] Rejecting shows an inline form for the reason; empty reason is rejected client-side.
  - [ ] Rejected proposals do not mutate state; the production's pre-decision values are unchanged.
  - [ ] Reload preserves decision state (read from udit.jsonl).
- **Verify:** new web/tests/ProposalCard.test.tsx (Vitest + RTL after R5-T2 lands); manual: open Console, run a fresh production, exercise approve/reject on at least 3 cards.
- **Files:** web/src/hooks/useProductionApi.ts, web/src/store/productionStore.ts, web/src/components/ProposalCard.tsx, web/src/views/AgentConsole/ConversationThread.tsx.
- **Size:** M.

**R1-T4 — Approval queue semantics: ordering, expiry, multi-user**
- **Description:** Add proposal_expires_at (default 24h after pending). Add a sweeper that marks stale proposals as expired (non-destructive). When two users approve the same proposal, the second raises a clear ConflictError and surfaces it in the Console.
- **Acceptance:**
  - [ ] Pending proposals older than their expiry surface as "expired" in the Console (distinct visual state).
  - [ ] Double-approve raises and is shown to the user, not silently swallowed.
  - [ ] Expired proposals can still be approved if the user explicitly does so (override semantics).
- **Verify:** pytest tests/test_proposal_lifecycle.py::test_expiry -q, ::test_double_approve_conflict -q.
- **Files:** src/service/production_service.py, 	ests/test_proposal_lifecycle.py.
- **Size:** S.

**Checkpoint after R1:** the Agent Console can drive an end-to-end production interactively (not just auto-confirm). production run --no-confirm and a manual click-through produce the same final production. Review with maintainer before R2.

### Phase R2 — Complete the frontend (3 missing views)

**Goal:** all 5 views from §10 shippable. Each view reads from the same Production state; switching views is instant and lossless (Axiom 2).

**Vertical slice (per view):** pick a representative scene with shots locked → open in Director's Canvas → rearrange shots → switch to Timeline Editor → the new order is reflected → switch to Node Graph → the editor's cut proposal appears as an approved node → switch to Agent Console → a state_transition audit entry records the reorder.

#### Tasks — Director's Canvas (F83)

**R2-T1 — Canvas primitive + Zustand view-state slice**
- **Description:** Add a canvas abstraction (use eact-zoom-pan-pinch or implement minimal pan/zoom/select on a <svg>). Add canvasViewState: {pan, zoom, selectedShotId, hoverSceneId} to the production store. Each scene is a <g> containing shot cards as <rect> + <text>; references float as small anchored <circle>s.
- **Acceptance:**
  - [ ] Mouse wheel zoom and click+drag pan work smoothly with 30+ shots on canvas.
  - [ ] Clicking a shot card sets selectedShotId; clicking empty space clears it.
  - [ ] Pan/zoom survives view switches (stored in production store, not local component state).
- **Verify:** manual in dev; new web/tests/canvas.test.tsx.
- **Files:** web/src/views/Canvas/ (new), web/src/store/productionStore.ts, web/src/App.tsx (route).
- **Size:** L.

**R2-T2 — Properties right-rail**
- **Description:** 340-px right panel that shows the selected shot's CameraSpec, LightingSpec, AudioSpec, ersion_history, eviewer_verdict. Each section is collapsible. Edits write back through useProductionApi.updateShot(shotId, patch) and emit a decision audit entry.
- **Acceptance:**
  - [ ] Selecting a shot populates the panel within one frame.
  - [ ] Editing a camera focal length and pressing Enter mutates the production and an audit entry appears in the Console within one poll cycle.
  - [ ] Unsaved edits show a subtle "modified" indicator; switching views surfaces a "discard?" prompt.
- **Verify:** web/tests/canvas-properties.test.tsx.
- **Files:** web/src/views/Canvas/PropertiesRail.tsx (new), web/src/hooks/useProductionApi.ts.
- **Size:** M.

**R2-T3 — AI proposal popovers on canvas**
- **Description:** When an agent returns a proposal that targets the currently visible shot/scene, render a floating card near the affected element with Approve / Adjust / Reject buttons. The popover is positioned with getBoundingClientRect() and respects canvas pan/zoom.
- **Acceptance:**
  - [ ] A new proposal for a visible shot shows a popover within 2 seconds of the proposal arriving (next poll cycle).
  - [ ] Approving applies the change and the popover disappears.
  - [ ] Rejecting dismisses the popover and records a rejection reason.
- **Verify:** manual + web/tests/canvas-popover.test.tsx.
- **Files:** web/src/views/Canvas/ProposalPopover.tsx (new).
- **Size:** M.

#### Tasks — Timeline Editor (F84)

**R2-T4 — Timeline shell + 5-track layout**
- **Description:** Top tabs (Scene 1, 2, 3, …), left asset bin (Video / Audio / Music / SFX / Voice sections, 180 px), center timeline (V1 / V2 / A1 / A2 / A3 tracks with horizontal ruler and clip blocks), right Inspector (300 px) for selected clip, bottom transport controls (playhead, in/out markers, scrub).
- **Acceptance:**
  - [ ] All shots from the active scene appear as clip blocks in correct track order.
  - [ ] Drag-drop reordering clips emits an audit entry and persists.
  - [ ] In/out markers highlight the current selection in green.
- **Verify:** web/tests/timeline.test.tsx.
- **Files:** web/src/views/Timeline/ (new), web/src/App.tsx (route).
- **Size:** L.

**R2-T5 — Timeline Inspector + transport controls**
- **Description:** Inspector shows the selected clip's timing, transition, audio, speed, reviewer verdict. Transport controls include playhead drag, in/out set, frame-step. Spacebar plays/pauses (mock playback — no real audio yet).
- **Acceptance:**
  - [ ] Clicking a clip populates the Inspector within one frame.
  - [ ] Pressing Space toggles a play state visible in the UI (no audio yet).
  - [ ] Frame-step buttons advance the playhead by exactly one shot duration.
- **Verify:** web/tests/timeline-inspector.test.tsx.
- **Files:** web/src/views/Timeline/Inspector.tsx, web/src/views/Timeline/Transport.tsx.
- **Size:** M.

#### Tasks — Node Graph (F85)

**R2-T6 — DAG layout + node types**
- **Description:** Use dagre or a hand-rolled topological layout to position nodes (transform = blue, composition = violet, evaluation = green, reviewer = magenta, gate = red). Edges labelled with data-flow names (camera_spec, lighting_spec, quality_verdict.json). Right rail: Node Inspector for selected node with metadata, inputs, outputs, status, provenance, and the three safe actions (Approve override / Re-run / Branch).
- **Acceptance:**
  - [ ] For a production with 10+ agents, the graph renders in < 500 ms and is readable.
  - [ ] Selecting a node shows its inputs/outputs/provenance.
  - [ ] Branch action creates a ranch audit entry and the new branch appears in the graph as a sub-DAG.
- **Verify:** web/tests/nodegraph.test.tsx.
- **Files:** web/src/views/NodeGraph/ (new), web/src/App.tsx (route).
- **Size:** L.

**R2-T7 — Cross-view consistency harness**
- **Description:** Add an integration test (Vitest + RTL) that: creates a production, opens the Director's Canvas, reorders two shots, switches to Timeline Editor, asserts the new order is reflected, switches to Node Graph, asserts the editor's node shows the approved reorder, switches to Agent Console, asserts the audit entry is present.
- **Acceptance:**
  - [ ] Test runs in < 5 seconds.
  - [ ] Asserts the universal-rule property from docs/wireframes/README.md: "Switching between views is instant. No data is lost when switching."
- **Verify:** web/tests/views-cross.test.tsx.
- **Files:** web/tests/views-cross.test.tsx.
- **Size:** M.

**Checkpoint after R2:** all 5 wireframes have working implementations. A user can drive a production from intent to publish across any view; each transition is lossless. Review with maintainer before R3.

### Phase R3 — Plugin ecosystem & real backends (F67–F71)

**Goal:** Open Production is no longer a single-process prototype. Real LLM, real generation backends, real export pipelines can be plugged in without changing the kernel.

**Vertical slice:** install open-production-runway-plugin → it auto-registers → production run --backend runway uses Runway for video generation → the cost appears in udit.jsonl → the user can switch backends without changing the production data model.

#### Tasks

**R3-T1 — Plugin entry-point discovery**
- **Description:** Extend PluginRegistry to load plugins via importlib.metadata.entry_points(group="open_production.plugins"). Each plugin's module declares its plugin_category, 
ame, capabilities. Add python -m src.cli plugins list to enumerate discovered plugins.
- **Acceptance:**
  - [ ] A package that declares entry_points={"open_production.plugins": ["runway_v1 = my_pkg:RunwayPlugin"]} is auto-registered on first PluginRegistry() instantiation.
  - [ ] production plugins list shows name, category, capabilities, health.
  - [ ] Plugins that fail health_check() at startup appear in disabled_plugins().
- **Verify:** pytest tests/test_plugin_registry.py::test_entry_point_discovery -q with a fixture package.
- **Files:** src/plugins/registry.py, src/cli/__main__.py (add plugins subcommand), 	ests/test_plugin_registry.py.
- **Size:** M.

**R3-T2 — LLM client protocol + default adapter**
- **Description:** Define LLMClient Protocol (complete(prompt, *, temperature, max_tokens) -> str, embed(text) -> list[float], health_check() -> PluginHealth). Replace the scattered MockLLMClient with src/tools/llm_client.py::LLMClient and a get_default_client() that returns OpenAIClient when OPENAI_API_KEY is set, else MockLLMClient. Add an AnthropicClient adapter that conforms to the same Protocol.
- **Acceptance:**
  - [ ] LLMClient is @runtime_checkable Protocol; both MockLLMClient and OpenAIClient pass isinstance.
  - [ ] get_default_client() selection is logged at startup.
  - [ ] AnthropicClient ships with a passing integration test (offline).
  - [ ] All 21 agents' un() methods that accept an injected LLM continue to work with both backends.
- **Verify:** pytest tests/test_llm_client.py -q; manual with OPENAI_API_KEY set, run production run "demo topic" --no-confirm --pick advocate and confirm udit.jsonl shows non-mock LLM calls.
- **Files:** src/tools/llm_client.py, src/tools/openai_client.py (new), src/tools/anthropic_client.py (new), 	ests/test_llm_client.py.
- **Size:** M.

**R3-T3 — First real GenerationPlugin adapter (Runway Gen-3)**
- **Description:** Implement one real GenerationPlugin adapter (Runway Gen-3 is the most likely target). It must: poll the backend's status endpoint, write the resulting MP4 to a content-addressed store under output/assets/<sha256>.mp4, surface a CostEstimate, run health_check() against the API on registration.
- **Acceptance:**
  - [ ] eg.register(RunwayPlugin()) succeeds when RUNWAY_API_KEY is set.
  - [ ] eg.health_check_all() returns healthy=True for a valid key, healthy=False with reason for an invalid key.
  - [ ] eg.by_capability(PluginCategory.GENERATION, PluginCapability.VIDEO) returns the Runway plugin for video shots.
  - [ ] A shot generated by Runway appears in production.json with ackend: "runway-v3", cost_estimate_usd: <actual>, output_sha256: <sha>.
- **Verify:** integration test against Runway's sandbox (or unit-test against a recorded fixture response).
- **Files:** src/plugins/generation/runway.py (new), 	ests/test_runway_plugin.py (new).
- **Size:** L.

**R3-T4 — Plugin health-check scheduler + cost/latency telemetry**
- **Description:** A lightweight background task (started by ProductionService or by a CLI subcommand production watch) runs health_check_all() every 60 seconds, logs disabled plugins, and aggregates CostEstimate data into a per-production summary. The summary is queryable via production report --cost.
- **Acceptance:**
  - [ ] production watch keeps running and emits a log line every 60s with disabled-plugin count and total spend in the current hour.
  - [ ] production report --cost <prod_id> returns per-agent totals and grand totals in JSON.
  - [ ] Disabling a plugin mid-run does not crash in-flight generations; they complete with the last-known backend.
- **Verify:** pytest tests/test_plugin_health.py -q, manual with production watch.
- **Files:** src/service/plugin_scheduler.py (new), src/cli/watch.py (new), src/cli/report.py (new).
- **Size:** M.

**R3-T5 — Real MP4 export pipeline**
- **Description:** Replace Mp4PlaceholderPlugin with a real ffmpeg pipeline. Takes a list of generated clips (URIs + durations + transitions), runs fmpeg -f concat with the transition metadata, writes output/exports/<prod_id>_<timestamp>.mp4. Honour platform-specific encoding requirements (YouTube 1080p h.264, Instagram Reels 1080×1920 vertical, TikTok 1080×1920).
- **Acceptance:**
  - [ ] production export <prod_id> --platform youtube produces a valid MP4 playable in VLC.
  - [ ] Vertical platforms produce 1080×1920 output.
  - [ ] The export run logs per-clip timing and total wall-clock.
  - [ ] fmpeg missing → clear error with install hint, not a stack trace.
- **Verify:** pytest tests/test_export_mp4.py -q (small fixture video); manual: export a real production, play in VLC.
- **Files:** src/plugins/export_format/mp4_real.py (new), src/cli/export.py (new), 	ests/test_export_mp4.py.
- **Size:** L.

**Checkpoint after R3:** the plugin story is real. External packages can extend generation, export, asset-type, or agent-role surfaces. Health monitoring and cost tracking are continuous. Review with maintainer before R4.

### Phase R4 — Multi-primitive transforms (F77–F79) + media vertical coverage

**Goal:** the kernel's five primitives cover all four media verticals the plan names: text, image, audio, video. Currently only text + a stub of video are covered.

**Vertical slice:** ingest an MP3 → run audio transforms (loudness normalise, transcribe) → produce a text artifact that feeds the research-writing vertical → render the resulting article as a PNG (image transform) → compose into a vertical MP4 → publish to Instagram Reels.

#### Tasks

**R4-T1 — Image transforms (resize, crop, normalise)**
- **Description:** Add image.resize, image.crop, image.normalise to the transform catalog. Backed by Pillow. Each transform returns a TransformResult with output_uri and output_sha256. Auto-register on import.
- **Acceptance:**
  - [ ] Three transforms listed in list_transforms() under the image prefix.
  - [ ] image.resize accepts {uri, width, height} and emits the resized file.
  - [ ] Idempotency: running image.resize twice on the same input produces the same output_sha256.
- **Verify:** pytest tests/test_image_transforms.py -q.
- **Files:** src/transforms/image/resize.py, src/transforms/image/crop.py, src/transforms/image/normalise.py, 	ests/test_image_transforms.py.
- **Size:** M.

**R4-T2 — Audio transforms (loudness-normalise, transcribe, segment)**
- **Description:** Add udio.loudness_normalise (EBU R128 via pyloudnorm), udio.transcribe (whisper.cpp or openai-whisper), udio.segment (silence detection → shot boundaries). Each must be idempotent and content-addressed.
- **Acceptance:**
  - [ ] Three transforms listed under the udio prefix.
  - [ ] udio.transcribe returns a TransformResult whose alue is a list of {start, end, text} segments.
  - [ ] udio.loudness_normalise measures input LUFS and writes a target-LUFS output.
- **Verify:** pytest tests/test_audio_transforms.py -q with a small WAV fixture.
- **Files:** src/transforms/audio/loudness.py, src/transforms/audio/transcribe.py, src/transforms/audio/segment.py, 	ests/test_audio_transforms.py.
- **Size:** L.

**R4-T3 — Video transforms (transcode, thumbnail, scene-detect)**
- **Description:** Add ideo.transcode (ffmpeg wrapper), ideo.thumbnail (extract mid-shot frame), ideo.scene_detect (PySceneDetect or content-based hash boundaries). The existing src/videos/render_transform.py becomes one of many; promote it to ideo.compose.linear and add ideo.compose.shots_from_scenes.
- **Acceptance:**
  - [ ] Three transforms listed under the ideo prefix; ideo.compose.linear and ideo.compose.shots_from_scenes under ideo.compose.
  - [ ] ideo.transcode accepts {input_uri, codec, resolution, bitrate} and emits a valid MP4.
  - [ ] ideo.scene_detect returns a list of {start, end, score} cuts.
- **Verify:** pytest tests/test_video_transforms.py -q with a small MP4 fixture.
- **Files:** src/transforms/video/transcode.py, src/transforms/video/thumbnail.py, src/transforms/video/scene_detect.py, src/transforms/video/compose/linear.py, src/transforms/video/compose/shots_from_scenes.py, 	ests/test_video_transforms.py.
- **Size:** L.

**R4-T4 — Cross-vertical composition example**
- **Description:** Author examples/cross_vertical_demo.py that runs the slice described in the Phase R4 vertical: MP3 → audio transforms → text artifact → research-writing vertical → PNG render → MP4 export → Instagram Reels publish manifest. Documented as the canonical "kernel-generalisation proof."
- **Acceptance:**
  - [ ] The script runs end-to-end with all-mock backends in < 30 seconds.
  - [ ] udit.jsonl records each transform and each gate.
  - [ ] docs/architecture/architecture.md §five-primitives section links to this example.
- **Verify:** python examples/cross_vertical_demo.py --no-confirm then inspect outputs.
- **Files:** examples/cross_vertical_demo.py, docs/architecture/architecture.md (update).
- **Size:** M.

**Checkpoint after R4:** the kernel demonstrates four-vertical coverage. The same primitives drive text, image, audio, and video pipelines. Review with maintainer before R5.

### Phase R5 — Frontend quality, CI, multi-user (F86, F90, F107, F121–F125, F133)

**Goal:** the system is shippable to multiple users. CI catches regressions. Frontend tests prevent accidental breakages. Auth and rate limiting are first-class.

**Vertical slice:** a new engineer clones the repo → CI runs on the PR → Vitest catches a regression → they merge → a real user (with auth) loads the app and runs a production → the rate limiter keeps them under the cap → they invite a collaborator → both see the same Production state without losing edits.

#### Tasks

**R5-T1 — GitHub Actions CI**
- **Description:** Create .github/workflows/ci.yml with three jobs: python (pytest -q --maxfail=1), web (
pm ci && npm run lint && npx tsc --noEmit && npm run test), docs (placeholder-check on ender_index_html). Cache pip and npm. Trigger on push and PR.
- **Acceptance:**
  - [ ] A PR with a failing pytest triggers a red CI badge.
  - [ ] A PR with a TypeScript error triggers a red CI badge.
  - [ ] Cache hits reduce subsequent runs to < 90 seconds.
- **Verify:** push a known-good branch, confirm green; push a known-bad change, confirm red.
- **Files:** .github/workflows/ci.yml.
- **Size:** S.

**R5-T2 — Frontend test framework + critical-path coverage**
- **Description:** Add Vitest + React Testing Library + jsdom. Cover the five highest-leverage components: ProposalCard, AuditEntryRow, CommandBar, StateMachineBadge, GateBadge. Plus a critical-path integration test for useProductionStore (load angles → finalize → poll → reset flow, the exact race condition fixed in SYSTEM_HEALTH.md).
- **Acceptance:**
  - [ ] 
pm test runs in < 30 seconds.
  - [ ] Coverage on store/, components/, hooks/ ≥ 80%.
  - [ ] The known race condition test would fail without the generation-counter fix.
- **Verify:** 
pm test -- --coverage.
- **Files:** web/vitest.config.ts, web/tests/*.test.tsx.
- **Size:** M.

**R5-T3 — Mypy strict + coverage threshold**
- **Description:** Add mypy --strict to pyproject.toml for the schema, validation, and service layers. Add pytest --cov-fail-under=85 to the test target. Fix any typing regressions uncovered.
- **Acceptance:**
  - [ ] mypy src/schema src/validation src/service exits 0.
  - [ ] pytest --cov reports ≥ 85% on those three packages.
  - [ ] CI runs both on every PR.
- **Verify:** local + CI.
- **Files:** pyproject.toml, possibly small typing fixes in src/schema/production_document.py and src/service/production_service.py.
- **Size:** M.

**R5-T4 — Authentication + rate limiting**
- **Description:** Add a minimal session-cookie auth layer (no third-party IDP, just signed cookies against SECRET_KEY). Endpoints that mutate a production require an authenticated session. Add slowapi rate limiting at 60 req/min per IP for /api/production/*. Add a production users add / emove CLI for multi-user setups.
- **Acceptance:**
  - [ ] production login and production logout exist; sessions survive across requests.
  - [ ] /api/production/<id>/apply_event rejects unauthenticated requests with 401.
  - [ ] 100 rapid-fire requests from one IP trigger 429s after the 60th.
  - [ ] Auth secret is loaded from .env; missing secret is a hard startup failure, not silent fallback.
- **Verify:** 	ests/test_auth.py, 	ests/test_rate_limit.py; manual: hammer the endpoint with hey or b.
- **Files:** src/public_demo/auth.py (new), src/public_demo/server.py (extend), src/cli/users.py (new), 	ests/test_auth.py, 	ests/test_rate_limit.py.
- **Size:** L.

**R5-T5 — Multi-user optimistic concurrency + WebSocket / SSE**
- **Description:** Replace the per-instance RLock with a per-production version counter. Each pply_event returns the new version. The HTTP server emits SSE events on udit.jsonl appends; the frontend subscribes via EventSource instead of polling. Conflict detection: a production save from a stale version is rejected with 409.
- **Acceptance:**
  - [ ] Two users editing the same production: the second save returns 409 with a clear error.
  - [ ] Console updates appear within 1 second of a server-side mutation (SSE).
  - [ ] Polling still works as a fallback for users behind SSE-blocking proxies.
- **Verify:** new 	ests/test_concurrent_save.py::test_optimistic_locking; manual: open two browser tabs, edit one, watch the other.
- **Files:** src/service/production_service.py, src/public_demo/server.py (SSE endpoint), web/src/hooks/useAuditPoll.ts (replace with useAuditStream.ts).
- **Size:** L.

**Checkpoint after R5:** CI green; auth + rate limit on every endpoint; multi-user conflict detection works; SSE delivers sub-second event latency. Review with maintainer before R6.

### Phase R6 — Customisation surfaces, moonshots (F129–F133, F147, F148, F152)

**Goal:** the system is no longer "the production engine." It is the platform.

**Vertical slice:** an enterprise user logs in → opens Studio settings → creates a brand kit with 8 style tokens → assigns 3 reviewers (Legal, Brand, Accessibility) → invites 5 collaborators → runs a production with all 3 reviewers gating → publishes with full audit trail.

#### Tasks

**R6-T1 — Studio Library UI**
- **Description:** Surface the existing style_library.py + sset_library_service.py in a new Studio view (/?view=studio). Users can create studios, share brand kits across productions, browse style tokens, and apply a kit as a starting point.
- **Acceptance:**
  - [ ] Studio create / rename / delete / share flows are wired.
  - [ ] A brand kit applied to a new production copies the tokens into Production.style_tokens and Production.brand_kit.
  - [ ] Cross-production token changes do not retroactively modify existing productions (immutable history).
- **Verify:** web/tests/studio.test.tsx, pytest tests/test_studio.py -q.
- **Files:** web/src/views/Studio/ (new), web/src/App.tsx (route), src/service/studio.py (new).
- **Size:** L.

**R6-T2 — Consistency Contract visual editor**
- **Description:** A panel inside Director's Canvas and Agent Console that lets the user author a ConsistencyContract for a character or environment: visual anchors (uploaded references), required attributes (chip picker), prohibited attributes, variance tolerance (slider). Persists via production.update_consistency_contract(subject_id, contract).
- **Acceptance:**
  - [ ] Adding a prohibited attribute and re-running ReviewerAgent against a shot containing that attribute blocks delivery.
  - [ ] Variance tolerance slider at 0.05 enables strict stop-fast; at 0.30 enables partial-match allowance.
  - [ ] Contract revisions are versioned (non-destructive).
- **Verify:** web/tests/contract-editor.test.tsx, pytest tests/test_consistency_contract.py -q.
- **Files:** web/src/components/ConsistencyContractEditor.tsx (new), src/service/production_service.py::update_consistency_contract, 	ests/test_consistency_contract.py.
- **Size:** L.

**R6-T3 — User research interviews (ACT-1)**
- **Description:** Run the protocol in docs/research/user-research-plan.md with at least one real user per persona (Sam / Jordan / Alex / Maya). Capture findings in docs/research/findings/.
- **Acceptance:**
  - [ ] Four interview transcripts under docs/research/findings/.
  - [ ] Findings synthesised into a 1-page doc identifying which of the 5 Laws or 3 Axioms survive contact with users.
  - [ ] At least one principle in docs/principles.md updated based on findings.
- **Verify:** artefacts present; maintainer reviews.
- **Files:** docs/research/findings/ (new), possibly docs/principles.md.
- **Size:** M (people-time).

**R6-T4 — Pipeline validation session (P0-4)**
- **Description:** Run the protocol in docs/research/pipeline-validation-plan.md with a practicing video producer. Capture whether the 26-stage ordering is right; revise docs/architecture/architecture.md §pipeline accordingly.
- **Acceptance:**
  - [ ] One session transcript under docs/research/pipeline-validation/.
  - [ ] Updated pipeline diagram reflecting any reorderings.
  - [ ] Updated src/demo_flow.py stage ordering if needed.
- **Verify:** artefacts present; maintainer reviews.
- **Files:** docs/research/pipeline-validation/ (new), possibly docs/architecture/architecture.md and src/demo_flow.py.
- **Size:** M.

**R6-T5 — Moonshot prototypes (select 1–2 from §24)**
- **Description:** Pick one or two moonshots from open-production-plan.md §24 and prototype them behind feature flags. Suggested first picks: (a) **Production Replay** — open any production's udit.jsonl and step through it as a deterministic replayable timeline; (b) **Studio Memory** — local, opt-in, cross-production style-token retrieval (within the same user; respects Law 8 no-leakage).
- **Acceptance:**
  - [ ] Selected moonshot(s) ship behind a --feature-flag moonshot_replay toggle.
  - [ ] A test exercises the toggle on and off.
  - [ ] docs/architecture/architecture.md §research-opportunities updated with the prototype outcomes.
- **Verify:** feature-flag toggle + tests + docs update.
- **Files:** TBD per moonshot.
- **Size:** L per moonshot.

**Checkpoint after R6:** the system is platform-grade. Customisation, multi-user, governance, and at least one moonshot prototype are live. The maintainer signs off the next planning cycle.

---

## Part 3 — Cross-cutting risks and mitigations

| Risk | Impact | Mitigation | Linked phase |
|---|---|---|---|
| Scope creep into "build a video editor" | High — distracts from production-engine thesis | Each R2 view task is bounded by the wireframe; reject scope additions | R2 |
| Real-backend integration cost (Runway / OpenAI) | Medium — slow if API access is delayed | Keep MockGenerationPlugin as the default; real adapters are opt-in via entry_points | R3 |
| Cross-process lock failure on Windows | Medium — silent data loss | _safe_replace already retries; add cross-process lock with best-effort fallback | R0 |
| Multi-user conflict storms | High — users lose work | Optimistic locking + 409 + UI affordance to merge | R5 |
| Frontend test debt | Medium — regressions slip | Vitest on critical-path components first, expand to 80% coverage | R5 |
| Auth bypass during demo | High — leak risk | Add auth before any public exposure; refuse to expose demo server without it | R5 |
| Plugin supply-chain risk | Medium — malicious plugin writes bad data | Plugin health checks + audit trail of plugin calls + sandboxed execution | R3 |
| LLM cost blow-up on long runs | Medium — surprise bills | CostEstimate aggregation + production report --cost + per-agent budget caps | R3 |
| User research findings contradict a Law | High — design foundation destabilises | Update the Law + write a public "Law N v2" note; don't silently edit | R6 |

---

## Part 4 — Dependency graph (text form)

`
                       ┌── R0-T1 cross-process lock
                       ├── R0-T2 healthz + logging
           ┌── R0 ─────┼── R0-T3 un-silent excepts
           │           ├── R0-T4 doctor fix
           │           └── R0-T5 audit replay
           │
           │           ┌── R1-T1 propose/approve/reject
           ├── R1 ─────┼── R1-T2 wire demo_flow
           │           ├── R1-T3 frontend proposal cards
           │           └── R1-T4 ordering/expiry
           │
           │           ┌── R2-T1 canvas primitive
           │           ├── R2-T2 properties rail
           │           ├── R2-T3 proposal popovers
           ├── R2 ─────┼── R2-T4 timeline shell
           │           ├── R2-T5 inspector + transport
           │           ├── R2-T6 node graph + DAG
           │           └── R2-T7 cross-view harness
           │
           │           ┌── R3-T1 entry-point discovery
           ├── R3 ─────┼── R3-T2 LLM Protocol
           │           ├── R3-T3 first real gen backend
           │           ├── R3-T4 scheduler + telemetry
           │           └── R3-T5 real MP4 export
           │
           │           ┌── R4-T1 image transforms
           ├── R4 ─────┼── R4-T2 audio transforms
           │           ├── R4-T3 video transforms
           │           └── R4-T4 cross-vertical example
           │
           │           ┌── R5-T1 GitHub Actions
           ├── R5 ─────┼── R5-T2 frontend tests
           │           ├── R5-T3 mypy strict + coverage
           │           ├── R5-T4 auth + rate limit
           │           └── R5-T5 SSE + optimistic locking
           │
           │           ┌── R6-T1 Studio Library UI
           ├── R6 ─────┼── R6-T2 Consistency Contract editor
           │           ├── R6-T3 user research
           │           ├── R6-T4 pipeline validation
           │           └── R6-T5 moonshots
           │
           ▼
     R0 → R1 → R2 → R3 → R4 → R5 → R6     (sequential backbone)
`

Parallelisable within a phase:
- **R0:** T1, T2, T3, T4 can run in parallel; T5 needs T1.
- **R1:** T1 must finish first; T2 + T3 can run in parallel once T1 lands; T4 independent.
- **R2:** three views can be built in parallel by separate engineers; T7 is the integration gate.
- **R3:** T1, T2 independent; T3 needs T1; T4 needs T3; T5 independent.
- **R5:** T1, T2, T3 can run in parallel; T4 needs T1; T5 needs T3.
- **R6:** T1, T2 can run in parallel; T3, T4, T5 independent.

---

## Part 5 — Task index (one-line summary, all 35 tasks)

| Task | Phase | Size | One-line |
|---|---|---|---|
| R0-T1 | Stability | M | Cross-process file lock helper |
| R0-T2 | Stability | S | /healthz + structured JSON logging |
| R0-T3 | Stability | S | Replace silent except in demo_flow.py |
| R0-T4 | Stability | XS | Fix doctor consistency_contract_gate yellow |
| R0-T5 | Stability | M | Audit replay from JSONL (round-trip test) |
| R1-T1 | Approval API | M | propose() / pprove() / eject() on service |
| R1-T2 | Approval API | M | Wire demo_flow through propose/approve |
| R1-T3 | Approval API | M | Frontend proposal cards + store slice |
| R1-T4 | Approval API | S | Approval expiry + double-approve conflict |
| R2-T1 | Frontend views | L | Director's Canvas primitive + Zustand slice |
| R2-T2 | Frontend views | M | Director's Canvas properties right-rail |
| R2-T3 | Frontend views | M | Director's Canvas AI proposal popovers |
| R2-T4 | Frontend views | L | Timeline Editor shell + 5-track layout |
| R2-T5 | Frontend views | M | Timeline Inspector + transport controls |
| R2-T6 | Frontend views | L | Node Graph + DAG layout + Node Inspector |
| R2-T7 | Frontend views | M | Cross-view consistency harness |
| R3-T1 | Plugins | M | Plugin entry-point discovery |
| R3-T2 | Plugins | M | LLMClient Protocol + OpenAI + Anthropic adapters |
| R3-T3 | Plugins | L | First real GenerationPlugin (Runway Gen-3) |
| R3-T4 | Plugins | M | Plugin health scheduler + cost/latency telemetry |
| R3-T5 | Plugins | L | Real MP4 export via ffmpeg |
| R4-T1 | Transforms | M | Image transforms (resize, crop, normalise) |
| R4-T2 | Transforms | L | Audio transforms (loudness, transcribe, segment) |
| R4-T3 | Transforms | L | Video transforms (transcode, thumbnail, scene-detect) |
| R4-T4 | Transforms | M | Cross-vertical composition example |
| R5-T1 | Quality | S | GitHub Actions CI |
| R5-T2 | Quality | M | Vitest + RTL on critical-path components |
| R5-T3 | Quality | M | mypy strict + coverage threshold |
| R5-T4 | Quality | L | Auth (signed cookies) + rate limiting |
| R5-T5 | Quality | L | SSE event stream + optimistic locking |
| R6-T1 | Platform | L | Studio Library UI |
| R6-T2 | Platform | L | Consistency Contract visual editor |
| R6-T3 | Platform | M | User research interviews (ACT-1) |
| R6-T4 | Platform | M | Pipeline validation session (P0-4) |
| R6-T5 | Platform | L | Moonshot prototype (1–2 selected) |

Total: **35 implementation tasks** across **7 phases** (R0–R6). Earliest checkpoint: end of R0 (~5 tasks in). Latest scope: R6 moonshot + research completion.

---

## Part 6 — Success criteria for the entire roadmap

- [ ] python -m pytest tests/ -q is green at every checkpoint.
- [ ] 
pm test (R5-T2 onwards) is green at every checkpoint from R5 forward.
- [ ] mypy --strict src/schema src/validation src/service (R5-T3 onwards) is green.
- [ ] production doctor --all is green on every fixture production at every checkpoint from R0 forward.
- [ ] All 5 wireframes have working implementations at the R2 checkpoint.
- [ ] At least one real GenerationPlugin adapter is registered and callable at the R3 checkpoint.
- [ ] A multi-user collaboration session (two browsers) does not lose writes at the R5 checkpoint.
- [ ] User research findings are integrated into docs/principles.md at the R6 checkpoint.
- [ ] The system survives a fresh clone + install + pytest + 
pm test + 
pm run dev on a maintainer's machine.

---

## Part 7 — Out of scope (per A2)

- IBM AI Builders Challenge submission-day logistics (platform form, certificate upload, video publishing).
- Bob session authoring (the 9 sessions in ob-sessions/ are the project's historical record; future Bob sessions are case-by-case).
- Production deployment infrastructure (CDN, edge cache, multi-region). When the system needs it, those tasks get their own spec.

---

*End of roadmap. Reference this file in PRs that close roadmap tasks; update Part 5 as tasks land.*
