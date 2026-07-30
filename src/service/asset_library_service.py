"""AssetLibraryService — content-addressed binary storage for production assets.

§13 of the Open Production architecture spec.

Design
------
Assets are stored under a root directory using a two-level SHA-256 prefix layout
(the same scheme used by git object storage):

    <root>/<sha256[:2]>/<sha256[2:]>/manifest.json
    <root>/<sha256[:2]>/<sha256[2:]>/<original_filename>

A JSON manifest alongside each object captures provenance:

    {
        "sha256":      "<hex digest>",
        "size":        <bytes>,
        "kind":        "<ReferenceKind>",
        "label":       "<human label>",
        "filename":    "<original filename>",
        "ingested_at": "<ISO-8601 UTC>",
        "ingested_by": "<actor string>"
    }

The service is pure-stdlib (hashlib, shutil, pathlib, json).
It never raises on lookup — missing assets return None from retrieve().

Public API
----------
    ingest(data, filename, kind, label, ingested_by) -> IngestResult
        Hash data bytes, store under content-address, return IngestResult.

    retrieve(sha256) -> RetrieveResult | None
        Return raw bytes + manifest, or None if not found.

    exists(sha256) -> bool
        Fast existence check (stat only).

    list_assets() -> list[dict]
        Enumerate every manifest in the store.

    delete(sha256) -> bool
        Remove a stored asset. Returns True if deleted, False if not found.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class IngestResult:
    """Returned by AssetLibraryService.ingest()."""
    sha256: str
    size: int
    uri: str             # content-address URI: "asset://<sha256>"
    already_existed: bool


@dataclass(frozen=True)
class RetrieveResult:
    """Returned by AssetLibraryService.retrieve()."""
    sha256: str
    data: bytes
    filename: str
    kind: str
    label: str
    size: int
    ingested_at: str
    ingested_by: str


class AssetLibraryService:
    """Content-addressed binary storage for production assets.

    Parameters
    ----------
    root:
        Path to the storage root directory. Created on first use.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _object_dir(self, sha256: str) -> Path:
        """Two-level prefix directory: <root>/<sha256[:2]>/<sha256[2:]>/"""
        return self._root / sha256[:2] / sha256[2:]

    def _manifest_path(self, sha256: str) -> Path:
        return self._object_dir(sha256) / "manifest.json"

    def _data_path(self, sha256: str, filename: str) -> Path:
        return self._object_dir(sha256) / filename

    def _content_uri(self, sha256: str) -> str:
        return f"asset://{sha256}"

    def _compute_sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _write_manifest(
        self,
        sha256: str,
        size: int,
        kind: str,
        label: str,
        filename: str,
        ingested_by: str,
        ingested_at: str,
    ) -> None:
        manifest = {
            "sha256": sha256,
            "size": size,
            "kind": kind,
            "label": label,
            "filename": filename,
            "ingested_at": ingested_at,
            "ingested_by": ingested_by,
        }
        self._manifest_path(sha256).write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    def _read_manifest(self, sha256: str) -> Optional[dict]:
        mp = self._manifest_path(sha256)
        if not mp.exists():
            return None
        try:
            return json.loads(mp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        data: bytes,
        filename: str,
        kind: str,
        label: str,
        ingested_by: str = "system",
    ) -> IngestResult:
        """Hash *data* and store it under its SHA-256 content address.

        If an object with the same digest already exists the write is skipped
        (content-addressed deduplication). Returns an IngestResult either way.
        """
        sha256 = self._compute_sha256(data)
        obj_dir = self._object_dir(sha256)
        already_existed = self._manifest_path(sha256).exists()

        if not already_existed:
            obj_dir.mkdir(parents=True, exist_ok=True)
            ingested_at = _utc_now()
            self._data_path(sha256, filename).write_bytes(data)
            self._write_manifest(
                sha256=sha256,
                size=len(data),
                kind=kind,
                label=label,
                filename=filename,
                ingested_by=ingested_by,
                ingested_at=ingested_at,
            )

        return IngestResult(
            sha256=sha256,
            size=len(data),
            uri=self._content_uri(sha256),
            already_existed=already_existed,
        )

    def retrieve(self, sha256: str) -> Optional[RetrieveResult]:
        """Return the stored asset bytes + metadata, or None if not found."""
        manifest = self._read_manifest(sha256)
        if manifest is None:
            return None
        data_path = self._data_path(sha256, manifest["filename"])
        if not data_path.exists():
            return None
        try:
            data = data_path.read_bytes()
        except OSError:
            return None
        return RetrieveResult(
            sha256=manifest["sha256"],
            data=data,
            filename=manifest["filename"],
            kind=manifest["kind"],
            label=manifest["label"],
            size=manifest["size"],
            ingested_at=manifest["ingested_at"],
            ingested_by=manifest["ingested_by"],
        )

    def exists(self, sha256: str) -> bool:
        """Return True if an object with this digest is present in the store."""
        return self._manifest_path(sha256).exists()

    def list_assets(self) -> list[dict]:
        """Return a list of all manifest dicts in the store."""
        manifests: list[dict] = []
        for manifest_path in sorted(self._root.rglob("manifest.json")):
            try:
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifests.append(m)
            except (json.JSONDecodeError, OSError):
                pass
        return manifests

    def delete(self, sha256: str) -> bool:
        """Remove the stored asset. Returns True if deleted, False if not found."""
        obj_dir = self._object_dir(sha256)
        if not obj_dir.exists():
            return False
        shutil.rmtree(obj_dir)
        return True
