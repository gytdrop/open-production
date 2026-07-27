from src.transforms.base import Transform, TransformResult
from src.transforms.registry import register_transform


class SummaryTransform(Transform):
    name = "text.summary"
    input_schema = str
    output_schema = str

    def __init__(self, name: str = None, max_words: int = 50):
        super().__init__(name)
        self.max_words = max_words

    def apply(self, input_value: str) -> TransformResult:
        words = input_value.split()[: self.max_words]
        return TransformResult(
            value=" ".join(words),
            transform_name=self.name,
        )


register_transform(SummaryTransform())