from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class UpperTransform(Transform):
    name = "text.upper"
    input_schema = str
    output_schema = str

    def apply(self, input_value: str) -> TransformResult:
        return TransformResult(
            value=input_value.upper(),
            transform_name=self.name,
        )


register_transform(UpperTransform())