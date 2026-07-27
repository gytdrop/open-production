from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransformResult:
    value: Any
    transform_name: str
    metadata: dict = field(default_factory=dict)


class Transform:
    """Base class for a named, typed, idempotent transform."""

    name: str = "unnamed"
    input_schema: type | None = None
    output_schema: type | None = None

    def __init__(self, name: str = None):
        if name:
            self.name = name

    def apply(self, input_value: Any) -> TransformResult:
        raise NotImplementedError

    def __call__(self, input_value: Any) -> TransformResult:
        return self.apply(input_value)

    def compose(self, other: "Transform") -> "Transform":
        from src.transforms.compose.sequence import SequenceTransform
        return SequenceTransform(self, other)