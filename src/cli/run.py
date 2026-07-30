"""``production run "<intent>"`` - drive the full 22-stage pipeline.

This is the keystone CLI command. After it ships, Open Production can be
driven end-to-end from the terminal:

    python -m src.cli.run "A 60-second explainer on CRISPR" --no-confirm
    python -m src.cli.run "CRISPR for sickle cell" --pick skeptic --tone warm
    python -m src.cli.timeline prod_<id>   # inspect the audit trail

Architecture mirrors the timeline / trace / doctor / compare siblings:
  * argparse-style CLI with ANSI-coloured output (auto-disabled when
    stdout is not a TTY or NO_COLOR is set).
  * Defaults: --audience educated_lay, --tone neutral, --platform youtube,
    --out productions/.
  * Interactive mode binds a TtyConfirmSink so the user picks the angle live.
  * --no-confirm binds an AutoConfirmSink (with --pick to override).
  * Exit code: 0 on success, 1 on a hard failure (e.g. missing topic).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Bootstrap ``sys.path`` so internal subpackages (agents / audit / validation /
# tools / etc.) are importable via their bare names (``from agents.base ...``).
# pytest already does this via ``pyproject.toml``'s ``pythonpath = ["src"]``,
# but a ``python -m src.cli.run`` invocation only sees the project root on
# ``sys.path``, so without this bootstrap the agents package is unreachable.
_THIS_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _THIS_DIR.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from src.agents.confirm_gate import AutoConfirmSink, TtyConfirmSink  # noqa: E402
from src.demo_flow import pick_default_angle_id  # noqa: E402
from src.schema.production_document import IntentDocument  # noqa: E402
from src.service.pipeline_runner import PipelineRunner  # noqa: E402


# ---------------------------------------------------------------------------
# ANSI renderer (mirrors timeline / trace / doctor / compare).
# ---------------------------------------------------------------------------
_USE_ANSI: bool = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
_BOLD = "\x1b[1m" if _USE_ANSI else ""
_GREEN = "\x1b[32m" if _USE_ANSI else ""
_YELLOW = "\x1b[33m" if _USE_ANSI else ""
_RED = "\x1b[31m" if _USE_ANSI else ""
_CYAN = "\x1b[36m" if _USE_ANSI else ""
_DIM = "\x1b[2m" if _USE_ANSI else ""
_RESET = "\x1b[0m" if _USE_ANSI else ""


def _ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _resolve_sink(no_confirm, pick, topic):
    """Pick the ConfirmSink the runner will use at the ConfirmGate.

    AutoConfirmSink is deterministic and is used for --no-confirm (CI /
    scripted / make-demo). When --pick is supplied, that angle wins even
    with --no-confirm; otherwise we fall back to the deterministic
    pick_default_angle_id(topic).
    """
    if no_confirm:
        chosen = pick or pick_default_angle_id(topic)
        return AutoConfirmSink(choice=chosen)
    return TtyConfirmSink()


def _render_summary(production, out_dir):
    """Render a single-colour summary line for the final Production."""
    audit_path = out_dir / production.id / "audit.jsonl"
    state_path = out_dir / production.id / "production.json"
    lines = [
        f"{_BOLD}{_GREEN}production run: ok{_RESET}",
        f"  id:        {production.id}",
        f"  state:     {production.state}",
        f"  audit:     {audit_path}",
        f"  document:  {state_path}",
        f"  entries:   {len(production.audit_trail)}",
    ]
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="production run",
        description=(
            "Drive the full 22-stage production pipeline from an intent. "
            "The runner walks CreativeReframing -> ConfirmGate -> 20 stages, "
            "committing every proposal through ProductionService.apply_event "
            "and emitting gate decisions for evidence / consistency / "
            "consistency-contract / publication. With --no-confirm the runner "
            "uses AutoConfirmSink so the script is non-interactive."
        ),
    )
    parser.add_argument(
        "topic",
        help="Topic or one-line brief to drive the production.",
    )
    parser.add_argument(
        "--audience",
        default="educated_lay",
        help="Target audience descriptor (default: educated_lay).",
    )
    parser.add_argument(
        "--tone",
        default="neutral",
        help="Desired tone (default: neutral).",
    )
    parser.add_argument(
        "--platform",
        default="youtube",
        help="Intended publication platform (default: youtube).",
    )
    parser.add_argument(
        "--out",
        default="productions/",
        help="Output directory under which productions/prod_<id>/ is created.",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip the interactive ConfirmGate; use AutoConfirmSink.",
    )
    parser.add_argument(
        "--pick",
        default=None,
        help="With --no-confirm, force this angle. Must be one of: "
             "skeptic | advocate | contrarian.",
    )
    return parser


def main(argv=None):
    """Parse argv, run the pipeline, render the summary, return the exit code."""
    parser = build_parser()
    _ensure_utf8_stdout()
    args = parser.parse_args(argv)

    if not args.topic.strip():
        print(f"{_RED}error:{_RESET} topic must be a non-empty string", file=sys.stderr)
        return 1

    if args.pick is not None and args.pick not in ("skeptic", "advocate", "contrarian"):
        print(
            f"{_RED}error:{_RESET} --pick must be one of skeptic | advocate | contrarian "
            f"(got {args.pick!r})",
            file=sys.stderr,
        )
        return 1

    intent = IntentDocument(
        topic=args.topic,
        audience=args.audience,
        tone=args.tone,
        platform=args.platform,
    )
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    sink = _resolve_sink(args.no_confirm, args.pick, args.topic)
    runner = PipelineRunner(sink=sink)

    try:
        production = runner.run(intent, out_dir)
    except Exception as exc:
        print(f"{_RED}error:{_RESET} pipeline failed: {exc}", file=sys.stderr)
        return 1

    print(_render_summary(production, out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
