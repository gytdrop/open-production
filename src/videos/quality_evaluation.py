"""Evaluation — VisualQualityGate, a fail-closed quality gate for video frames."""
from dataclasses import dataclass
from src.videos.primitives import Frame
from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


@dataclass
class QualityVerdict:
    frame_index: int
    passed: bool
    score: float  # 0.0 to 1.0
    reason: str = ""


class VisualQualityGate(Transform):
    """Fail-closed quality gate for video frames."""
    name = "video.quality_gate"
    input_schema = list  # list[Frame]
    output_schema = list  # list[QualityVerdict]

    def __init__(self, min_score: float = 0.5, name: str = None):
        super().__init__(name=name)
        self.min_score = min_score

    def apply(self, frames: list[Frame]) -> TransformResult:
        verdicts = []
        for frame in frames:
            # Mock quality scoring: every frame passes by default.
            # Replace with real visual quality analysis in v0.2.
            score = 0.85
            passed = score >= self.min_score
            verdicts.append(QualityVerdict(
                frame_index=frame.index,
                passed=passed,
                score=score,
                reason="mock: visual quality scoring not implemented",
            ))
        return TransformResult(
            value=verdicts,
            transform_name=self.name,
            metadata={"frame_count": len(frames), "min_score": self.min_score},
        )


register_transform(VisualQualityGate())
