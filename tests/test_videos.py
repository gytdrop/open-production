"""Tests for the video vertical — composition, transforms, gates, and end-to-end render."""
import json
from pathlib import Path

import pytest

from src.videos.primitives import Frame, Shot, VideoClip, VideoIntent
from src.videos.composition import ShotComposition
from src.videos.render_transform import FrameRenderTransform
from src.videos.quality_evaluation import VisualQualityGate, QualityVerdict
from src.videos.render import render_video
from src.transforms.registry import get_transform, list_transforms, register_transform


@pytest.fixture(autouse=True)
def ensure_videos_registered():
    """Re-register the videos transforms before each test.

    Other test modules (test_transforms.py) use an autouse fixture that
    clears the global registry after each test. Re-register here so the
    videos package's transforms can be discovered regardless of test order.
    """
    register_transform(FrameRenderTransform())
    register_transform(VisualQualityGate())
    yield


# 1. VideoIntent constructor takes title, duration, shot_count, style.
def test_video_intent_constructor():
    intent = VideoIntent(title="Demo", duration_seconds=10.0, shot_count=5, style="noir")
    assert intent.title == "Demo"
    assert intent.duration_seconds == 10.0
    assert intent.shot_count == 5
    assert intent.style == "noir"
    # Default style is "cinematic" when omitted.
    intent_default = VideoIntent(title="T", duration_seconds=1.0, shot_count=1)
    assert intent_default.style == "cinematic"


# 2. Frame.render_text() produces a non-empty string with the frame number.
def test_frame_render_text_contains_index():
    frame = Frame(index=42, description="A test frame", duration_seconds=0.5)
    text = frame.render_text()
    assert isinstance(text, str)
    assert text  # non-empty
    assert "42" in text  # contains the frame number


# 3. ShotComposition produces a list of shots with shot_count items.
def test_shot_composition_count():
    intent = VideoIntent(title="Demo", duration_seconds=10.0, shot_count=5)
    comp = ShotComposition(intent)
    shots = comp.apply().value
    assert len(shots) == 5
    assert all(isinstance(s, Shot) for s in shots)


# 4. ShotComposition splits duration evenly across shots.
def test_shot_composition_even_split():
    intent = VideoIntent(title="Demo", duration_seconds=10.0, shot_count=5)
    comp = ShotComposition(intent)
    shots = comp.apply().value
    durations = [s.duration_seconds for s in shots]
    assert all(abs(d - 2.0) < 1e-9 for d in durations), f"uneven: {durations}"
    assert abs(sum(durations) - 10.0) < 1e-9


# 5. ShotComposition — empty shot_count returns empty list.
def test_shot_composition_empty():
    intent = VideoIntent(title="Empty", duration_seconds=0.0, shot_count=0)
    comp = ShotComposition(intent)
    shots = comp.apply().value
    assert shots == []


# 6. FrameRenderTransform produces N frames for a shot with N frames.
def test_frame_render_transform_produces_n_frames():
    shot = Shot(shot_id="shot-01", intent="Opener", frames=5, duration_seconds=2.0)
    result = FrameRenderTransform().apply(shot)
    frames = result.value
    assert len(frames) == 5
    assert all(isinstance(f, Frame) for f in frames)
    assert frames[0].index == 0
    assert frames[-1].index == 4


# 7. FrameRenderTransform is auto-registered in the transform registry.
def test_frame_render_transform_registered():
    names = list_transforms()
    assert "video.render_frame" in names
    t = get_transform("video.render_frame")
    assert isinstance(t, FrameRenderTransform)


# 8. VisualQualityGate fail-closed at min_score=0.99 rejects all frames.
def test_visual_quality_gate_fails_closed_at_high_threshold():
    frames = [Frame(index=i, description=f"frame {i}") for i in range(3)]
    gate = VisualQualityGate(min_score=0.99)
    verdicts = gate.apply(frames).value
    assert len(verdicts) == 3
    assert all(isinstance(v, QualityVerdict) for v in verdicts)
    assert all(v.passed is False for v in verdicts)
    assert all(v.score < 0.99 for v in verdicts)


# 9. render_video end-to-end produces 5+ files in output dir and 4+ audit entries.
def test_render_video_end_to_end(tmp_path):
    audit_path = tmp_path / "audio.jsonl"
    out_dir = tmp_path / "frames"
    intent = VideoIntent(title="Test video", duration_seconds=10.0, shot_count=5)
    frames = render_video(intent, out_dir=str(out_dir), audit_path=str(audit_path))

    # Should produce frames: 10s / 5 shots = 2s each → 2 * 30 = 60 frames per shot × 5 = 300 frames.
    assert len(frames) > 0

    # Output dir should have frame files + verdicts.json → 5+ files.
    out_files = list(out_path(out_dir))
    assert len(out_files) >= 5, f"expected 5+ files, got {len(out_files)}"

    # Audit trail should have 4+ entries (composition + 5 render + 1 quality = 7).
    audit_entries = read_jsonl(audit_path)
    assert len(audit_entries) >= 4, f"expected 4+ audit entries, got {len(audit_entries)}"

    # Quality gate should pass by default (mock score 0.85 >= 0.5).
    statuses = [e["decision_status"] for e in audit_entries]
    assert "publish_ok" in statuses


# --- helpers ---


def out_path(out_dir: Path) -> list[Path]:
    return [p for p in out_dir.iterdir() if p.is_file()]


def read_jsonl(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    return [json.loads(line) for line in text.splitlines() if line.strip()]
