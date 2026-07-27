from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class RequireSourceTransform(Transform):
    name = "filter.require_source"
    input_schema = dict
    output_schema = dict

    def apply(self, input_value: dict) -> TransformResult:
        return TransformResult(
            value={**input_value, "source_required": True},
            transform_name=self.name,
        )


register_transform(RequireSourceTransform())