"""Video vertical — proof the kernel generalizes beyond research writing.

Uses the same five primitives (Source, Transform, Composition, Evaluation, Intent)
to render a video preview as a folder of text-described PNG frame descriptions.
"""
from src.videos.primitives import Frame, Shot, VideoClip, VideoIntent
from src.videos.composition import ShotComposition
from src.videos.render_transform import FrameRenderTransform
from src.videos.quality_evaluation import VisualQualityGate, QualityVerdict
from src.videos.render import render_video

__all__ = [
    "Frame",
    "Shot",
    "VideoClip",
    "VideoIntent",
    "ShotComposition",
    "FrameRenderTransform",
    "VisualQualityGate",
    "QualityVerdict",
    "render_video",
]
