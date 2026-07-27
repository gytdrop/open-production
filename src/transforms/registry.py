from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Transform

_registry: dict = {}


def register_transform(t: "Transform") -> None:
    _registry[t.name] = t


def get_transform(name: str) -> "Transform":
    return _registry[name]


def list_transforms() -> list[str]:
    return sorted(_registry.keys())


def clear_registry() -> None:
    _registry.clear()