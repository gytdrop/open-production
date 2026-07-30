"""Schema validation for ``production run``.

Reuses the doctor's structural validator (it already understands how to deal
with the null vs object mismatch in this project's optional fields). Importing
the private helpers is acceptable here because ``production run`` and
``production doctor`` share the same "what counts as a healthy production"
contract; if the doctor's structural rules change, the run test will move
with them.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from src.cli.doctor import _filter_structural_errors, _strip_optional_nulls


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs" / "schema" / "production-document.schema.json"
)


def validate_production_structurally(document: dict, schema: dict) -> None:
    """Validate ``document`` against ``schema`` using the doctor's structural rules.

    Raises ``jsonschema.ValidationError`` on any structural mismatch.
    """
    validator = jsonschema.Draft202012Validator(schema)
    cleaned = _strip_optional_nulls(document, schema, root=schema)
    errors = sorted(validator.iter_errors(cleaned), key=lambda e: list(e.relative_path))
    structural = _filter_structural_errors(errors)
    if structural:
        raise structural[0]
