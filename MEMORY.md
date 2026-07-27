# Boris working memory — durable rules

Last updated: 2026-07-27 (updated by Bob — session sync)

## Three-worker pipeline (set 2026-07-26)

For Open Production / IBM AI Builders Challenge submission:

- **Boris (architect)** — design, specs, audit, doc polish. Does NOT write product code.
- **Bob (in IBM Bob IDE on user's machine)** — productive code that ends up in the demo video and the audit trail. Bobcoin spend.
- **Codex (local or runtime dispatch)** — mechanical scaffolding, fixtures, indexes. Does NOT pollute Bob audit trail.

When to dispatch Codex via runtime: only for short, well-specified mechanical asks. When local: paste the prompt into the user's local Codex window. When in-this-thread: Boris does the work directly.

When in doubt: Boris does it in-thread. Runtime dispatch is unreliable on this machine (per open loop L4 in earlier sessions — samagama proxy 401/403).

## Boris behavior

- Default to action. No permission asks for reversible decisions.
- Stop only for: public commits, breaking PDT, blowing the deadline, anything irreversible.
- Never ask "should I continue" mid-stream. Propose + default + continue.
- Codex via runtime: fine on my call for reversible mechanical work. No need to ask.
- Bob work: NEVER dispatch via Codex. That's the user's human-Bob domain.

## Submission state (2026-07-27)

- 51/51 tests passing (7 test files).
- 7 Bob sessions captured and indexed.
- Demo runs end-to-end with audit trail (audit_trail.jsonl).
- Video vertical built: `src/videos/` — proof kernel generalizes. `python -m src.videos.render` runs.
- Architecture doc, Project Page, README, demo story script, submission checklist, judge-pack one-pager all updated to reflect 7 sessions / 51 tests.
- PDT untouched.
- Next user action: record 3-min demo video.

## Open loops

- L4: samagama proxy 401/403 — runtime dispatch flakiness. Workaround: do work in-thread.
- L6: GOALS.md — deferred.
- Topic: IBM scope still unconfirmed.
