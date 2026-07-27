"""Tests for the Transform catalog. Boris wrote these to complete session 6."""
from __future__ import annotations

import pytest

from src.transforms.base import Transform, TransformResult
from src.transforms.registry import (
    register_transform,
    get_transform,
    list_transforms,
    clear_registry,
)
from src.transforms.text.upper import UpperTransform
from src.transforms.text.word_count import WordCountTransform
from src.transforms.text.summary import SummaryTransform
from src.transforms.filter.require_source import RequireSourceTransform
from src.transforms.filter.dedupe import DedupeTransform
from src.transforms.compose.sequence import SequenceTransform


@pytest.fixture(autouse=True)
def reset_registry():
    """Clear the registry, then re-register the canonical transforms by class.

    We re-register using the *imported* class objects directly rather than
    reloading the registrar modules — reloading would create fresh class
    objects and break ``isinstance`` assertions that compare against the
    classes imported at the top of this file.
    """
    clear_registry()
    register_transform(UpperTransform())
    register_transform(WordCountTransform())
    register_transform(SummaryTransform())
    register_transform(RequireSourceTransform())
    register_transform(DedupeTransform())
    register_transform(SequenceTransform())
    yield
    clear_registry()


def test_text_upper_basic():
    t = get_transform("text.upper")
    result = t.apply("hello")
    assert result.value == "HELLO"
    assert result.transform_name == "text.upper"


def test_text_upper_idempotent():
    t = get_transform("text.upper")
    assert t.apply("hello").value == "HELLO"
    assert t.apply("hello").value == "HELLO"


def test_text_word_count():
    t = get_transform("text.word_count")
    result = t.apply("hello world foo")
    assert result.value == 3


def test_text_summary_truncates():
    t = SummaryTransform(max_words=2)
    result = t.apply("a b c d e")
    assert result.value == "a b"


def test_filter_require_source():
    t = get_transform("filter.require_source")
    result = t.apply({"text": "x"})
    assert result.value["text"] == "x"
    assert result.value["source_required"] is True


def test_filter_dedupe():
    t = get_transform("filter.dedupe")
    result = t.apply([1, 2, 2, 3, 1])
    assert result.value == [1, 2, 3]


def test_compose_sequence_runs_in_order():
    upper = get_transform("text.upper")
    counter = get_transform("text.word_count")
    seq = SequenceTransform([upper, counter])
    result = seq.apply("hello world")
    # upper -> "HELLO WORLD", then word_count -> 2
    assert result.value == 2


def test_registry_lists_transforms():
    names = list_transforms()
    assert len(names) >= 6
    assert "text.upper" in names
    assert "text.word_count" in names
    assert "filter.dedupe" in names


def test_registry_get_returns_instance():
    t = get_transform("text.upper")
    assert isinstance(t, UpperTransform)


def test_transform_compose_returns_sequence():
    seq = UpperTransform().compose(WordCountTransform())
    assert isinstance(seq, SequenceTransform)


def test_transform_result_metadata():
    t = SummaryTransform(max_words=3)
    result = t.apply("alpha beta gamma delta epsilon")
    assert result.metadata == {}
    assert result.transform_name == "text.summary"