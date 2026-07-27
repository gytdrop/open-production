"""Primitives — Frame, Shot, VideoClip, VideoIntent dataclasses."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Frame:
    """A text-described video frame."""
    index: int
    description: str
    duration_seconds: float = 1.0
    metadata: dict = field(default_factory=dict)

    def render_text(self) -> str:
        return f"Frame {self.index:04d} ({self.duration_seconds}s): {self.description}"


@dataclass
class Shot:
    """A single shot in a video composition."""
    shot_id: str
    intent: str  # short description
    frames: int  # number of frames
    duration_seconds: float = 4.0
    metadata: dict = field(default_factory=dict)


@dataclass
class VideoClip:
    """A complete video clip produced by a Composition."""
    title: str
    frames: list[Frame]
    duration_seconds: float
    metadata: dict = field(default_factory=dict)


@dataclass
class VideoIntent:
    """A desired video state — what should exist after the kernel acts."""
    title: str
    duration_seconds: float
    shot_count: int
    style: str = "cinematic"