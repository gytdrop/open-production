"""Composition — a DAG of shots. v0.1 is a linear sequence."""
from src.videos.primitives import Shot, VideoIntent
from src.transforms.base import TransformResult


class ShotComposition:
    """A DAG of shots. For v0.1, a linear sequence."""

    def __init__(self, intent: VideoIntent):
        self.intent = intent
        self.shots = self._plan_shots()

    def _plan_shots(self) -> list[Shot]:
        """Linear plan: split into `shot_count` shots, each ~equal duration."""
        if self.intent.shot_count <= 0:
            return []
        per_shot = self.intent.duration_seconds / self.intent.shot_count
        return [
            Shot(
                shot_id=f"shot-{i+1:02d}",
                intent=f"{self.intent.title} — segment {i+1}/{self.intent.shot_count}",
                frames=int(per_shot * 30),  # 30 fps
                duration_seconds=per_shot,
                metadata={"style": self.intent.style},
            )
            for i in range(self.intent.shot_count)
        ]

    def apply(self) -> TransformResult:
        return TransformResult(
            value=self.shots,
            transform_name="shot_composition",
            metadata={"shot_count": len(self.shots), "intent_title": self.intent.title},
        )
