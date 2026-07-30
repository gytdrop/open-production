"""Tests for the demo-server hardening patches (path traversal, oversized body,
input-length caps, security headers)."""
from __future__ import annotations

from io import BytesIO
from public_demo.server import (
    MAX_BODY_BYTES,
    MAX_TOPIC_LEN,
    MAX_AUDIENCE_LEN,
    MAX_TONE_LEN,
    MAX_ANGLE_ID_LEN,
    _PRODUCTION_ID_RE,
    _validate_production_id,
    _normalize_payload,
    _read_json_body,
    _BodyTooLarge,
    _InvalidJsonBody,
    DemoHTTPRequestHandler,
    _CORS_ORIGIN,
)


# -------- _validate_production_id ------------------------------------------

def test_validate_production_id_accepts_legacy_format():
    assert _validate_production_id("prod_abc123") == "prod_abc123"


def test_validate_production_id_accepts_real_uuid_format():
    assert _validate_production_id("prod_deadbeefcafe") == "prod_deadbeefcafe"


def test_validate_production_id_rejects_parent_traversal():
    import pytest
    with pytest.raises(ValueError):
        _validate_production_id("..")


def test_validate_production_id_rejects_slash():
    import pytest
    with pytest.raises(ValueError):
        _validate_production_id("prod_abc/123")


def test_validate_production_id_rejects_empty():
    import pytest
    with pytest.raises(ValueError):
        _validate_production_id("")


def test_validate_production_id_rejects_oversized():
    import pytest
    with pytest.raises(ValueError):
        _validate_production_id("prod_" + ("a" * 200))


def test_validate_production_id_rejects_dot_prefix():
    import pytest
    with pytest.raises(ValueError):
        _validate_production_id(".hidden")


def test_production_id_regex_matches_documented_ids():
    """The regex must accept the IDs the system actually generates."""
    assert _PRODUCTION_ID_RE.match("prod_deadbeef1234")
    assert _PRODUCTION_ID_RE.match("evt_deadbeef1234")
    assert _PRODUCTION_ID_RE.match("branch_deadbeef1234")
    assert _PRODUCTION_ID_RE.match("snap_deadbeef1234")
    assert _PRODUCTION_ID_RE.match("studio_deadbeef1234")


# -------- _normalize_payload ------------------------------------------------

def test_normalize_payload_truncates_oversized_topic():
    huge = "x" * (MAX_TOPIC_LEN + 1000)
    out = _normalize_payload({"topic": huge, "audience": "x", "tone": "x"})
    assert len(out["topic"]) == MAX_TOPIC_LEN


def test_normalize_payload_truncates_audience_and_tone():
    out = _normalize_payload({
        "topic": "ok",
        "audience": "y" * (MAX_AUDIENCE_LEN + 50),
        "tone": "z" * (MAX_TONE_LEN + 50),
    })
    assert len(out["audience"]) == MAX_AUDIENCE_LEN
    assert len(out["tone"]) == MAX_TONE_LEN


def test_normalize_payload_falls_back_to_defaults_on_empty():
    out = _normalize_payload({})
    assert out["topic"]
    assert out["audience"]
    assert out["tone"]


def test_normalize_payload_falls_back_to_defaults_on_non_string():
    out = _normalize_payload({"topic": 12345, "audience": None, "tone": []})
    assert isinstance(out["topic"], str) and out["topic"]
    assert isinstance(out["audience"], str) and out["audience"]
    assert isinstance(out["tone"], str) and out["tone"]


# -------- _read_json_body ---------------------------------------------------

class _FakeHandler:
    def __init__(self, body: bytes, content_length: str):
        self.headers = {"Content-Length": content_length}
        self._rfile = BytesIO(body)

    @property
    def rfile(self):
        return self._rfile


def test_read_json_body_rejects_oversized_with_413_signal():
    h = _FakeHandler(b"{}" * 100, str(MAX_BODY_BYTES + 100))
    try:
        _read_json_body(h)
        assert False, "expected _BodyTooLarge"
    except _BodyTooLarge as exc:
        assert str(MAX_BODY_BYTES) in str(exc)


def test_read_json_body_accepts_max_size():
    body = b'{"topic":"x","audience":"y","tone":"z"}'
    h = _FakeHandler(body, str(len(body)))
    parsed = _read_json_body(h)
    assert parsed["topic"] == "x"


def test_read_json_body_rejects_negative_content_length():
    h = _FakeHandler(b"{}", "-1")
    try:
        _read_json_body(h)
        assert False, "expected _InvalidJsonBody"
    except _InvalidJsonBody:
        pass


def test_read_json_body_rejects_non_object():
    h = _FakeHandler(b"[1,2,3]", "7")
    try:
        _read_json_body(h)
        assert False, "expected _InvalidJsonBody"
    except _InvalidJsonBody:
        pass


# -------- route integration -------------------------------------------------

def test_route_rejects_path_traversal_in_status():
    """A path-traversal production_id must be rejected with HTTP 400."""

    class _FakeServer:
        server_name = "localhost"
        server_port = 8000

    class FakeHandler(DemoHTTPRequestHandler):
        def __init__(self, path: str):
            self.path = path
            self.server = _FakeServer()
            self.headers = {}
            self._responses: list[int] = []
            self._headers_sent: list[tuple[str, str]] = []
            self._body = b""

        def send_response(self, code, message=None):
            self._responses.append(code)

        def send_header(self, key, value):
            self._headers_sent.append((key, value))

        def end_headers(self):
            pass

        @property
        def wfile(self):
            class _W:
                def __init__(self, outer):
                    self.outer = outer

                def write(self, data: bytes) -> None:
                    self.outer._body = data
            return _W(self)

    h = FakeHandler("/api/production/..%2Fetc/status")
    h.do_GET()
    assert h._responses[0] == 400
    body = h._body.decode()
    assert "invalid_production_id" in body


def test_security_headers_present_on_json_response():
    """_json_response sets X-Content-Type-Options: nosniff and Cache-Control: no-store."""

    class _FakeServer:
        server_name = "localhost"
        server_port = 8000

    class FakeHandler(DemoHTTPRequestHandler):
        def __init__(self):
            self.path = "/healthz"
            self.server = _FakeServer()
            self.headers = {}
            self._headers_sent: list[tuple[str, str]] = []
            self._body = b""

        def send_response(self, code, message=None):
            pass

        def send_header(self, key, value):
            self._headers_sent.append((key, value))

        def end_headers(self):
            pass

        @property
        def wfile(self):
            class _W:
                def __init__(self, outer):
                    self.outer = outer

                def write(self, data: bytes) -> None:
                    self.outer._body = data
            return _W(self)

    h = FakeHandler()
    from public_demo.server import _json_response
    _json_response(h, {"ok": True})
    header_map = dict(h._headers_sent)
    assert header_map.get("X-Content-Type-Options") == "nosniff"
    assert header_map.get("Cache-Control") == "no-store"
    assert header_map.get("Access-Control-Allow-Origin") == _CORS_ORIGIN
