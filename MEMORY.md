﻿﻿# Boris working memory â€” durable rules

Last updated: 2026-07-29 (post production-run CLI)

## Three-worker pipeline (set 2026-07-26)

For Open Production / IBM AI Builders Challenge submission:

- **Boris (architect)** â€” design, specs, audit, doc polish. Does NOT write product code.
- **Bob (in IBM Bob IDE on user's machine)** â€” productive code that ends up in the demo video and the audit trail. Bobcoin spend.
- **Codex (local or runtime dispatch)** â€” mechanical scaffolding, fixtures, indexes. Does NOT pollute Bob audit trail.

When to dispatch Codex via runtime: only for short, well-specified mechanical asks. When local: paste the prompt into the user's local Codex window. When in-this-thread: Boris does the work directly.

When in doubt: Boris does it in-thread. Runtime dispatch is unreliable on this machine (per open loop L4 in earlier sessions â€” samagama proxy 401/403).

## Boris behavior

- Default to action. No permission asks for reversible decisions.
- Stop only for: public commits, breaking PDT, blowing the deadline, anything irreversible.
- Never ask "should I continue" mid-stream. Propose + default + continue.
- Codex via runtime: fine on my call for reversible mechanical work. No need to ask.
- Bob work: NEVER dispatch via Codex. That's the user's human-Bob domain.

## Submission state (2026-07-29 â€” post production-run CLI)

- **597/597 tests passing** (42 test files + 3 dunder-prefixed utility scripts). The **`production run "<intent>"` keystone** is shipped: `python -m src.cli.run "<topic>" --no-confirm [--pick X] [--audience Y] [--tone Z] [--out DIR]` walks Stages 2â†’22, fires all 4 gates (evidence / consistency / consistency_contract / publication), emits one AuditEntry per stage + one per gate decision, and writes `productions/prod_<id>/{production.json, audit.jsonl}`. Locked by 7 tests in `tests/test_cli_run.py`. The runner is `src/service/pipeline_runner.py::PipelineRunner.run(intent, out_dir)`; the engine is `src/demo_flow.py::run_pipeline(intent_dict, out_dir, *, sink, llm_client)`.
- The dispatcher got its 5th subcommand (`run`). The 3 pre-existing `test_cli_compare.py` subprocess failures were the same `sys.path` bootstrap bug as the keystone; the same 3-line fix was applied to all 5 CLI entry points (`run.py`, `compare.py`, `timeline.py`, `trace.py`, `doctor.py`) so `python -m src.cli.<subcmd>` works without pytest's `pythonpath`.
- New audit: `docs/plans/audit-2026-07-29-run-done.md` (closes `production run` keystone + the runner + the dispatcher + the end-to-end happy-path test).
- 9 Bob sessions captured and indexed (sessions 01â€”09 in `bob-sessions/_index.md`).
- Video vertical built: `src/videos/` â€” proof kernel generalizes.
- Architecture doc, Project Page, README, demo story script, submission checklist, judge-pack one-pager all updated to reflect the keystone.
- PDT untouched.
- Next user action: record 3-min demo video (keystone is now `production run` from intent to production).

## Open loops

- L4: samagama proxy 401/403 — runtime dispatch flakiness. Workaround: do work in-thread.
- L6: GOALS.md — deferred.
- Topic: IBM scope still unconfirmed.
- **Resolved** (2026-07-29): the dispatcher's run_parser used add_argument(`topic`, `--topic`, ...) which argparse rejects (both names must start with -). Dropped the --topic alias in `src/cli/__main__.py` so `topic` is positional; matches `src/cli/run.py`. The dispatcher bug had been hiding because `tests/test_cli_main.py` did not run as part of the keystone flow; surfaced + fixed in this pass. All 7 dispatcher tests now green. Full suite: 600/600.
- **Still open:** `production doctor` reports YELLOW on `consistency_contract_gate` while timeline shows the actual gate name is `consistency_contract`. ~5 min one-line fix in `src/cli/doctor.py`.