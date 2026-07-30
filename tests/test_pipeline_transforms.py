"""Tests verifying the transform catalog is wired into pipeline execution.

The _run_pipeline_transforms() helper in demo_flow.py bridges the transform
catalog and the main build_demo_report() pipeline.  These tests confirm:

1. _run_pipeline_transforms() runs all expected transforms and returns
   correctly shaped output.
2. build_demo_report() includes transform_results in its return value and
   the values are consistent with the inputs.
3. The deduped source-id list produced by the transform pass is the same
   set of ids that the Research stage receives.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src is on the path (mirrors tests/conftest.py)
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.demo_flow import _run_pipeline_transforms, FIXTURE_CLAIMS


# ---------------------------------------------------------------------------
# _run_pipeline_transforms unit tests
# ---------------------------------------------------------------------------

class TestRunPipelineTransforms:
    """Unit tests for _run_pipeline_transforms()."""

    TOPIC = "CRISPR gene therapy reduces disease burden"
    SOURCE_IDS = ["pubmed:001", "pubmed:002", "pubmed:002", "pubmed:003"]

    def _call(self, topic=None, claims=None, source_ids=None):
        return _run_pipeline_transforms(
            topic=topic or self.TOPIC,
            claims=claims or FIXTURE_CLAIMS,
            source_ids=source_ids or self.SOURCE_IDS,
        )

    def test_returns_dict_with_all_expected_keys(self):
        r = self._call()
        expected_keys = {
            "topic_summary",
            "topic_word_count",
            "deduped_source_ids",
            "tagged_claims",
            "pipeline_word_count",
            "pipeline_steps",
            "registered_transforms",
        }
        assert expected_keys.issubset(r.keys())

    def test_topic_summary_is_string(self):
        r = self._call()
        assert isinstance(r["topic_summary"], str)
        assert len(r["topic_summary"]) > 0

    def test_topic_summary_truncates_long_topic(self):
        long_topic = " ".join(["word"] * 200)
        r = self._call(topic=long_topic)
        words = r["topic_summary"].split()
        assert len(words) <= 50

    def test_topic_summary_preserves_short_topic(self):
        short = "short topic"
        r = self._call(topic=short)
        assert r["topic_summary"] == short

    def test_topic_word_count_is_int(self):
        r = self._call()
        assert isinstance(r["topic_word_count"], int)
        assert r["topic_word_count"] == len(self.TOPIC.split())

    def test_deduped_source_ids_removes_duplicates(self):
        result = self._call(source_ids=["a", "b", "a", "c"])
        assert result["deduped_source_ids"] == ["a", "b", "c"]

    def test_deduped_source_ids_sorted(self):
        result = self._call(source_ids=["c", "a", "b"])
        assert result["deduped_source_ids"] == ["a", "b", "c"]

    def test_deduped_source_ids_empty(self):
        result = _run_pipeline_transforms(topic=self.TOPIC, claims=[], source_ids=[])
        assert result["deduped_source_ids"] == []

    def test_tagged_claims_length_unchanged(self):
        r = self._call()
        assert len(r["tagged_claims"]) == len(FIXTURE_CLAIMS)

    def test_claims_with_sources_tagged_source_required(self):
        """Claims that already carry source_ids get source_required=True."""
        r = self._call()
        for claim, tagged in zip(FIXTURE_CLAIMS, r["tagged_claims"]):
            if claim.get("source_ids"):
                assert tagged.get("source_required") is True
            else:
                assert "source_required" not in tagged

    def test_tagged_claims_preserve_original_fields(self):
        r = self._call()
        for original, tagged in zip(FIXTURE_CLAIMS, r["tagged_claims"]):
            for key in original:
                assert tagged[key] == original[key]

    def test_pipeline_word_count_matches_summary_then_word_count(self):
        """SequenceTransform(summary, word_count) should produce word count of the summary."""
        from src.transforms.text.summary import SummaryTransform
        summary_t = SummaryTransform()
        topic_summary = summary_t.apply(self.TOPIC).value
        expected_count = len(topic_summary.split())
        r = self._call()
        assert r["pipeline_word_count"] == expected_count

    def test_pipeline_steps_lists_both_transform_names(self):
        r = self._call()
        assert "text.summary" in r["pipeline_steps"]
        assert "text.word_count" in r["pipeline_steps"]

    def test_registered_transforms_includes_catalog(self):
        r = self._call()
        reg = r["registered_transforms"]
        assert "text.upper" in reg
        assert "text.word_count" in reg
        assert "text.summary" in reg
        assert "filter.dedupe" in reg
        assert "filter.require_source" in reg
        assert "compose.sequence" in reg

    def test_registered_transforms_includes_visual_quality_gate(self):
        """VisualQualityGate lives in src/videos and registers as video.quality_gate."""
        # Import videos to trigger registration
        import src.videos  # noqa: F401
        r = self._call()
        assert "video.quality_gate" in r["registered_transforms"]


# ---------------------------------------------------------------------------
# Integration: build_demo_report includes transform_results
# ---------------------------------------------------------------------------

class TestBuildDemoReportTransformIntegration:
    """Verify build_demo_report() includes transform_results in its output."""

    @pytest.fixture(scope="class")
    @classmethod
    def report(cls, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("demo_transforms")
        from src.demo_flow import build_demo_report
        return build_demo_report(
            topic="CRISPR reduces disease burden",
            audit_dir=str(tmp),
        )

    def test_transform_results_key_present(self, report):
        assert "transform_results" in report

    def test_transform_topic_summary_in_report(self, report):
        tr = report["transform_results"]
        assert "topic_summary" in tr
        assert isinstance(tr["topic_summary"], str)

    def test_transform_deduped_sources_consistent_with_claims(self, report):
        """Deduped source ids from transforms should be a subset of all claim source ids."""
        from src.demo_flow import FIXTURE_CLAIMS
        all_ids = {
            sid
            for claim in FIXTURE_CLAIMS
            for sid in (claim.get("source_ids") or [])
            if str(sid).strip()
        }
        deduped = set(report["transform_results"]["deduped_source_ids"])
        assert deduped == all_ids

    def test_transform_word_count_positive(self, report):
        assert report["transform_results"]["topic_word_count"] > 0

    def test_pipeline_steps_two_entries(self, report):
        assert len(report["transform_results"]["pipeline_steps"]) == 2
