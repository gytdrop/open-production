"""Tests for AssetLibraryService — §13 content-addressed binary storage."""
from __future__ import annotations

import hashlib

import pytest

from service.asset_library_service import AssetLibraryService, IngestResult, RetrieveResult


@pytest.fixture
def store(tmp_path):
    return AssetLibraryService(root=tmp_path / "asset_store")


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

def test_ingest_returns_ingest_result(store):
    """ingest() must return an IngestResult with sha256, uri, size."""
    data = b"hello world"
    result = store.ingest(data, "hello.txt", kind="text", label="Hello")
    assert isinstance(result, IngestResult)
    assert result.sha256 == hashlib.sha256(data).hexdigest()
    assert result.uri == f"asset://{result.sha256}"
    assert result.size == len(data)


def test_ingest_content_addressed_uri(store):
    """URI must be 'asset://<sha256>'."""
    data = b"some image bytes"
    result = store.ingest(data, "img.jpg", kind="image", label="Test image")
    assert result.uri.startswith("asset://")
    assert result.uri.endswith(result.sha256)


def test_ingest_deduplication(store):
    """Ingesting the same bytes twice sets already_existed=True on second call."""
    data = b"duplicate content"
    first = store.ingest(data, "dup.bin", kind="image", label="First")
    assert first.already_existed is False
    second = store.ingest(data, "dup.bin", kind="image", label="Second")
    assert second.already_existed is True
    assert first.sha256 == second.sha256


def test_ingest_creates_manifest_on_disk(store):
    """After ingest, a manifest.json file must exist at the expected path."""
    data = b"manifest test"
    result = store.ingest(data, "manifest_test.bin", kind="video", label="Video")
    sha = result.sha256
    manifest_path = store._root / sha[:2] / sha[2:] / "manifest.json"
    assert manifest_path.exists()


def test_ingest_creates_data_file_on_disk(store):
    """After ingest, the raw data file must exist at the expected path."""
    data = b"raw data file"
    result = store.ingest(data, "data.bin", kind="audio", label="Audio")
    sha = result.sha256
    data_path = store._root / sha[:2] / sha[2:] / "data.bin"
    assert data_path.exists()
    assert data_path.read_bytes() == data


def test_ingest_manifest_fields(store):
    """Manifest must contain sha256, size, kind, label, filename, ingested_at, ingested_by."""
    data = b"manifest fields check"
    store.ingest(data, "fields.txt", kind="text", label="Fields check", ingested_by="test_actor")
    sha = hashlib.sha256(data).hexdigest()
    import json
    manifest = json.loads((store._root / sha[:2] / sha[2:] / "manifest.json").read_text())
    assert manifest["sha256"] == sha
    assert manifest["size"] == len(data)
    assert manifest["kind"] == "text"
    assert manifest["label"] == "Fields check"
    assert manifest["filename"] == "fields.txt"
    assert manifest["ingested_by"] == "test_actor"
    assert "ingested_at" in manifest


def test_ingest_different_content_stored_separately(store):
    """Different byte sequences must produce distinct content addresses."""
    r1 = store.ingest(b"content A", "a.bin", kind="image", label="A")
    r2 = store.ingest(b"content B", "b.bin", kind="image", label="B")
    assert r1.sha256 != r2.sha256
    assert len(store.list_assets()) == 2


# ---------------------------------------------------------------------------
# retrieve
# ---------------------------------------------------------------------------

def test_retrieve_after_ingest(store):
    """retrieve() returns a RetrieveResult with matching bytes and metadata."""
    data = b"retrieve me"
    result = store.ingest(data, "retrieve.bin", kind="image", label="Retrieve test",
                          ingested_by="user1")
    fetched = store.retrieve(result.sha256)
    assert isinstance(fetched, RetrieveResult)
    assert fetched.data == data
    assert fetched.sha256 == result.sha256
    assert fetched.filename == "retrieve.bin"
    assert fetched.kind == "image"
    assert fetched.label == "Retrieve test"
    assert fetched.ingested_by == "user1"
    assert fetched.size == len(data)


def test_retrieve_missing_returns_none(store):
    """retrieve() returns None for an unknown sha256."""
    result = store.retrieve("a" * 64)
    assert result is None


def test_retrieve_truncated_sha_returns_none(store):
    """retrieve() returns None for a partial sha256 that doesn't match any stored object."""
    result = store.retrieve("ab")
    assert result is None


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------

def test_exists_true_after_ingest(store):
    """exists() returns True immediately after ingest."""
    data = b"existence check"
    result = store.ingest(data, "exist.bin", kind="text", label="Exist")
    assert store.exists(result.sha256) is True


def test_exists_false_for_unknown(store):
    """exists() returns False for a sha256 that was never ingested."""
    assert store.exists("0" * 64) is False


# ---------------------------------------------------------------------------
# list_assets
# ---------------------------------------------------------------------------

def test_list_assets_empty_store(store):
    """list_assets() returns an empty list for a fresh store."""
    assert store.list_assets() == []


