from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class SequenceTransform(Transform):
    name = "compose.sequence"
    input_schema = None
    output_schema = None

    def __init__(self, *transforms: Transform, name: str = None):
        super().__init__(name)
        # Allow either SequenceTransform([a, b]) or SequenceTransform(a, b).
        if len(transforms) == 1 and isinstance(transforms[0], list):
            self.transforms = list(transforms[0])
        else:
            self.transforms = list(transforms)

    def apply(self, input_value) -> TransformResult:
        current = input_value
        step_names: list[str] = []
        for t in self.transforms:
            result = t.apply(current)
            step_names.append(result.transform_name)
            current = result.value
        return TransformResult(
            value=current,
            transform_name=self.name,
            metadata={"steps": step_names},
        )


register_transform(SequenceTransform())