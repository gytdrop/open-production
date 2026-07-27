"""End-to-end render: intent -> composition -> frames -> quality gate -> audit."""
import json
from pathlib import Path
from src.videos.primitives import VideoIntent, Frame
from src.videos.composition import ShotComposition
from src.videos.render_transform import FrameRenderTransform
from src.videos.quality_evaluation import VisualQualityGate
from src.audit.recorder import AuditRecorder


def render_video(intent: VideoIntent, out_dir: str, audit_path: str = "video_audit.jsonl") -> list[Frame]:
    """End-to-end video render: intent -> composition -> frames -> quality gate -> audit."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    recorder = AuditRecorder(path=audit_path)
    all_frames: list[Frame] = []

    # Stage 1: Composition (declarative desired state)
    composition = ShotComposition(intent)
    shots = composition.apply().value
    recorder.record_gate_decision(
        gate_name="composition_plan",
        claim_id=f"intent-{intent.title}",
        decision_status="accepted",
        reason=f"planned {len(shots)} shots",
        evidence={
            "title": intent.title,
            "duration_seconds": intent.duration_seconds,
            "shot_count": intent.shot_count,
            "style": intent.style,
        },
    )

    # Stage 2: Render each shot
    transform = FrameRenderTransform()
    for shot in shots:
        result = transform.apply(shot)
        # Re-index frames globally so each frame has a unique index across
        # the whole video. Without this, every shot starts at index 0 and
        # frame filenames collide on disk.
        offset = len(all_frames)
        shot_frames = result.value
        for frame in shot_frames:
            frame.index = offset + frame.index
        all_frames.extend(shot_frames)
        recorder.record_gate_decision(
            gate_name="frame_render",
            claim_id=shot.shot_id,
            decision_status="accepted",
            reason=f"rendered {len(shot_frames)} frames",
            evidence={"shot_id": shot.shot_id, "frame_count": len(shot_frames)},
        )

    # Stage 3: Quality gate
    gate = VisualQualityGate(min_score=0.5)
    verdicts = gate.apply(all_frames).value
    rejected = [v for v in verdicts if not v.passed]
    recorder.record_gate_decision(
        gate_name="video_quality_gate",
        claim_id="video-render",
        decision_status="publish_ok" if not rejected else "publish_rejected",
        reason=f"{len(verdicts) - len(rejected)}/{len(verdicts)} frames passed",
        evidence={"frame_count": len(verdicts), "rejected_count": len(rejected)},
    )

    # Stage 4: Write frame descriptions to disk
    for frame in all_frames:
        (out_path / f"frame_{frame.index:06d}.txt").write_text(frame.render_text(), encoding="utf-8")

    # Stage 5: Write verdict summary
    (out_path / "verdicts.json").write_text(json.dumps(
        [{"frame_index": v.frame_index, "passed": v.passed, "score": v.score, "reason": v.reason} for v in verdicts],
        indent=2,
    ), encoding="utf-8")

    return all_frames


def main():
    """CLI: parse args, run render, print summary."""
    import argparse
    parser = argparse.ArgumentParser(description="Render a video vertical from intent.")
    parser.add_argument("--title", default="Product demo", help="Video title")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration in seconds")
    parser.add_argument("--shots", type=int, default=5, help="Number of shots")
    parser.add_argument("--out-dir", default="output/video", help="Output directory")
    parser.add_argument("--audit", default="video_audit.jsonl", help="Audit trail path")
    args = parser.parse_args()

    intent = VideoIntent(title=args.title, duration_seconds=args.duration, shot_count=args.shots)
    frames = render_video(intent, out_dir=args.out_dir, audit_path=args.audit)
    total_seconds = sum(f.duration_seconds for f in frames)
    print(f"Rendered {len(frames)} frames ({total_seconds:.1f}s) for '{args.title}'")
    print(f"Output: {args.out_dir}/")
    print(f"Audit trail: {args.audit}")


if __name__ == "__main__":
    main()