def test_list_assets_returns_all_manifests(store):
    """list_assets() returns one manifest dict per ingested object."""
    store.ingest(b"alpha", "a.bin", kind="image", label="A")
    store.ingest(b"beta", "b.bin", kind="video", label="B")
    assets = store.list_assets()
    assert len(assets) == 2
    shas = {a["sha256"] for a in assets}
    assert shas == {
        hashlib.sha256(b"alpha").hexdigest(),
        hashlib.sha256(b"beta").hexdigest(),
    }


def test_list_assets_deduplication_does_not_inflate_count(store):
    """Ingesting the same bytes twice must not add a second manifest entry."""
    store.ingest(b"same", "same.bin", kind="image", label="Same")
    store.ingest(b"same", "same.bin", kind="image", label="Same again")
    assert len(store.list_assets()) == 1


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_removes_asset(store):
    """delete() removes the object directory and returns True."""
    data = b"delete me"
    result = store.ingest(data, "del.bin", kind="image", label="Delete me")
    assert store.exists(result.sha256)
    deleted = store.delete(result.sha256)
    assert deleted is True
    assert not store.exists(result.sha256)
    assert store.retrieve(result.sha256) is None


def test_delete_missing_returns_false(store):
    """delete() returns False for a sha256 not in the store."""
    assert store.delete("f" * 64) is False


def test_delete_removes_from_list(store):
    """list_assets() no longer includes a deleted asset."""
    result = store.ingest(b"to delete", "td.bin", kind="image", label="To delete")
    store.delete(result.sha256)
    assert store.list_assets() == []


# ---------------------------------------------------------------------------
# AssetLibraryAgent integration
# ---------------------------------------------------------------------------

def test_asset_library_agent_ingest_via_service(tmp_path):
    """AssetLibraryAgent.run({'operation': 'ingest', ...}) stores bytes via service."""
    from agents.asset_library import AssetLibraryAgent
    svc = AssetLibraryService(root=tmp_path / "store")
    agent = AssetLibraryAgent(service=svc)
    data = b"agent ingest test"
    out = agent.run({
        "operation": "ingest",
        "data": data,
        "filename": "agent_test.bin",
        "kind": "image",
        "label": "Agent ingest test",
        "ingested_by": "agent_tester",
    })
    assert "sha256" in out
    assert out["uri"].startswith("asset://")
    assert out["size"] == len(data)
    assert out["already_existed"] is False
    assert svc.exists(out["sha256"])


def test_asset_library_agent_ingest_deduplication(tmp_path):
    """Second ingest of same bytes sets already_existed=True."""
    from agents.asset_library import AssetLibraryAgent
    svc = AssetLibraryService(root=tmp_path / "store")
    agent = AssetLibraryAgent(service=svc)
    data = b"dup agent bytes"
    agent.run({"operation": "ingest", "data": data, "filename": "d.bin",
               "kind": "image", "label": "D"})
    out = agent.run({"operation": "ingest", "data": data, "filename": "d.bin",
                     "kind": "image", "label": "D"})
    assert out["already_existed"] is True


def test_asset_library_agent_retrieve_found(tmp_path):
    """retrieve operation returns found=True with metadata after ingest."""
    from agents.asset_library import AssetLibraryAgent
    svc = AssetLibraryService(root=tmp_path / "store")
    agent = AssetLibraryAgent(service=svc)
    data = b"retrievable"
    ingest_out = agent.run({
        "operation": "ingest",
        "data": data,
        "filename": "ret.bin",
        "kind": "text",
        "label": "Retrievable",
    })
    retrieve_out = agent.run({
        "operation": "retrieve",
        "sha256": ingest_out["sha256"],
    })
    assert retrieve_out["found"] is True
    assert retrieve_out["sha256"] == ingest_out["sha256"]
    assert retrieve_out["filename"] == "ret.bin"
    assert retrieve_out["kind"] == "text"


def test_asset_library_agent_retrieve_not_found(tmp_path):
    """retrieve returns found=False for unknown sha256."""
    from agents.asset_library import AssetLibraryAgent
    svc = AssetLibraryService(root=tmp_path / "store")
    agent = AssetLibraryAgent(service=svc)
    out = agent.run({"operation": "retrieve", "sha256": "a" * 64})
    assert out["found"] is False


def test_asset_library_agent_ingest_without_service():
    """ingest without a configured service returns an error key (no raise)."""
    from agents.asset_library import AssetLibraryAgent
    agent = AssetLibraryAgent()  # no service
    out = agent.run({"operation": "ingest", "data": b"x", "filename": "x.bin",
                     "kind": "image", "label": "X"})
    assert "error" in out


def test_asset_library_agent_retrieve_without_service():
    """retrieve without a configured service returns found=False (no raise)."""
    from agents.asset_library import AssetLibraryAgent
    agent = AssetLibraryAgent()
    out = agent.run({"operation": "retrieve", "sha256": "a" * 64})
    assert out["found"] is False
