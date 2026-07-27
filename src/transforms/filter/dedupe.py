from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class DedupeTransform(Transform):
    name = "filter.dedupe"
    input_schema = list
    output_schema = list

    def apply(self, input_value: list) -> TransformResult:
        return TransformResult(
            value=sorted(set(input_value)),
            transform_name=self.name,
        )


register_transform(DedupeTransform())