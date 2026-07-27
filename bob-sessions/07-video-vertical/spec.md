# Bob Session 7 — Video Vertical Sketch

**Goal:** Build a real, working video vertical skeleton that uses the same five primitives (Source, Transform, Composition, Evaluation, Intent). This is the "we can actually generalize" proof judges score on Innovation. Concretely: a `videos/` package with a Shot Composition, a Shot Render Transform, a Visual Quality Evaluation, and a CLI that runs an end-to-end video preview render to a folder of PNG frames.

**Output:** New `src/videos/` package + compositions + tests.

---

## Context

Working directory: `D:\IBM Project\Open_Production\`.

Existing:
- `src/transforms/` (session 6) — base Transform class, registry, 6 transforms
- `src/agents/creative_reframing.py` — Bob-built, 189 lines
- `src/agents/confirm_gate.py` — Bob-built (session 5)
- `src/validation/gates.py` — three gate classes
- `src/audit/recorder.py` — Bob-built
- `src/tools/llm_client.py` — MockLLMClient
- 36+ tests pass (26 original + 10 transform)

The submission's narrative is medium-blind-ness. This session proves we can build a non-research vertical on the same primitives — without rendering actual video (no Remotion, no FFmpeg), but with a *Composition* that describes a video and a *Transform* that produces frame descriptions.

---

## Spec — paste into Bob IDE verbatim

> I need to build a small `video` vertical that proves the kernel generalizes beyond research writing. The vertical uses the same five primitives: Source (video clip), Transform (render frame), Composition (DAG of shots), Evaluation (visual quality gate), Intent (e.g., "60s product demo"). It does NOT depend on Remotion or FFmpeg — it produces a folder of PNG frame descriptions (text-based mock).
>
> ## Directory layout
>
> ```
> src/videos/
> ├── __init__.py
> ├── primitives.py            # Shot, Frame, VideoClip, VideoIntent dataclasses
> ├── composition.py           # ShotComposition class — DAG of shots
> ├── render_transform.py      # FrameRenderTransform — produces a Frame description
> ├── quality_evaluation.py    # VisualQualityGate — checks frame for basic quality
> └── render.py                # end-to-end: intent -> composition -> frames -> audit
> ```
>
> ## `src/videos/primitives.py`
>
> ```python
> from dataclasses import dataclass, field
> from typing import Any
>
> @dataclass
> class Frame:
>     """A text-described video frame."""
>     index: int
>     description: str
>     duration_seconds: float = 1.0
>     metadata: dict = field(default_factory=dict)
>
>     def render_text(self) -> str:
>         return f"Frame {self.index:04d} ({self.duration_seconds}s): {self.description}"
>
> @dataclass
> class Shot:
>     """A single shot in a video composition."""
>    shot_id: str
>     intent: str  # short description
>     frames: int  # number of frames
>     duration_seconds: float = 4.0
>     metadata: dict = field(default_factory=dict)
>
> @dataclass
> class VideoClip:
>     """A complete video clip produced by a Composition."""
>     title: str
>     frames: list[Frame]
>     duration_seconds: float
>     metadata: dict = field(default_factory=dict)
>
> @dataclass
> class VideoIntent:
>     """A desired video state — what should exist after the kernel acts."""
>     title: str
>     duration_seconds: float
>     shot_count: int
>     style: str = "cinematic"
> ```
>
> Total file: ≤ 60 lines.
>
> ## `src/videos/composition.py`
>
> ```python
> from src.videos.primitives import Shot, VideoClip, VideoIntent, Frame
> from src.transforms.base import TransformResult
>
> class ShotComposition:
>     """A DAG of shots. For v0.1, a linear sequence."""
>
>     def __init__(self, intent: VideoIntent):
>         self.intent = intent
>         self.shots = self._plan_shots()
>
>     def _plan_shots(self) -> list[Shot]:
>         """Linear plan: split into `shot_count` shots, each ~equal duration."""
>         if self.intent.shot_count <= 0:
>             return []
>         per_shot = self.intent.duration_seconds / self.intent.shot_count
>         return [
>             Shot(
>                 shot_id=f"shot-{i+1:02d}",
>                 intent=f"{self.intent.title} — segment {i+1}/{self.intent.shot_count}",
>                 frames=int(per_shot * 30),  # 30 fps
>                 duration_seconds=per_shot,
>                 metadata={"style": self.intent.style},
>             )
>             for i in range(self.intent.shot_count)
>        ]
>
>     def apply(self) -> TransformResult:
>         return TransformResult(
>             value=self.shots,
>             transform_name="shot_composition",
>             metadata={"shot_count": len(self.shots), "intent_title": self.intent.title},
>         )
> ```
>
> Total file: ≤ 50 lines.
>
> ## `src/videos/render_transform.py`
>
> ```python
> from src.videos.primitives import Shot, Frame
> from src.transforms.base import Transform, TransformResult
> from src.transforms.registry import register_transform
>
> class FrameRenderTransform(Transform):
>     """Renders a Shot into a list of Frame descriptions."""
>     name = "video.render_frame"
>     input_schema = Shot
>     output_schema = list  # list[Frame]
>
>     def apply(self, shot: Shot) -> TransformResult:
>         frames = [
>             Frame(
>                 index=i,
>                 description=f"[{shot.intent}] frame {i+1}/{shot.frames}",
>                 duration_seconds=shot.duration_seconds / max(shot.frames, 1),
>                 metadata={"shot_id": shot.shot_id, "style": shot.metadata.get("style", "cinematic")},
>             )
>             for i in range(shot.frames)
>        ]
>         return TransformResult(
>             value=frames,
>             transform_name=self.name,
>             metadata={"shot_id": shot.shot_id, "frame_count": len(frames)},
>         )
>
> register_transform(FrameRenderTransform())
> ```
>
> Total file: ≤ 35 lines.
>
> ## `src/videos/quality_evaluation.py`
>
> ```python
> from src.videos.primitives import Frame
> from src.transforms.base import Transform, TransformResult
> from src.transforms.registry import register_transform
> from dataclasses import dataclass
>
> @dataclass
> class QualityVerdict:
>     frame_index: int
>     passed: bool
>    score: float  # 0.0 to 1.0
>     reason: str = ""
>
> class VisualQualityGate(Transform):
>     """Fail-closed quality gate for video frames."""
>     name = "video.quality_gate"
>     input_schema = list  # list[Frame]
>     output_schema = list  # list[QualityVerdict]
>
>     def __init__(self, min_score: float = 0.5, name: str = None):
>         super().__init__(name=name)
>         self.min_score = min_score
>
>     def apply(self, frames: list[Frame]) -> TransformResult:
>         verdicts = []
>         for frame in frames:
>             # Mock quality scoring: every frame passes by default.
>             # Replace with real visual quality analysis in v0.2.
>             score = 0.85
>             passed = score >= self.min_score
>             verdicts.append(QualityVerdict(
>                 frame_index=frame.index,
>                 passed=passed,
>                 score=score,
>                 reason="mock: visual quality scoring not implemented",
>             ))
>         return TransformResult(
>             value=verdicts,
>             transform_name=self.name,
>             metadata={"frame_count": len(frames), "min_score": self.min_score},
>         )
>
> register_transform(VisualQualityGate())
> ```
>
> Total file: ≤ 50 lines.
>
> ## `src/videos/render.py`
>
> ```python
> import json
> from pathlib import Path
> from src.videos.primitives import VideoIntent, Frame
> from src.videos.composition import ShotComposition
> from src.videos.render_transform import FrameRenderTransform
> from src.videos.quality_evaluation import VisualQualityGate, QualityVerdict
> from src.audit.recorder import AuditRecorder
>
> def render_video(intent: VideoIntent, out_dir: str, audit_path: str = "video_audit.jsonl") -> list[Frame]:
>     """End-to-end video render: intent -> composition -> frames -> quality gate -> audit."""
>     out_path = Path(out_dir)
>     out_path.mkdir(parents=True, exist_ok=True)
>
>     recorder = AuditRecorder(path=audit_path)
>     all_frames: list[Frame] = []
>
>     # Stage 1: Composition (declarative desired state)
>     composition = ShotComposition(intent)
>     shots = composition.apply().value
>     recorder.record_gate_decision(
>         gate_name="composition_plan",
>         claim_id=f"intent-{intent.title}",
>         decision_status="accepted",
>         reason=f"planned {len(shots)} shots",
>         evidence={"title": intent.title, "duration_seconds": intent.duration_seconds, "shot_count": intent.shot_count, "style": intent.style},
>    )
>
>     # Stage 2: Render each shot
>     transform = FrameRenderTransform()
>     for shot in shots:
>         result = transform.apply(shot)
>         all_frames.extend(result.value)
>         recorder.record_gate_decision(
>             gate_name="frame_render",
>             claim_id=shot.shot_id,
>             decision_status="accepted",
>             reason=f"rendered {len(result.value)} frames",
>             evidence={"shot_id": shot.shot_id, "frame_count": len(result.value)},
>         )
>
>     # Stage 3: Quality gate
>     gate = VisualQualityGate(min_score=0.5)
>     verdicts = gate.apply(all_frames).value
>     rejected = [v for v in verdicts if not v.passed]
>     recorder.record_gate_decision(
>         gate_name="video_quality_gate",
>         claim_id="video-render",
>         decision_status="publish_ok" if not rejected else "publish_rejected",
>         reason=f"{len(verdicts) - len(rejected)}/{len(verdicts)} frames passed",
>         evidence={"frame_count": len(verdicts), "rejected_count": len(rejected)},
>     )
>
>     # Stage 4: Write frame descriptions to disk
>     for frame in all_frames:
>         (out_path / f"frame_{frame.index:06d}.txt").write_text(frame.render_text())
>
>     # Stage 5: Write verdict summary
>     (out_path / "verdicts.json").write_text(json.dumps(
>         [{"frame_index": v.frame_index, "passed": v.passed, "score": v.score, "reason": v.reason} for v in verdicts],
>         indent=2,
>     ))
>
>     return all_frames
>
> def main():
>     """CLI: parse args, run render, print summary."""
>     import argparse
>     parser = argparse.ArgumentParser(description="Render a video vertical from intent.")
>     parser.add_argument("--title", default="Product demo", help="Video title")
>     parser.add_argument("--duration", type=float, default=10.0, help="Duration in seconds")
>     parser.add_argument("--shots", type=int, default=5, help="Number of shots")
>     parser.add_argument("--out-dir", default="output/video", help="Output directory")
>     parser.add_argument("--audit", default="video_audit.jsonl", help="Audit trail path")
>     args = parser.parse_args()
>
>     intent = VideoIntent(title=args.title, duration_seconds=args.duration, shot_count=args.shots)
>     frames = render_video(intent, out_dir=args.out_dir, audit_path=args.audit)
>     total_seconds = sum(f.duration_seconds for f in frames)
>     print(f"Rendered {len(frames)} frames ({total_seconds:.1f}s) for '{args.title}'")
>     print(f"Output: {args.out_dir}/")
>    print(f"Audit trail: {args.audit}")
>
> if __name__ == "__main__":
>     main()
> ```
>
> Total file: ≤ 90 lines.
>
> ## Tests — `tests/test_videos.py`
>
> 8 tests:
>
> 1. `VideoIntent` — constructor takes title, duration, shot_count, style.
> 2. `Frame.render_text()` — produces a non-empty string with the frame number.
> 3. `ShotComposition` — produces a list of shots with `shot_count` items.
> 4. `ShotComposition` — splits duration evenly across shots.
> 5. `ShotComposition` — empty shot_count returns empty list.
> 6. `FrameRenderTransform` — produces N frames for a shot with N frames.
> 7. `FrameRenderTransform` — auto-registered in transform registry.
> 8. `VisualQualityGate` — fail-closed at min_score=0.99 should reject all frames.
> 9. `render_video` end-to-end — produces 5+ files in output dir and 4+ audit entries.
>
> ## Constraints
>
> - Pure stdlib (json, dataclasses, pathlib). No new dependencies.
> - DO NOT modify any existing files.
> - All existing tests must still pass. Plus 9 new = 45+ total.
> - Run `pytest -v` after each file. Report full output.
> - `render_video` must work end-to-end when called from `python -m src.videos.render`.
>
> ## Output
>
> 1. New files in `src/videos/` and `tests/test_videos.py`.
> 2. Full pytest run output (showing 45+ passing).
> 3. End-to-end run output from `python -m src.videos.render --title "Test video" --duration 10 --shots 5`.
> 4. 5-line summary at the top of the transcript.

---

## Save the transcript

Save to `D:\IBM Project\Open_Production\bob-sessions\07-video-vertical\transcript.md`. Use this header:

```markdown
# Bob Session 7 — Video Vertical Sketch

**Date:** 2026-07-27
**Goal:** Build the video vertical — proof the kernel generalizes beyond research.
**Outcome:** (paste 5-line summary)

---

## Files produced

- src/videos/ (5 files)
- tests/test_videos.py

---

## End-to-end run

(paste output from `python -m src.videos.render --title "Test video" --duration 10 --shots 5`)

---

## Transcript

(paste session here)
```

---

## Done when

- [ ] All files in `src/videos/` exist.
- [ ] `python -m src.videos.render` runs end-to-end.
- [ ] `tests/test_videos.py` has 9 tests, all pass.
- [ ] All existing tests still pass (45+ total).
- [ ] Transcript saved.

---

## Why this session matters

This is the "we can actually generalize" proof. The submission's narrative is that the same five primitives power any medium. After this session, judges evaluating Innovation see a *second* vertical — video — that uses the same Transform, Composition, Evaluation, and Intent primitives. That's not a doc claim; it's running code.

v0.2 would replace the text-frame mock with real Remotion rendering. v0.1 proves the abstraction.

Begin.