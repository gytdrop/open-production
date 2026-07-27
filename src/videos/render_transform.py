"""Transform — renders a Shot into a list of Frame descriptions."""
from src.videos.primitives import Shot, Frame
from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class FrameRenderTransform(Transform):
    """Renders a Shot into a list of Frame descriptions."""
    name = "video.render_frame"
    input_schema = Shot
    output_schema = list  # list[Frame]

    def apply(self, shot: Shot) -> TransformResult:
        frames = [
            Frame(
                index=i,
                description=f"[{shot.intent}] frame {i+1}/{shot.frames}",
                duration_seconds=shot.duration_seconds / max(shot.frames, 1),
                metadata={"shot_id": shot.shot_id, "style": shot.metadata.get("style", "cinematic")},
            )
            for i in range(shot.frames)
        ]
        return TransformResult(
            value=frames,
            transform_name=self.name,
            metadata={"shot_id": shot.shot_id, "frame_count": len(frames)},
        )


register_transform(FrameRenderTransform())
