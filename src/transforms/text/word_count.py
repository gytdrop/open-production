from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class WordCountTransform(Transform):
    name = "text.word_count"
    input_schema = str
    output_schema = int

    def apply(self, input_value: str) -> TransformResult:
        return TransformResult(
            value=len(input_value.split()),
            transform_name=self.name,
        )


register_transform(WordCountTransform())