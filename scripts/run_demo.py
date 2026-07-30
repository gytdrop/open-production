"""End-to-end Open Production demo.

Runs CreativeReframing → **ConfirmGate** → three fail-closed gates against
a fixture claim set, records every gate decision to audit_trail.jsonl, and
prints a summary.

Usage:
    python scripts/run_demo.py --topic "CRISPR for sickle cell disease"
    python scripts/run_demo.py --topic "..." --no-confirm   # CI / scripted

The confirm gate (between Stage 2 and Stage 3) is the AI-as-creative-partner
moment: the system proposes three angles, the user picks one, and only then
do the gates fire against that framing. ``--no-confirm`` is the escape hatch
for non-interactive contexts (CI, ``make demo``).
"""
from __future__ import annotations

import argparse
import os
import sys

# Allow imports from root and src/ without installing the package.
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src_dir = os.path.join(_root_dir, "src")
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from agents.confirm_gate import AutoConfirmSink, ConfirmRequest, ConfirmSink, TtyConfirmSink
from agents.creative_reframing import ANGLE_IDS
from demo_flow import build_demo_report, generate_angles, pick_default_angle_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Open Production end-to-end demo.")
    parser.add_argument("--topic", required=True, help="Topic to reframe")
    parser.add_argument("--audience", default="educated_lay", help="Target audience")
    parser.add_argument("--tone", default="neutral", help="Desired tone")
    parser.add_argument("--out", default="audit_trail.jsonl", help="Audit trail output path")
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip the interactive confirm gate (use AutoConfirmSink). "
             "This is what `make demo` and CI use.",
    )
    parser.add_argument(
        "--pick",
        default=None,
        help="With --no-confirm, force this angle instead of the deterministic default.",
    )
    args = parser.parse_args()

    # ---- 1. Creative reframing ----
    angles = generate_angles(args.topic, args.audience, args.tone)
    print(f"\nCreative angles for: {args.topic!r}\n")
    for i, angle in enumerate(angles, 1):
        print(f"  {i}. [{angle['id']}] {angle['name']}")
        print(f"     {angle['summary']}")

    # ---- 2. Confirm gate (the AI-as-creative-partner moment) ----
    default_angle_id = args.pick or pick_default_angle_id(args.topic)
    sink: ConfirmSink = (
        AutoConfirmSink(choice=default_angle_id)
        if args.no_confirm
        else TtyConfirmSink()
    )
    request = ConfirmRequest(
        summary="Which angle should guide the write?",
        options=list(ANGLE_IDS),
        default=default_angle_id,
    )
    response = sink.ask(request)

    if response.declined:
        print("\nUser cancelled. Exiting.")
        return 0

    chosen_angle = next(
        (a for a in angles if a["id"] == response.choice),
        None,
    )
    if chosen_angle is None:
        # Sink returned an unknown id (shouldn't happen, but be safe).
        chosen_angle = next(a for a in angles if a["id"] == default_angle_id)

    print(f"\nUser picked: [{chosen_angle['id']}] {chosen_angle['name']}")
    print(f"  {chosen_angle['summary']}")

    report = build_demo_report(
        topic=args.topic,
        audience=args.audience,
        tone=args.tone,
        chosen_angle_id=response.choice,
        audit_path=args.out,
    )

    print(f"\n{report['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
